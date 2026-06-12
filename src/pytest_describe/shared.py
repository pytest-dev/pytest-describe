"""Support for shared behaviors"""

from collections.abc import Callable
from typing import Any, TypeVar

__all__ = ["behaves_like"]

F = TypeVar("F", bound=Callable[..., Any])


def behaves_like(*behavior_funcs: Callable[..., Any]) -> Callable[[F], F]:
    """Decorator for shared behaviors."""

    def decorator(func: F) -> F:
        try:
            func._behaves_like.extend(behavior_funcs)  # type: ignore[attr-defined]
        except AttributeError:
            func._behaves_like = behavior_funcs[:]  # type: ignore[attr-defined]
        return func

    return decorator
