
class AppException(Exception):
    status_code: int = 500
    detail: str = "服务异常"

    def __init__(self, status_code: int = None, detail: str = None):
        self.status_code = status_code or self.__class__.status_code
        self.detail = detail or self.__class__.detail
        super().__init__(self.detail)

class NotFoundException(AppException):
    """资源不存在 (404)"""
    status_code = 404

    def __init__(self, resource: str):
        super().__init__(detail=f"{resource}不存在")

class VaildationException(AppException):
    """参数校验失败 (400)"""
    status_code = 400

    def __init__(self, message: str):
        super().__init__(detail=message)

class UnauthorizedException(AppException):
    """未认证 (401)"""
    status_code = 401

    def __init__(self, message: str = "请先登录"):
        super().__init__(detail=message)

class ForbiddenException(AppException):
    """权限不足 (403)"""
    status_code = 403

    def __init__(self, message: str = "权限不足"):
        super().__init__(detail=message)

class ConflictException(AppException):
    """资源冲突 (409)"""
    status_code = 409

    def __init__(self, message: str):
        super().__init__(detail=message)