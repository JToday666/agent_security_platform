from fastapi import HTTPException, status


def success(data=None, message: str = "success") -> dict:
    return {
        "code": 0,
        "data": data,
        "message": message,
    }


def fail(http_status: int, code: int, message: str) -> HTTPException:
    return HTTPException(
        status_code=http_status,
        detail={
            "code": code,
            "data": None,
            "message": message,
        },
    )


def unauthorized(message: str = "token 无效或已过期") -> HTTPException:
    return fail(status.HTTP_401_UNAUTHORIZED, 401, message)
