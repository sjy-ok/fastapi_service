class AppError(Exception):
    status_code = 500

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class BadRequestError(AppError):
    status_code = 400


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class IntegrationError(AppError):
    status_code = 502
