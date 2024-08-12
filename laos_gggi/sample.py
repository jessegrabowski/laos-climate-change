import os
import pathlib

import arviz as az
import pymc as pm


def sample_or_load(
    fp: str,
    *,
    model: pm.Model = None,
    resample: bool = False,
    sample_kwargs: dict | None = None,
) -> az.InferenceData:
    """
    Sample the model or load the model from disk.

    Args:
        fp (str): The file path to save/load the inference data.
        model (pm.Model, optional): The PyMC model to sample. Defaults to None.
        resample (bool, optional): Whether to resample the model. Defaults to False.
        sample_kwargs (dict, optional): Additional keyword arguments to pass to the sampling function. Defaults to None.

    Returns
    -------
        az.InferenceData: The sampled inference data.

    This function performs posterior and posterior predictive sampling of a PyMC model. It either loads the model from disk or samples it using the provided model and sample_kwargs. If the file already exists and resampling is not requested, it loads the data from disk. Otherwise, it samples the model, performs posterior predictive sampling, and saves the resulting inference data to disk.
    """
    _fp = pathlib.Path(fp)
    model = pm.modelcontext(model)

    # Create directory structure if necessary
    os.makedirs(_fp.parent, exist_ok=True)
    if _fp.exists() and not resample:
        idata = az.from_netcdf(_fp)
        idata.load()  # Force load to avoid mismatch if the memory is overwritten before idata is used
    else:
        if sample_kwargs is None:
            sample_kwargs = {}
        with model:
            idata = pm.sample(**sample_kwargs)
            idata = pm.sample_posterior_predictive(idata, extend_inferencedata=True)
            idata = pm.compute_log_likelihood(idata, extend_inferencedata=True)
            if _fp.exists():
                os.remove(_fp)
            az.to_netcdf(idata, _fp)
    return idata
