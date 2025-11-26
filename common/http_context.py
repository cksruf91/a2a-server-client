import inspect
from functools import wraps
from typing import Callable

import httpx


def get_httpx_context() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=60 * 3,
        headers={
            "Content-Type": "application/json",
        }
    )


def httpx_context(func: Callable):
    """
    비동기 함수 또는 비동기 제너레이터 함수를 래핑하는 데코레이터로, `httpx.AsyncClient` 인스턴스를 제공합니다.
    데코레이트된 함수는 미리 정의된 타임아웃과 헤더 설정이 포함된 HTTP 클라이언트에 접근할 수 있습니다.
    `httpx.AsyncClient` 인스턴스는 데코레이트된 함수의 **kwargs를 통해 `httpx_client` 인자로 전달됩니다.

    비동기 제너레이터 함수의 경우, 래퍼는 값을 yield하는 동안 `httpx.AsyncClient`가 적절하게 관리되도록 보장합니다.

    Args:
        func: 래핑할 비동기 함수 또는 비동기 제너레이터 함수

    Returns:
        `httpx.AsyncClient` 인스턴스가 함수의 **kwargs로 주입된 입력 함수 또는 제너레이터 함수의 래핑된 버전
    """
    if inspect.isasyncgenfunction(func):
        # Async generator function (yields values)
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with get_httpx_context() as httpx_client:
                kwargs['httpx_client'] = httpx_client
                async for event in func(*args, **kwargs):
                    yield event

        return wrapper
    else:
        # Regular async function (returns a value)
        @wraps(func)
        async def wrapper(*args, **kwargs):
            async with get_httpx_context() as httpx_client:
                kwargs['httpx_client'] = httpx_client
                return await func(*args, **kwargs)

        return wrapper
