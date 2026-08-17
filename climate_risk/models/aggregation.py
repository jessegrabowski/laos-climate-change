from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pytensor.tensor as pt

from pytensor.tensor import TensorVariable
from scipy import sparse

from climate_risk.exceptions import DataValidationError


@dataclass(frozen=True, slots=True)
class Aggregation:
    r"""
    The linear operator taking a cell-level field to the polygon totals it is observed through.

    .. math::

        y_A = \sum_{i \in A} w_i \lambda_i

    ``units`` fixes the row order, which the model reads by position: it must agree with the order
    the observations arrive in.

    Parameters
    ----------
    units : tuple of str
        Unit labels, in row order.
    rows : ndarray
        Unit index of each contributing cell, one entry per nonzero.
    columns : ndarray
        Cell index of each contributing cell, one entry per nonzero.
    weights : ndarray
        Weight of each contributing cell, one entry per nonzero.
    n_cells : int
        Width of the operator, counting cells that contribute to no unit.
    """

    # The triplet is primary because a scipy matrix cannot multiply a pytensor variable.
    units: tuple[str, ...]
    rows: np.ndarray
    columns: np.ndarray
    weights: np.ndarray
    n_cells: int

    @property
    def n_units(self) -> int:
        """Rows of the operator, and the length of an aggregated vector."""
        return len(self.units)

    @property
    def matrix(self) -> sparse.csr_array:
        """The operator as a sparse matrix, shape ``(n_units, n_cells)``."""
        return sparse.csr_array(
            (self.weights, (self.rows, self.columns)),
            shape=(self.n_units, self.n_cells),
        )

    def aggregate(self, cell_values: np.ndarray) -> np.ndarray:
        """
        Sum a cell-level field to unit totals, outside a graph.

        Use this on drawn or observed arrays. Inside a model, use :meth:`aggregate_symbolic`.

        Parameters
        ----------
        cell_values : ndarray
            Shape ``(n_cells,)`` for one field, or ``(n_cells, k)`` to aggregate ``k`` of them at
            once, which is how posterior draws are carried through.

        Returns
        -------
        ndarray
            Shape ``(n_units,)`` or ``(n_units, k)``, in the row order of ``units``.
        """
        self._check_width(cell_values.shape[0])

        return np.asarray(self.matrix @ cell_values)

    def aggregate_symbolic(self, cell_values: TensorVariable) -> TensorVariable:
        """
        Sum a cell-level field to unit totals, as a graph.

        Cells sharing a unit accumulate, and the reverse pass is the operator's transpose.

        Parameters
        ----------
        cell_values : TensorVariable
            Shape ``(n_cells,)`` for one field, or ``(n_cells, k)`` to aggregate ``k`` of them at
            once, each column independently.

        Returns
        -------
        TensorVariable
            Shape ``(n_units,)`` or ``(n_units, k)``, in the row order of ``units``.
        """
        weights = pt.as_tensor_variable(self.weights)
        if cell_values.ndim == 2:
            weights = weights[:, None]
            base = pt.zeros((self.n_units, cell_values.shape[1]))
        else:
            base = pt.zeros((self.n_units,))

        contributions = weights * cell_values[self.columns]

        totals: TensorVariable = pt.inc_subtensor(base[self.rows], contributions)

        return totals

    def _check_width(self, width: int) -> None:
        if width != self.n_cells:
            raise DataValidationError(f"The field has {width} cells but the operator was built for {self.n_cells}.")


def build_aggregation(
    *,
    unit_of_cell: Sequence[str | None],
    weights: np.ndarray,
    units: Sequence[str] | None = None,
) -> Aggregation:
    """
    Build the cell-to-unit aggregation operator.

    Parameters
    ----------
    unit_of_cell : sequence of str or None
        The unit each cell belongs to. ``None`` marks a cell inside the gridded extent but outside
        every unit, which is dropped: it contributes to no total.
    weights : ndarray
        Each cell's weight in its unit, one per entry of ``unit_of_cell``. Cell area gives an
        integral over the polygon; population gives an exposure-weighted one.
    units : sequence of str, optional
        Row order of the operator. Every assigned label must appear, and no label twice. Default
        None, which orders the labels that appear in ``unit_of_cell``, sorted.

    Returns
    -------
    Aggregation
        The operator and its row labels.
    """
    weights = np.asarray(weights, dtype=float)
    if len(unit_of_cell) != weights.shape[0]:
        raise DataValidationError(
            f"{len(unit_of_cell)} cell assignments against {weights.shape[0]} weights; they index the same cells."
        )

    if not np.all(np.isfinite(weights)):
        raise DataValidationError("Cell weights carry a non-finite value, which would poison every total it enters.")

    if np.any(weights < 0.0):
        raise DataValidationError("Cell weights are negative, so a polygon's total would not be a sum of parts.")

    assigned = np.array([label is not None for label in unit_of_cell], dtype=bool)
    labels = [label for label in unit_of_cell if label is not None]

    non_strings = sorted({type(label).__name__ for label in labels if not isinstance(label, str)})
    if non_strings:
        raise DataValidationError(
            f"Cell assignments carry non-string labels ({', '.join(non_strings)}). A spatial join marks a cell it "
            f"matched to nothing with NaN; mark it with None instead, which is what drops it."
        )

    if units is None:
        units = sorted(set(labels))

    counts = Counter(units)
    repeated = sorted(unit for unit, count in counts.items() if count > 1)
    if repeated:
        raise DataValidationError(f"The row order repeats units, so their rows would not be reachable: {repeated}.")

    row_of_unit = {unit: row for row, unit in enumerate(units)}
    unknown = sorted(set(labels) - row_of_unit.keys())
    if unknown:
        raise DataValidationError(f"Cells are assigned to units absent from the row order: {unknown}.")

    return Aggregation(
        units=tuple(units),
        rows=np.array([row_of_unit[label] for label in labels], dtype=int),
        columns=np.flatnonzero(assigned),
        weights=weights[assigned],
        n_cells=weights.shape[0],
    )
