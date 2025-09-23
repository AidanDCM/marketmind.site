import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '2m',
  thresholds: {
    http_req_duration: ['p(99)<500'], // 99% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Error rate under 1%
  },
};

const API_BASE = __ENV.API_BASE || 'http://localhost:8000';

export default function () {
  // Health check endpoint
  let res = http.get(`${API_BASE}/health/summary`);
  check(res, {
    'health status is 200': (r) => r.status === 200,
    'health response has status': (r) => r.json('status') !== undefined,
  });

  // Test metrics endpoint (if available)
  res = http.get(`${API_BASE}/metrics`);
  check(res, {
    'metrics accessible': (r) => r.status === 200,
  });

  // Test auth endpoint rate limiting
  res = http.post(`${API_BASE}/auth/token`, {
    username: 'test',
    password: 'invalid'
  });
  check(res, {
    'auth responds appropriately': (r) => r.status === 400 || r.status === 422 || r.status === 429,
  });

  sleep(1);
}

export function handleSummary(data) {
  return {
    'k6-results.json': JSON.stringify(data),
  };
}
