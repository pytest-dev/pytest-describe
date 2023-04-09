"""Support for shared behaviors"""

__all__ = ["behaves_like"]


def behaves_like(*behavior_funcs):
    """Decorator for shared behaviors."""

    def decorator(func):
        try:
            func._behaves_like.extend(behavior_funcs)
        except AttributeError:
            func._behaves_like = behavior_funcs[:]
        return func

    return decorator
