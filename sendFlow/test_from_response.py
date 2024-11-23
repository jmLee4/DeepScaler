import gevent
from locust import HttpUser, TaskSet, task, between
from locust.env import Environment
from locust.stats import stats_printer, stats_history
from locust.log import setup_logging

setup_logging("INFO", None)

class UserBehavior(TaskSet):
    @task
    def my_task(self):
        self.client.post("/cart", {
            'product_id': '66VCHSJNUP',
            'quantity': 3
        })
        response = self.client.post("/cart/checkout", {
            'email': 'someone@example.com',
            'street_address': '1600 Amphitheatre Parkway',
            'zip_code': '94043',
            'city': 'Mountain View',
            'state': 'CA',
            'country': 'United States',
            'credit_card_number': '4432-8015-6152-0454',
            'credit_card_expiration_month': '1',
            'credit_card_expiration_year': '2039',
            'credit_card_cvv': '672',
        })
        return response

class WebsiteUser(HttpUser):
    tasks = [UserBehavior]
    wait_time = between(5, 9)
    host = "http://localhost:30411"  # 指定基地址

# 创建一个Locust环境
env = Environment(user_classes=[WebsiteUser])

# 启动一个Locust runner
env.create_local_runner()

# 启动一个Web UI（可选）
# env.create_web_ui("127.0.0.1", 8089)

# 启动一个绿色线程来运行任务
gevent.spawn(stats_printer(env.stats))
gevent.spawn(stats_history, env.runner)

# 创建一个用户实例
user = WebsiteUser(env)

# 手动调用任务并获取结果
response = user.tasks[0](user).my_task()

# 打印详细的请求情况
print("请求URL:", response.url)
print("请求方法:", response.request.method)
print("请求头:", response.request.headers)
print("请求体:", response.request.body)
print("响应状态码:", response.status_code)
print("响应头:", response.headers)

content = response.text
if '<!DOCTYPE html>' in content:
    with open('./sendFlow/test_response.html', 'w', encoding='utf-8') as file:
        file.write(content)
    print("保存为HTML")
else:
    print("响应内容:", content)

# 停止Locust runner
env.runner.quit()