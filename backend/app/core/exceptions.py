class AppError(Exception):
    """Expected failure. message is PUBLIC: never put keys, raw exceptions or data here.

    Raise with ``raise ExternalSourceError("safe guidance") from exc`` to keep the
    cause type and frame available in request-ID diagnostics without leaking values.
    """
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ExternalSourceError(AppError):
    """외부 API 호출 실패 → 503."""
    def __init__(self, message: str):
        super().__init__(message, status_code=503)


class ValidationFailure(AppError):
    """입력값 검증 실패 → 422."""
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class AuthError(AppError):
    """인증 실패 → 401."""
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)


class ConfigurationError(AppError):
    """필수 설정 누락 → 500."""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)
