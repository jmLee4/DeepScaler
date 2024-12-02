#coding=utf-8
import datetime
import os
import time
import urllib.parse

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

metrics = ["pod", "cpu", "request_duration", "request_received", "memory"]
training_root_dir = ""

# 原本是通过Prometheus的/query接口，每次只能单个查询，所以原本的代码实现是遍历每个时间点，不断发送该时间点的查询请求
# 现在改用/query_range接口，设置start、end、step参数即可一次性获得所有数据，加快数据的获取

def fetch_and_save_data(service_name, metric, start_time, end_time, interval, save_filename):

    # 服务下线时Prometheus不会存储有这一刻的数据，不添加默认值 vector(0) 会导致数据数目出现差异，影响后面Tensor的拼接；原有的代码逻辑是判断是否请求成功，失败则写入0
    api_str = promQL[metric].format(namespace, service_name, str(interval)+"s") + " or vector(0)"
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
                    print("0", file=f)
                else:
                    print(str(line[1]), file=f)

def save_all_fetched_data(times=[], start_index=1, root_dir="./testData/", interval=interval, services=services, metrics=metrics, print_log=False):

    # 不存在则创建
    if not os.path.exists(root_dir):
        os.makedirs(root_dir)

    for i, (start_time, end_or_lasted) in enumerate(times):
        start_time = datetime.datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S') #+ datetime.timedelta(hours=8)  # 时区问题
        end_time = datetime.datetime.strptime(end_or_lasted, '%Y-%m-%d %H:%M:%S') #+ datetime.timedelta(hours=8)

        # 遍历每个Service的每个Metric，提取特定时间段的指标
        for service in services:
            for metric in metrics:
                fetch_and_save_data(service, metric, start_time, end_time, interval, root_dir + "{}_{}_{}.log".format(start_index+i, service, metric))
                if print_log:
                    print("Saved file: " + root_dir + "{}_{}_{}.log".format(start_index+i, service, metric))

if __name__ == '__main__':

    # ("2023-03-04 04:09:01", "2023-03-04 05:25:15")
    # 这是原代码提供的时间戳，时间跨度是 4574s = 76min14s = 1h16min14s，比较短，论文所选用的负载一个周期应该在 2h30min 左右，不清楚是否该把该长度的时间作为基准

    times = [
        ("2024-11-24 17:43:00", "2024-11-25 06:50:00")
    ]
    save_all_fetched_data(times, start_index=1, root_dir='./data/train/', interval=30, services=services)
    print("Finish")
