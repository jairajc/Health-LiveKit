"""Custom exceptions for the insurance agent."""


class StediAPIError(Exception):
    """Exception raised for STEDI API failures."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ValidationError(Exception):
    """Exception raised for invalid data."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)
