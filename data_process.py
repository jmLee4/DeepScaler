import torch
import numpy as np
from generate_dataset import read_and_generate_dataset

services = [
    "adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend",
    "paymentservice", "productcatalogservice", "recommendationservice", "shippingservice"
]
metrics = ["pod", "cpu", "request_duration", "request_received", "memory"]

def load_data(service, metric):
    file = f'./data/train/1_{service}_{metric}.log'
    data = np.genfromtxt(file, dtype=np.double)
    return data[:, np.newaxis]

data_dict = {metric: {service: load_data(service, metric) for service in services} for metric in metrics}

timeLen = len(data_dict["cpu"]["adservice"])
xx = torch.tensor([])

# 将所有数据拼接为一个大的Tensor
for i in range(timeLen):
    listpod = np.vstack([data_dict["pod"][service][i] for service in services])
    listcpu = np.vstack([data_dict["cpu"][service][i] for service in services])
    listres = np.vstack([data_dict["request_duration"][service][i] for service in services])
    listreq = np.vstack([data_dict["request_received"][service][i] for service in services])
    listmem = np.vstack([data_dict["memory"][service][i] for service in services])

    listpod = torch.as_tensor(listpod, dtype=torch.float32)
    listcpu = torch.as_tensor(listcpu, dtype=torch.float32)
    listres = torch.as_tensor(listres, dtype=torch.float32)
    listreq = torch.as_tensor(listreq, dtype=torch.float32)
    listmem = torch.as_tensor(listmem, dtype=torch.float32)

    listt = torch.cat((listpod, listcpu, listres, listreq, listmem), dim=1)
    yy = torch.unsqueeze(listt, dim=0)
    xx = torch.cat((xx, yy), dim=0)

xx = xx.numpy()
print("Shape of train.npz:", xx.shape)
np.savez("./data/train.npz", xx)

# 基于这个大Tensor，构造时序预测的数据集
read_and_generate_dataset(graph_signal_matrix_filename='./data/train.npz', num_of_hours=1, num_for_predict=1, points_per_hour=80, save=True)
