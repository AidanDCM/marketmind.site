from locust import HttpUser, TaskSet, between, task


class HealthCheckBehavior(TaskSet):
    @task(5)
    def check_health(self):
        """Exercise health endpoints used by verify_integrations."""
        self.client.get("/health/live")
        self.client.get("/health/ready")
        self.client.get("/health/data")


class PricingBehavior(TaskSet):
    @task(1)
    def pricing_history(self):
        self.client.get("/pricing/history", params={"asin": "B08N5WRWNW", "limit": 5})

    @task(1)
    def pricing_pending(self):
        self.client.get("/pricing/pending", params={"limit": 5})

    @task(1)
    def pricing_approved(self):
        self.client.get("/pricing/approved", params={"limit": 5})


class OrdersBehavior(TaskSet):
    @task(1)
    def order_detail(self):
        self.client.get("/orders/1")

    @task(1)
    def orders_kpis(self):
        self.client.get("/orders/kpis")

    @task(1)
    def orders_actions(self):
        self.client.post("/orders/1/reprocess", json={})
        self.client.post("/orders/1/route", json={})
        self.client.post("/orders/1/po", json={})
        self.client.post("/orders/1/fulfill", json={})
        self.client.post("/orders/1/exception", json={"kind": "OOS", "note": "test"})


class WebsiteUser(HttpUser):
    """Main user class for performance testing (Phase 8 endpoints)."""

    tasks = [HealthCheckBehavior, PricingBehavior, OrdersBehavior]
    wait_time = between(0.5, 2.0)
    host = "http://127.0.0.1:8001"


class HighLoadUser(HttpUser):
    """High load user focused on pricing + health."""

    tasks = [PricingBehavior, HealthCheckBehavior]
    wait_time = between(0.1, 0.5)
    host = "http://127.0.0.1:8001"
