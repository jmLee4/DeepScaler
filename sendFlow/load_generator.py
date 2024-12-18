from locust import HttpUser, TaskSet, task, constant
from locust import LoadTestShape
import random
from random import randint, choice
import base64

class BookInfoUserTasks(TaskSet):
    def __init__(self, parent):
        super().__init__(parent)

    @task(1)
    def get_productpage(self):
        self.client.get("/productpage")
    
    @task(1)
    def get_details(self):
        self.client.get("/details")

    @task(1)
    def get_reviews(self):
        self.client.get("/reviews")
    
    @task(1)
    def get_ratings(self):
        self.client.get("/ratings")

class BoutiqueUserTasks(TaskSet):
    def __init__(self, parent):
        super().__init__(parent)
        self.products = [
            '0PUK6V6EV0',
            '1YMWWN1N4O',
            '2ZYFJ3GM2N',
            '66VCHSJNUP',
            '6E92ZMYYFZ',
            '9SIQT8TOJO',
            'L9ECAV7KIM',
            'LS4PSXUNUM',
            'OLJCESPC7Z',
        ]

    @task(1)
    def index(self):
        self.client.get("/")

    @task(2)
    def setCurrency(self):
        currencies = ['EUR', 'USD', 'JPY', 'CAD']
        self.client.post("/setCurrency", {'currency_code': random.choice(currencies)})

    @task(10)
    def browseProduct(self):
        self.client.get("/product/" + random.choice(self.products))

    @task(2)
    def viewCart(self):
        self.client.get("/cart")

    @task(3)
    def addToCart(self):
        product = random.choice(self.products)
        self.client.get("/product/" + product)
        self.client.post("/cart", {
            'product_id': product,
            'quantity': random.choice([1, 2, 3, 4, 5, 10])
        })

    @task(1)
    def checkout(self):
        self.addToCart()
        self.client.post("/cart/checkout", {
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

class WebsiteUser(HttpUser):
    def on_start(self):
        return super().on_start()

    def on_stop(self):
        return super().on_stop()

    host = "http://localhost:30411"
    wait_time = constant(1)
    # tasks = [BookInfoUserTasks]
    tasks = [BoutiqueUserTasks]
    
class StagesShape(LoadTestShape):
    def __init__(self):
        super().__init__()
        lines = []
        with open("./sendFlow/random-100max.req", 'r') as f:
            lines = list(map(int, f.readlines()))
            self.lines = ([1] * 5 + lines + [1] * 5)
    
    def tick(self):
        run_time = self.get_run_time()
        for _ in range(10):
            for i, v in enumerate(self.lines):
                if run_time < (i+1) * 10:
                    tick_data = (v, 100)                
                    return tick_data
