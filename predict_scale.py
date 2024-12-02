import argparse
import datetime
import math
import os
import sys
import time

import numpy as np
import torch
import yaml
from torch.utils.data import DataLoader

import trainer
from dataset import TPDataset, TPDataset2
from generate_dataset import predict_read_and_generate_dataset
from metrics_fetch import save_all_fetched_data
from models import AdapGL
from utils import scaler
from utils.k8s_operator import K8sOperator

# 重构原先的predict_scale.py代码

def load_config(data_path):
    with open(data_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config

def fetch_and_process_data(iterate_time, services, metrics):
    current_time = datetime.datetime.now()
    current_time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    if iterate_time == 0:
        # 根据论文，首次迭代获取前80min的历史数据进行预测，后续迭代去最新的一次追加到之前的数据中，并舍弃最旧的1次数据
        start_time_str = (current_time - datetime.timedelta(hours=1) - datetime.timedelta(minutes=21)).strftime("%Y-%m-%d %H:%M:%S")
    else:
        start_time_str = (current_time - datetime.timedelta(seconds=55)).strftime("%Y-%m-%d %H:%M:%S")
    times_original = [(str(start_time_str), str(current_time_str))]
    print(times_original)

    save_all_fetched_data(times_original, 1, root_dir="./experiment/dataForPredict/", interval=60, services=services)

    data = {}
    for metric in metrics:
        data[metric] = []
        for service in services:
            file = f"./experiment/dataForPredict/1_{service}_{metric}.log"
            metric_data = np.genfromtxt(file, dtype=np.double)
            if iterate_time != 0:
                metric_data = np.array([metric_data])
            metric_data = metric_data[:, np.newaxis]
            data[metric].append(metric_data)
    return data

def main(args):
    k8s_operator = K8sOperator()
    services = ["adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend", "paymentservice", "productcatalogservice", "recommendationservice", "shippingservice"]
    metrics = ["pod", "cpu", "request_duration", "request_received", "memory"]

    iterate_time = 0
    while True:
        start = time.time()

        # 拉取数据
        data = fetch_and_process_data(iterate_time, services, metrics)

        # 初始化xx，或者是在非首轮迭代的时候舍弃最旧的1条数据，后面追加最新的1条数据
        timeLen = len(data["cpu"][0])
        if iterate_time == 0:
            xx = torch.tensor([])
        else:
            xx = xx[1:, :, :]

        # 拼接为一个大Tensor，对应data_process.py的逻辑
        for i in range(timeLen):
            all_metric_data = []
            for metric in metrics:
                metric_data = np.vstack([data[metric][j][i] for j in range(len(services))])
                metric_data = torch.tensor(metric_data, dtype=torch.float32)
                all_metric_data.append(metric_data)
            all_metric_data = torch.cat(all_metric_data, dim=1)
            yy = torch.unsqueeze(all_metric_data, dim=0)
            xx = torch.cat((xx, yy), dim=0)

        np.savez("./experiment/predict_scale", xx)
        all_data = predict_read_and_generate_dataset(graph_signal_matrix_filename="./experiment/predict_scale.npz", num_of_hours=1, num_for_predict=1, points_per_hour=80, save=True)

        print("Finish data generation, begin to predict")

        model_config = load_config(args.model_config_path)
        train_config = load_config(args.train_config_path)
        torch.manual_seed(train_config["seed"])
        torch.cuda.manual_seed(train_config["seed"])

        # ----------------------- 加载数据集 ------------------------
        Scaler = getattr(sys.modules["utils.scaler"], train_config["scaler"])
        data_scaler = Scaler(axis=(0, 1, 2))

        data_config = model_config["dataset"]
        device = torch.device(data_config["device"])
        data_name = "./experiment/predict_scale_1_dataset.npz"

        dataset = TPDataset2(os.path.join(data_config["data_dir"], data_name))
        data_scaler.fit(dataset.data["x"])
        dataset.fit(data_scaler)
        data_loader = DataLoader(dataset, batch_size=data_config["batch_size"])

        # ----------------------- 导入预测设置 ----------------------
        model_name = args.model_name
        model_config = model_config[model_name]
        model_config.update(data_config)
        Model = getattr(AdapGL, model_name, None)
        if Model is None:
            raise ValueError("Model {} is not right".format(model_name))
        predict_model = Model(**model_config).to(device)

        # 导入模型
        predict_model.load_state_dict(torch.load("./model_states/AdapGLA/AdapGLA.pkl"))
        adjacency_matrix = np.load("./model_states/AdapGLA/best_adj_mx.npy")
        adjacency_matrix = torch.from_numpy(adjacency_matrix)

        # 预测
        input_data = torch.from_numpy(data_loader.dataset.data["x"])
        predict_result = predict_model(input_data, adjacency_matrix).detach()
        predict_result = data_scaler.inverse_transform(data=predict_result, axis=0)

        # 基于预测结果确定Pod对应的副本数
        pods_num_to_scale = {}
        for idx, service in enumerate(services):
            service_pred = predict_result[-1, 0, idx]
            if math.isnan(service_pred):
                service_pred = 1
            restriction = 0.35
            if (float(service_pred) - math.floor(float(service_pred))) < restriction:
                pods_num_to_scale[service] = math.floor(float(service_pred))
            else:
                pods_num_to_scale[service] = math.ceil(float(service_pred))
            if pods_num_to_scale[service] <= 0:
                pods_num_to_scale[service] = 1

        print(f"Finish calculation, comsump {time.time()-start}s, ready to scaling")

        # 基于预测结果进行扩缩容
        for service in services:
            k8s_operator.scale_deployment_by_replicas(service, pods_num_to_scale[service])
        with open("./experiment/pods_num_to_scale.log", "a") as f:
            f.write(str(pods_num_to_scale) + "\n")
        print("Service scaling result:", pods_num_to_scale)

        # 每55s固定一个迭代周期
        duration = time.time() - start
        print(f"This iteration lasts for {duration}, requires {55-duration} of hibernation")
        if duration < 55:
            time.sleep(55 - duration)

        iterate_time += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model_config_path", type=str, default="./config/model_config.yaml", help="Config path of models")
    parser.add_argument("--train_config_path", type=str, default="./config/train_config.yaml", help="Config path of Trainer")
    parser.add_argument("--model_name", type=str, default="AdapGLT", help="Model name to train")
    parser.add_argument("--num_epoch", type=int, default=5, help="Training times per epoch")
    parser.add_argument("--num_iter", type=int, default=5, help="Maximum value for iteration")
    parser.add_argument("--model_save_path", type=str, default="./model_states/AdapGLA_1.pkl", help="Model save path")
    parser.add_argument("--max_graph_num", type=int, default=3, help="Volume of adjacency matrix set")
    args = parser.parse_args()

    main(args)
