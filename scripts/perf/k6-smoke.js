import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '1m',
  thresholds: {
    http_req_duration: ['p(99)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

const API = __ENV.API_BASE || 'http://localhost:8000';

export default function () {
  let r = http.get(`${API}/health/summary`);
  check(r, { 'health 200': res => res.status === 200 });
  sleep(1);
}

export function handleSummary(data) {
  return { 'k6-results.json': JSON.stringify(data, null, 2) };
}
