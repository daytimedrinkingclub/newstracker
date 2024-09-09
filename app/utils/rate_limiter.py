import time
from functools import wraps
from queue import Queue
import threading

class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = Queue()
        self.lock = threading.Lock()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.lock:
                now = time.time()
                if self.calls.qsize() >= self.max_calls:
                    oldest_call = self.calls.get()
                    if now - oldest_call < self.period:
                        time.sleep(self.period - (now - oldest_call))
                self.calls.put(now)
            return func(*args, **kwargs)
        return wrapper

def exponential_backoff(max_retries=5, base_delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if '429' in str(e):
                        delay = base_delay * (2 ** retries)
                        time.sleep(delay)
                        retries += 1
                    else:
                        raise
            raise Exception("Max retries exceeded")
        return wrapper
    return decorator