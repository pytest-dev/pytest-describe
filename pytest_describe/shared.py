def behaves_like(*behavior_funcs):
    def decorator(func):
        if not hasattr(func, '_behaves_like'):
            func._behaves_like = []
        func._behaves_like += behavior_funcs
        return func
    return decorator
