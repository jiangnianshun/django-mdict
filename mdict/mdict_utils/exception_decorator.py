import functools


def search_exception(default_value=[]):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # return func(*args, **kwargs)
            try:
                return func(*args, **kwargs)
            except FileNotFoundError as e:
                print(e)
            except AttributeError as e:
                print(e)
            except Exception as e:
                print(e)
            return default_value
        return wrapper
    return decorator
