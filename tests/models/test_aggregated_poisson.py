import numpy as np
import pytensor
import pytensor.tensor as pt
import pytest

from climate_risk.models.aggregated_poisson import (
    expected_intensity,
    sample_log_intensity,
)
from climate_risk.models.aggregation import build_aggregation

N_CELLS, N_INDUCING = 12, 4


def latent_pieces(seed: int):
    """A mean, an independent variance, and a covariance factor, standing in for an SVGP fit."""
    rng = np.random.default_rng(seed)
    mean = rng.normal(0.0, 0.4, size=N_CELLS)
    independent_variance = rng.uniform(0.05, 0.3, size=N_CELLS)
    factor = rng.normal(0.0, 0.3, size=(N_CELLS, N_INDUCING))

    return mean, independent_variance, factor


def brute_force_intensities(mean, independent_variance, factor, weights, unit_of_cell, units, n_draws, seed):
    """Draw the field from the covariance the factors describe and aggregate it with numpy."""
    rng = np.random.default_rng(seed)
    covariance = np.diag(independent_variance) + factor @ factor.T
    chol = np.linalg.cholesky(covariance + 1e-10 * np.eye(len(mean)))
    field = mean[:, None] + chol @ rng.standard_normal((len(mean), n_draws))

    rows = np.array([units.index(unit) for unit in unit_of_cell])
    contributions = weights[:, None] * np.exp(field)

    return np.stack([contributions[rows == row].sum(axis=0) for row in range(len(units))])


def test_the_expected_intensity_matches_sampling_the_field():
    """E[Lambda] is exact and needs only the marginals, so it must agree with sampling the full
    factored covariance. Aggregating before exponentiating, or dropping the variance correction,
    both show up as a bias here.
    """
    mean, independent_variance, factor = latent_pieces(seed=0)
    weights = np.linspace(0.5, 1.5, N_CELLS)
    unit_of_cell = ["a"] * 5 + ["b"] * 7
    aggregation = build_aggregation(unit_of_cell=unit_of_cell, weights=weights)

    closed_form = pytensor.function(
        [], expected_intensity(aggregation, pt.as_tensor_variable(mean), independent_variance, factor)
    )()
    drawn = brute_force_intensities(
        mean, independent_variance, factor, weights, unit_of_cell, ["a", "b"], n_draws=400_000, seed=1
    )

    np.testing.assert_allclose(closed_form, drawn.mean(axis=1), rtol=0.02)


def test_the_sampled_log_intensity_converges_on_the_truth():
    """The log term is the one with no closed form. Its estimator has to be centred on the real
    expectation, and the Jensen gap is the thing it exists to capture: log E[Lambda] is an upper
    bound that a correct estimator must sit strictly below.
    """
    mean, independent_variance, factor = latent_pieces(seed=2)
    weights = np.linspace(0.5, 1.5, N_CELLS)
    unit_of_cell = ["a"] * 5 + ["b"] * 7
    aggregation = build_aggregation(unit_of_cell=unit_of_cell, weights=weights)

    rng = np.random.default_rng(3)
    n_draws = 40_000
    inducing_draws, cell_draws = pt.matrix("inducing_draws"), pt.matrix("cell_draws")
    sampled = pytensor.function(
        [inducing_draws, cell_draws],
        sample_log_intensity(
            aggregation, pt.as_tensor_variable(mean), independent_variance, factor, inducing_draws, cell_draws
        ),
    )(rng.standard_normal((N_INDUCING, n_draws)), rng.standard_normal((N_CELLS, n_draws))).mean(axis=1)

    drawn = brute_force_intensities(
        mean, independent_variance, factor, weights, unit_of_cell, ["a", "b"], n_draws=400_000, seed=4
    )
    truth = np.log(drawn).mean(axis=1)
    jensen = np.log(drawn.mean(axis=1))

    np.testing.assert_allclose(sampled, truth, rtol=0.01)
    assert (sampled < jensen).all(), "the estimator must sit below the Jensen bound it corrects"


def test_the_draws_reproduce_the_within_unit_correlation():
    """A unit's cells are correlated through the shared inducing values, and that correlation is
    what the log term is sensitive to. Sampling each cell independently would leave the mean
    intact and the spread of Lambda far too small.
    """
    mean, independent_variance, factor = latent_pieces(seed=5)
    aggregation = build_aggregation(unit_of_cell=["a"] * N_CELLS, weights=np.ones(N_CELLS))

    rng = np.random.default_rng(6)
    n_draws = 20_000
    values = (rng.standard_normal((N_INDUCING, n_draws)), rng.standard_normal((N_CELLS, n_draws)))
    inducing_draws, cell_draws = pt.matrix("inducing_draws"), pt.matrix("cell_draws")

    def spread(factor_used):
        log_intensity = pytensor.function(
            [inducing_draws, cell_draws],
            sample_log_intensity(
                aggregation,
                pt.as_tensor_variable(mean),
                independent_variance,
                factor_used,
                inducing_draws,
                cell_draws,
            ),
        )(*values)
        return log_intensity.std()

    assert spread(factor) > 1.5 * spread(np.zeros_like(factor))


def test_an_unwhitened_svgp_is_refused():
    """The moment expressions are derived from the whitened conditional. Running them against the
    unwhitened parameterization would silently use the wrong covariance factor.
    """
    from climate_risk.exceptions import DataValidationError
    from climate_risk.models.aggregated_poisson import latent_moments

    class Unwhitened:
        whiten = False

    with pytest.raises(DataValidationError, match="whitened"):
        latent_moments(Unwhitened(), pt.matrix("X"))
