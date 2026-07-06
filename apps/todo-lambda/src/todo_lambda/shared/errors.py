class DomainError(Exception):
    status_code: int


class ValidationError(DomainError):
    status_code = 422
