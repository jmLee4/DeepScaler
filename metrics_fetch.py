#coding=utf-8
import datetime
import os
import time
import urllib.parse

import numpy as np
import pandas as pd
import requests

promQL = {
    # 分配的CPU利用率
    "cpu": "sum(irate(container_cpu_usage_seconds_total{{container=~'{1}',namespace=~'{0}'}}[1m])) / sum(container_spec_cpu_quota{{container=~'{1}',namespace=~'{0}'}} / container_spec_cpu_period{{container=~'{1}',namespace=~'{0}'}})",
    
    # 内存利用率
    "memory": "sum(container_memory_usage_bytes{{container=~'{1}',namespace=~'{0}'}}) / sum(container_spec_memory_limit_bytes{{container=~'{1}',namespace=~'{0}'}})",
    
    # 请求的平均处理时间
    "request_duration": "sum(rate(istio_request_duration_milliseconds_sum{{reporter='destination',destination_workload_namespace='{0}',destination_workload='{1}'}}[{2}])) / sum(rate(istio_request_duration_milliseconds_count{{reporter='destination',destination_workload_namespace='{0}',destination_workload='{1}'}}[{2}]))",
    
    # 接收到的请求次数
    "request_received": "sum(rate(istio_requests_total{{destination_workload_namespace='{0}',destination_workload='{1}'}}[{2}]))",
    
    # Pod数量
    "pod": "count(container_spec_cpu_period{{namespace=~'{0}',container=~'{1}'}})"
}

prometheus_api = "http://localhost:30090/api/v1/query_range?query="
namespace = "default"
interval = 120
services = [
    "adservice", "cartservice", "checkoutservice", "currencyservice", "emailservice", "frontend",
    "paymentservice", "productcatalogservice", "recommendationservice", "shippingservice"
]

metrics = ["pod", "cpu", "request_duration", "request_received"]
training_root_dir = ""

def fetch_cpu_utilization(service_name, namespace=namespace):
    cpu_api = promQL["cpu"].format(namespace, service_name)
    url = prometheus_api + urllib.parse.quote_plus(cpu_api)
    response = requests.get(url).json()["data"]
    v = 0
    if "result" in response and len(response["result"]) > 0 and "value" in response["result"][0]:
        v = response["result"][0]["value"][1]
    return float(v)

def fetch_mem_utilization(service_name, namespace=namespace):
    mem_api = promQL["memory"].format(namespace, service_name)
    url = prometheus_api + urllib.parse.quote_plus(mem_api)
    response = requests.get(url).json()["data"]
    v = 0
    if "result" in response and len(response["result"]) > 0 and "value" in response["result"][0]:
        v = response["result"][0]["value"][1]
    return float(v)

def fetch_res_time(service_name, namespace=namespace, interval=30):
    res_api = promQL["request_duration"].format(namespace, service_name, str(interval)+'s')
    url = prometheus_api + urllib.parse.quote_plus(res_api)
    res = requests.get(url).json()["data"]
    if "result" in res and len(res["result"]) > 0 and "value" in res["result"][0]:
        v = res["result"][0]["value"]
        if v[1] != 'NaN':
            return float(v[1])
    return 0

def fetch_req(service_name, namespace=namespace, interval=30):
    req_api = promQL["request_received"].format(namespace, service_name, str(interval)+'s')
    url = prometheus_api + urllib.parse.quote_plus(req_api)
    req = requests.get(url).json()["data"]
    if "result" in req and len(req["result"]) > 0 and "value" in req["result"][0]:
        v = req["result"][0]["value"]
        if v[1] != 'NaN':
            return int(float(v[1]))
    return 0

def fetch_prior_req(service_name, namespace=namespace, interval=30, delta=30):
    req_api = promQL["request_received"].format(namespace, service_name, str(interval)+'s')
    url = prometheus_api + urllib.parse.quote_plus(req_api) + "&time=" + str(time.time() - delta)
    req = requests.get(url).json()["data"]
    if "result" in req and len(req["result"]) > 0 and "value" in req["result"][0]:
        v = req["result"][0]["value"]
        if v[1] != 'NaN':
            return int(float(v[1]))
    return 0

def fetch_pod_number(service_name, namespace=namespace):
    pod_api = promQL["pod"].format(namespace, service_name)
    url = prometheus_api + urllib.parse.quote_plus(pod_api)
    response = requests.get(url).json()["data"]
    if "result" in response and len(response["result"]) > 0 and "value" in response["result"][0]:
        v = response["result"][0]["value"]
        if v[1] != "NaN":
            return int(float(v[1]))
    return 0

def save_fetch_data(service_name, mode, start_time, latsted_time, interval, save_file):
    api_str = promQL[mode].format(namespace, service_name, str(interval)+'s')
    with open(save_file, 'w') as f:
        for i in range(0, latsted_time, int(interval)):#以interval为间隔
            t = start_time + datetime.timedelta(seconds=i)#加时间
            unixtime = time.mktime(t.timetuple())#返回用秒数来表示时间的浮点数。
            url = prometheus_api + urllib.parse.quote_plus(api_str) + "&time=" + str(unixtime)
            response = requests.get(url).json()["data"]
            # {"resultType": "vector", "result": [{"metric":{}, "value": [<timestamp>, <value>]}]}
            if "result" in response and len(response["result"]) > 0 and "value" in response["result"][0]:
                v = response["result"][0]["value"]
                if v[1] == 'NaN':
                    print("0", file=f)
                else:
                    print(str(v[1]), file=f)
            else:
                print("0", file=f)

# 原本是通过Prometheus的/query接口，每次只能单个查询，所以原本的代码实现是遍历每个时间点，不断发送该时间点的查询请求
# 现在改用/query_range接口，设置start、end、step参数即可一次性获得所有数据，加快数据的获取

def fetch_and_save_data(service_name, metric, start_time, end_time, interval, save_filename):

    # 服务下线时Prometheus不会存储有这一刻的数据，不添加默认值 vector(0) 会导致数据数目出现差异，影响后面Tensor的拼接
    api_str = promQL[metric].format(namespace, service_name, str(interval)+'s') + " or vector(0)"
    with open(save_filename, "w") as f:
        start_time_unix = str(time.mktime(start_time.timetuple()))
        # 原代码逻辑是左闭右开区间，改用/query_range接口是左右闭区间，但不影响，只需保证每个文件的数目相同即可
        end_time_unix = str(time.mktime(end_time.timetuple()))
        url = prometheus_api + urllib.parse.quote_plus(api_str) + "&start=" + start_time_unix + "&end=" + end_time_unix + "&step=" + str(interval)

        response = requests.get(url).json()["data"]
        if "result" in response and len(response["result"]) > 0 and "values" in response["result"][0]:
            lines = response["result"][0]["values"]
            
            for line in lines:
                if line[1] == "NaN":
                    print(str(line[0]), "0", file=f)
                else:
                    print(str(line[0]), str(line[1]), file=f)

def save_all_fetched_data(times=[], start_index=1, root_dir="./testData/", interval=interval, services=services, metrics=metrics):

    # 不存在则创建
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)

    for i, (start_time, end_or_lasted) in enumerate(times):
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=8)  # 时区问题
        end_time = datetime.datetime.strptime(end_or_lasted, '%Y-%m-%d %H:%M:%S') + datetime.timedelta(hours=8)

        # 遍历每个Service的每个Metric，提取特定时间段的指标
        for service in services:
            for metric in metrics:
                fetch_and_save_data(service, metric, start_time, end_time, interval, root_dir + "{}_{}_{}.log".format(start_index+i, service, metric))
                print("Saved file: " + root_dir + "{}_{}_{}.log".format(start_index+i, service, metric))

def load_fetch_data(root_dir, start_iter=1, end_iter=None, services=services, metrics=metrics) -> pd.DataFrame:
    if not end_iter:
        end_iter = start_iter
    data = {}
    for svc in services:
        data[svc] = {}
        for m in metrics:
            data[svc][m] = []
    for svc in services:
        for m in metrics:
            for iternum in range(start_iter, end_iter+1):
                path = root_dir + '{}_{}_{}.log'.format(iternum, svc, m)
                with open(path, 'r') as f:
                    lines = f.readlines()
                data[svc][m] += list(map(lambda x:float(x), lines))
    D = [data[svc][m] for svc in services for m in metrics]
    data_df = pd.DataFrame(np.array(D).T, columns=[svc+"_"+m for svc in services for m in metrics])
    return data_df

def load_processed_fetch_data(iternums=[1, 2], root_dir=training_root_dir, metrics=metrics):
    data_df = load_fetch_data(iternums, root_dir, metrics)
    D, l = [], len(metrics)
    for r in data_df.values:
        D.append([1]+list(r[:l]))
        D.append([2]+list(r[l:2*l]))
        D.append([3]+list(r[2*l:3*l]))
        D.append([4]+list(r[3*l:]))
    data_df = pd.DataFrame(D, columns=['svc']+metrics)
    data_df['pod'] = data_df['pod'].astype(int)
    return data_df

if __name__ == '__main__':

    # ("2023-03-04 04:09:01", "2023-03-04 05:25:15")
    # 这是原代码提供的时间戳，时间跨度是 4574s = 76min14s = 1h16min14s，比较短，论文所选用的负载一个周期应该在 2h30min 左右，不清楚是否该把该长度的时间作为基准

    times = [
        ("2024-11-24 17:43:00", "2024-11-25 06:50:00")
    ]
    save_all_fetched_data(times, start_index=1, root_dir='./data/train/', interval=30, services=services)
    print("Finish")
