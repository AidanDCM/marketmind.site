from locust import HttpUser, task, between
import json

class MarketMindUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Called when a user starts"""
        # Test initial health check
        self.client.get("/health/summary")
    
    @task(3)
    def health_check(self):
        """Primary health endpoint - most frequent"""
        with self.client.get("/health/summary", catch_response=True) as response:
            if response.status_code == 200:
                try:
                    json_response = response.json()
                    if json_response.get("status") == "ok":
                        response.success()
                    else:
                        response.failure(f"Health status not ok: {json_response}")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def metrics_endpoint(self):
        """Metrics endpoint for monitoring"""
        self.client.get("/metrics")
    
    @task(1)
    def auth_rate_limit_test(self):
        """Test auth endpoint (should be rate limited)"""
        self.client.post("/auth/token", json={
            "username": "test_user",
            "password": "invalid_password"
        })
    
    @task(1)
    def dashboard_kpis(self):
        """Test dashboard KPI endpoint"""
        self.client.get("/kpis")

# Run with: locust -f scripts/locust-load-test.py --host=http://localhost:8000
