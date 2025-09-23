from locust import HttpUser, task, between

class ApiUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health(self):
        r = self.client.get("/health/summary")
        assert r.status_code == 200
