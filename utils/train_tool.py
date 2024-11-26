import time
import functools
import numpy as np


class EarlyStop:
    def __init__(self, tolerance_num, min_is_best):
        
        # 容忍指标未改善的最大迭代次数
        self.tolerance_num = tolerance_num
        # 布尔值，指示指标是否越小越好
        self.min_is_best = min_is_best

        self.count, self.cur_value = None, None
        self.reset()

    def reset(self):
        self.count = 0
        finfo = np.finfo(np.float32)
        self.cur_value = finfo.max if self.min_is_best else finfo.min

    def reach_stop_criteria(self, cur_value):
        if self.min_is_best:
            self.count = self.count + 1 if cur_value >= self.cur_value else 0
        else:
            self.count = self.count + 1 if cur_value <= self.cur_value else 0

        if self.count == self.tolerance_num:
            print(f"Early stopping triggered. Tolerance reached: {self.tolerance_num}")
            return True

        self.cur_value = cur_value
        return False

# 计算函数执行开销的装饰器
def time_decorator(func):
    TIME_FORMAT = "Time Consumption: {:.4f}s"
    
    @functools.wraps(func)
    def inner(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(TIME_FORMAT.format(end_time - start_time))
        return result
    return inner
