from functools import wraps


def default_function(func):
    func.is_default_function = True
    return func


def on_preprocess(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.initialized_for_preprocessing:
            raise RuntimeError(
                f"{func.__name__} requires preprocessing initialization."
            )
        return func(self, *args, **kwargs)

    return wrapper


def on_postprocess(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.initialized_for_postprocessing:
            raise RuntimeError(
                f"{func.__name__} requires postprocessing initialization."
            )
        return func(self, *args, **kwargs)

    return wrapper
