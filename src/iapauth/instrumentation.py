"""
dummy functions for instrumentation

fall back to these if `beeline` isn't available.
"""
import functools


def add_context_field(name, value):
    pass


def traced(name, trace_id=None, parent_id=None):
    def decorator_traced(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator_traced
