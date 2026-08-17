from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
import pytensor.tensor as pt

from scipy import sparse

from climate_risk.exceptions import DataValidationError


@dataclass(frozen=True, slots=True)
class Aggregation:
    """
    The linear operator taking a cell-level field to the polygon totals it is observed through.

    A polygon's total is :math:`\\sum_{i \\in A} w_i \\lambda_i`, so aggregation is a sparse matrix
    product. It is stored as its coordinate triplet rather than as a matrix because the symbolic
    path is a scatter-add over those indices: a scipy matrix cannot multiply a pytensor variable,
    and expressing the sum with :func:`pytensor.tensor.inc_subtensor` avoids depending on how well
    any given compilation backend covers sparse ops.

    Holding the operator and its row labels together is the point of the class: the model reads
    totals by position, and a row order that silently disagrees with the observation order
    attributes every polygon's events to the wrong place.

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

    def aggregate_symbolic(self, cell_values: pt.TensorVariable) -> pt.TensorVariable:
        """
        Sum a cell-level field to unit totals, as a graph.

        The scatter-add accumulates over repeated row indices, so a unit collects every cell
        assigned to it, and the gradient with respect to ``cell_values`` is the cell's weight.

        Parameters
        ----------
        cell_values : TensorVariable
            Shape ``(n_cells,)``.

        Returns
        -------
        TensorVariable
            Shape ``(n_units,)``, in the row order of ``units``.
        """
        contributions = pt.as_tensor_variable(self.weights) * cell_values[self.columns]

        totals: pt.TensorVariable = pt.inc_subtensor(pt.zeros((self.n_units,))[self.rows], contributions)

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
        Row order of the operator. Every assigned label must appear. Default None, which orders the
        labels that appear in ``unit_of_cell``, sorted.

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

    if units is None:
        units = sorted(set(labels))

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
