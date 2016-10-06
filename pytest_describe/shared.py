def behaves_like(behavior_func):
    def decorator(func):
        if not hasattr(func, '_behaves_like'):
            func._behaves_like = []
        func._behaves_like.append(behavior_func)
        return func
    return decorator
