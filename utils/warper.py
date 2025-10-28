# -*- coding: utf-8 -*-
"""
Created on Tue Apr 23 13:57:54 2024

@author: Billy_Hsu
"""


import time
from contextlib import asynccontextmanager
from functools import wraps


class AsyncTimer:
    def __init__(self):
        self.execution_times = {}

    @asynccontextmanager
    async def timer(self):
        try:
            yield self
        finally:
            pass

    def timeit(self, async_func):
        @wraps(async_func)
        async def wrapper(*args, **kwargs):
            self.update_start_time(async_func.__name__)
            result = await async_func(*args, **kwargs)
            self.update_end_time(async_func.__name__)
            print(
                f"{async_func.__name__} executed in {self.execution_times[f'{async_func.__name__}_end'] - self.execution_times[f'{async_func.__name__}_start']:.4f} seconds"  # noqa: E501
            )
            return result

        return wrapper

    def update_start_time(self, func_name):
        self.execution_times[f"{func_name}_start"] = time.perf_counter()

    def update_end_time(self, func_name):
        self.execution_times[f"{func_name}_end"] = time.perf_counter()

    def get_times(self):
        return self.execution_times


async_timer = AsyncTimer()


# 创建一个异步装饰器来测量函数执行时间
def timeit(async_func):
    async def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # 开始时间
        result = await async_func(*args, **kwargs)  # 执行异步函数
        end_time = time.perf_counter()  # 结束时间
        print(
            f"{async_func.__name__} executed in {end_time - start_time:.4f} seconds"
        )  # 打印执行时间
        return result

    return wrapper


def timeit_sync(sync_func):
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()  # 开始时间
        result = sync_func(*args, **kwargs)  # 执行同步函数
        end_time = time.perf_counter()  # 结束时间
        print(
            f"{sync_func.__name__} executed in {end_time - start_time:.4f} seconds"
        )  # 打印执行时间
        return result

    return wrapper
