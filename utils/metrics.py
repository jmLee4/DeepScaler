import numpy as np

# MAE (平均绝对误差)
def get_mae(y_pred, y_true):
    non_zero_pos = y_true != 0
    return np.fabs((y_true[non_zero_pos] - y_pred[non_zero_pos])).mean()

# RMSE (均方根误差)
def get_rmse(y_pred, y_true):
    non_zero_pos = y_true != 0
    return np.sqrt(np.square(y_true[non_zero_pos] - y_pred[non_zero_pos]).mean())

# MAPE (平均绝对百分比误差)
def get_mape(y_pred, y_true):
    non_zero_pos = (np.fabs(y_true) > 0.5)
    return np.fabs((y_true[non_zero_pos] - y_pred[non_zero_pos]) / y_true[non_zero_pos]).mean()
