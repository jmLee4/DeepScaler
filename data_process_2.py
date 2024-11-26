import torch
import numpy as np
import datetime
from metrics_fetch import save_all_fetched_data
from prepareData import read_and_generate_dataset

services = [
    "adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend",
    "paymentservice", "productcatalogservice", "recommendationservice", "shippingservice"
]
metrics = ["pod", "cpu", "request_duration", "request_received"]

def load_data(service, metric):
    file = f'./train/1_{service}_{metric}.log'
    data = np.genfromtxt(file, dtype=np.double)
    return data[:, np.newaxis]

data_dict = {metric: {service: load_data(service, metric) for service in services} for metric in metrics}

timeLen = len(data_dict["cpu"]["adservice"])
xx = torch.tensor([])

for i in range(timeLen):
    listpod = np.vstack([data_dict["pod"][service][i] for service in services])
    listcpu = np.vstack([data_dict["cpu"][service][i] for service in services])
    listres = np.vstack([data_dict["request_duration"][service][i] for service in services])
    listreq = np.vstack([data_dict["request_received"][service][i] for service in services])
    listmem = np.vstack([data_dict["request_received"][service][i] for service in services])  # Assuming "mem" is same as "request_received"

    listpod = torch.tensor(listpod, dtype=torch.float32)
    listcpu = torch.tensor(listcpu, dtype=torch.float32)
    listres = torch.tensor(listres, dtype=torch.float32)
    listreq = torch.tensor(listreq, dtype=torch.float32)
    listmem = torch.tensor(listmem, dtype=torch.float32)

    listt = torch.cat((listpod, listcpu, listres, listreq, listmem), dim=1)
    yy = torch.unsqueeze(listt, dim=0)
    xx = torch.cat((xx, yy), dim=0)

xx = xx.numpy()
print(xx.shape)
np.savez("./train2", xx)

all_data = read_and_generate_dataset(graph_signal_matrix_filename='./train2.npz', num_of_hours=1, num_for_predict=1, points_per_hour=80, save=True)