class DataValidationError(Exception):
    """Raised when upstream data does not match what the pipeline expects of it."""


class ISOCodeValidationError(DataValidationError):
    """Raised when ISO codes are not one-to-one with the geometries they label."""


class UpstreamUnavailableError(Exception):
    """Raised when a source could not be reached, as distinct from having no answer to give."""
