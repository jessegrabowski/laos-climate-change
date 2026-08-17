import numpy as np
import pytensor
import pytensor.tensor as pt
import pytest

from climate_risk.exceptions import DataValidationError
from climate_risk.models.aggregation import build_aggregation

# A unit square split into a left and a right half, so both units have a known analytic integral.
SPLIT = 0.5


def square_grid(cells_per_axis: int):
    """Cell centroids and areas for a regular grid over the unit square, split into two units."""
    edges = np.linspace(0.0, 1.0, cells_per_axis + 1)
    centres = (edges[:-1] + edges[1:]) / 2.0
    x, y = (axis.ravel() for axis in np.meshgrid(centres, centres, indexing="ij"))

    area = (1.0 / cells_per_axis) ** 2
    unit_of_cell = ["left" if position < SPLIT else "right" for position in x]

    return x, y, np.full(x.shape, area), unit_of_cell


def integrate_plane(a: float, b: float, c: float, x0: float, x1: float, y0: float, y1: float) -> float:
    """The exact integral of ``a + b*x + c*y`` over a rectangle."""
    return a * (x1 - x0) * (y1 - y0) + b * (x1**2 - x0**2) / 2.0 * (y1 - y0) + c * (y1**2 - y0**2) / 2.0 * (x1 - x0)


def test_a_plane_integrates_exactly():
    """The midpoint rule is exact for a linear field, so this pins the operator against a closed
    form rather than against a tolerance. An error in the weights or the row order shows up here.
    """
    a, b, c = 2.0, 3.0, -1.5
    x, y, areas, unit_of_cell = square_grid(cells_per_axis=8)

    aggregation = build_aggregation(unit_of_cell=unit_of_cell, weights=areas)
    totals = aggregation.aggregate(a + b * x + c * y)

    assert aggregation.units == ("left", "right")
    assert totals == pytest.approx(
        [
            integrate_plane(a, b, c, 0.0, SPLIT, 0.0, 1.0),
            integrate_plane(a, b, c, SPLIT, 1.0, 0.0, 1.0),
        ]
    )


def test_refining_the_grid_converges_on_a_curved_field():
    """A sinusoid is not integrated exactly by the midpoint rule, so the claim is convergence.
    A fixed tolerance would pass on an operator that is wrong by a constant factor.
    """
    # Integral of sin(pi x) sin(pi y) over the unit square, which separates into (2 / pi) squared.
    exact = 4.0 / np.pi**2

    errors = []
    for cells_per_axis in (8, 32):
        x, y, areas, unit_of_cell = square_grid(cells_per_axis)
        aggregation = build_aggregation(unit_of_cell=unit_of_cell, weights=areas)
        totals = aggregation.aggregate(np.sin(np.pi * x) * np.sin(np.pi * y))
        errors.append(abs(totals.sum() - exact))

    assert errors[1] < errors[0] / 10.0, errors


def test_weights_place_each_cell_in_exactly_one_unit():
    """Every cell's weight appears once in the operator, so the column sums are the weights back.
    A cell double-counted into two units inflates one polygon's total and is invisible in a
    row-wise check.
    """
    _, _, areas, unit_of_cell = square_grid(cells_per_axis=6)

    aggregation = build_aggregation(unit_of_cell=unit_of_cell, weights=areas)

    assert np.asarray(aggregation.matrix.sum(axis=0)) == pytest.approx(areas)


def test_a_cell_outside_every_unit_contributes_to_nothing():
    """The gridded extent is a bounding box, so cells over the sea or a neighbouring country are
    normal. They must drop out rather than join whichever unit is nearest.
    """
    aggregation = build_aggregation(
        unit_of_cell=["left", None, "right"],
        weights=np.array([1.0, 99.0, 1.0]),
    )

    totals = aggregation.aggregate(np.array([1.0, 1.0, 1.0]))

    assert totals == pytest.approx([1.0, 1.0])
    assert aggregation.matrix.sum() == pytest.approx(2.0)


def test_draws_aggregate_columnwise():
    """Posterior draws come through as (n_cells, n_draws), and each column is its own field."""
    aggregation = build_aggregation(unit_of_cell=["a", "a", "b"], weights=np.ones(3))

    totals = aggregation.aggregate(np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]]))

    np.testing.assert_allclose(totals, [[3.0, 30.0], [3.0, 30.0]])


def test_the_symbolic_path_integrates_the_plane_exactly():
    """The graph is a scatter-add over index arrays while the array path is a sparse matrix
    product, so they are two implementations of one operator. Pinning the graph against the same
    closed form as :func:`test_a_plane_integrates_exactly` checks it on its own terms rather than
    checking that the two agree, which they would if a shared index array were wrong.
    """
    a, b, c = 2.0, 3.0, -1.5
    x, y, areas, unit_of_cell = square_grid(cells_per_axis=8)

    aggregation = build_aggregation(unit_of_cell=unit_of_cell, weights=areas)
    cells = pt.vector("cells")
    totals = pytensor.function([cells], aggregation.aggregate_symbolic(cells))(a + b * x + c * y)

    assert totals == pytest.approx(
        [
            integrate_plane(a, b, c, 0.0, SPLIT, 0.0, 1.0),
            integrate_plane(a, b, c, SPLIT, 1.0, 0.0, 1.0),
        ]
    )


def test_the_symbolic_path_handles_repeats_gaps_and_empty_units():
    """The scatter-add has to accumulate over cells sharing a unit, skip cells assigned to none,
    and leave an empty unit's row at zero. A plain assignment rather than an increment would keep
    only the last cell of each unit and pass a test where every unit holds one cell.
    """
    aggregation = build_aggregation(
        unit_of_cell=["b", "a", None, "b", "a"],
        weights=np.array([1.5, 2.0, 99.0, 0.5, 3.0]),
        units=["a", "empty", "b"],
    )
    field = np.array([1.0, 2.0, 7.0, 3.0, 4.0])

    cells = pt.vector("cells")
    totals = pytensor.function([cells], aggregation.aggregate_symbolic(cells))(field)

    assert totals == pytest.approx([16.0, 0.0, 3.0])


def test_the_symbolic_gradient_is_the_operator_transpose():
    """The model differentiates through this, and a gather paired with the wrong scatter can give
    the right totals with the wrong sensitivities. The operator is linear, so its Jacobian is the
    matrix itself and the reverse pass is exactly its transpose.
    """
    _, _, areas, unit_of_cell = square_grid(cells_per_axis=4)
    aggregation = build_aggregation(unit_of_cell=unit_of_cell, weights=areas)

    cotangent = np.array([2.0, -3.0])
    cells = pt.vector("cells")
    seeded = pt.sum(aggregation.aggregate_symbolic(cells) * pt.as_tensor_variable(cotangent))
    pullback = pytensor.function([cells], pt.grad(seeded, cells))

    np.testing.assert_allclose(pullback(np.zeros_like(areas)), aggregation.matrix.T @ cotangent)


def test_the_default_row_order_is_sorted():
    """Sorted, not first-appearance: a caller joining totals back to a sorted unit table would get
    silently transposed rows if the default followed the order the cells happened to arrive in.
    """
    aggregation = build_aggregation(unit_of_cell=["b", "a"], weights=np.array([1.0, 2.0]))

    assert aggregation.units == ("a", "b")
    assert aggregation.aggregate(np.array([10.0, 20.0])) == pytest.approx([40.0, 10.0])


def test_the_row_order_can_be_given():
    """The model reads totals by position, so the caller has to be able to fix the order rather
    than depend on the sort of whatever labels happened to appear.
    """
    aggregation = build_aggregation(
        unit_of_cell=["b", "a"],
        weights=np.ones(2),
        units=["b", "a"],
    )

    assert aggregation.units == ("b", "a")
    assert aggregation.aggregate(np.array([1.0, 2.0])) == pytest.approx([1.0, 2.0])


def test_a_unit_with_no_cells_keeps_its_row():
    """A polygon smaller than a cell is real, and its row is all zeros. Dropping the row instead
    would shift every later unit up one and misalign the observations.
    """
    aggregation = build_aggregation(
        unit_of_cell=["a", "a"],
        weights=np.ones(2),
        units=["a", "empty", "b"],
    )

    totals = aggregation.aggregate(np.array([1.0, 1.0]))

    assert aggregation.units == ("a", "empty", "b")
    assert totals == pytest.approx([2.0, 0.0, 0.0])


def test_a_unit_absent_from_the_row_order_is_named():
    """Silently dropping the cells of an unlisted unit would lose part of the field with no sign."""
    with pytest.raises(DataValidationError, match="ghost"):
        build_aggregation(unit_of_cell=["a", "ghost"], weights=np.ones(2), units=["a"])


def test_mismatched_assignments_and_weights_are_rejected():
    with pytest.raises(DataValidationError, match="same cells"):
        build_aggregation(unit_of_cell=["a", "b"], weights=np.ones(3))


@pytest.mark.parametrize("bad", [np.nan, np.inf])
def test_a_non_finite_weight_is_rejected(bad):
    """One NaN weight silently turns a polygon's total into NaN and the fit into a wall of errors
    a long way from the cause.
    """
    with pytest.raises(DataValidationError, match="non-finite"):
        build_aggregation(unit_of_cell=["a", "b"], weights=np.array([1.0, bad]))


def test_a_negative_weight_is_rejected():
    with pytest.raises(DataValidationError, match="negative"):
        build_aggregation(unit_of_cell=["a", "b"], weights=np.array([1.0, -1.0]))


def test_a_field_of_the_wrong_length_is_rejected():
    """The operator is built once and applied many times, so a mismatch here means the cell table
    changed underneath it."""
    aggregation = build_aggregation(unit_of_cell=["a", "b"], weights=np.ones(2))

    with pytest.raises(DataValidationError, match="built for 2"):
        aggregation.aggregate(np.ones(3))
