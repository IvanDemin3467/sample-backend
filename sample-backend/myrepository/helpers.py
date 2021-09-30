import time

def measure_time(func):
    def inner(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            ex_time = time.time() - start_time
            print(f'Execution time: {ex_time:.2f} seconds')

    return inner


def memoize(func):
    _cache = {}

    def wrapper(*args, **kwargs):
        name = func.__name__
        key = (name, args, frozenset(kwargs.items()))
        if key in _cache:
            return _cache[key]
        response = func(*args, **kwargs)
        _cache[key] = response
        return response

    return wrapper
