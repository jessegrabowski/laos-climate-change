class DataValidationError(Exception):
    """Raised when upstream data does not match what the pipeline expects of it."""


class ISOCodeValidationError(DataValidationError):
    """Raised when ISO codes are not one-to-one with the geometries they label."""
