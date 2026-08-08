import http from 'k6/http';
import { check, sleep } from 'k6';

// Run with: k6 run scripts/load_test.js
export const options = {
    stages: [
        { duration: '30s', target: 10 }, // Low load baseline
        { duration: '1m', target: 50 },  // Moderate concurrency
        { duration: '30s', target: 100 }, // Gradually increasing load
        { duration: '30s', target: 0 },   // Scale down
    ],
    thresholds: {
        http_req_duration: ['p(95)<250', 'p(99)<500'], // 95% of requests must complete below 250ms
        http_req_failed: ['rate<0.01'],                // Max 1% error rate
    },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';
const API_KEY = __ENV.API_KEY || 'test-secret-api-key';

export default function () {
    const params = {
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
        },
    };

    // 1. Health check endpoint (verify basic connectivity and minimal DB pool contention)
    const healthRes = http.get(`${BASE_URL}/health`);
    check(healthRes, {
        'health is status 200': (r) => r.status === 200,
    });

    // 2. Async message processing endpoint (verify Celery enqueuing performance)
    const payload = JSON.stringify({
        message_id: `msg_${__VU}_${__ITER}`,
        user_id: `user_${__VU}`,
        conversation_type: 'personal',
        created_at: new Date().toISOString(),
        message_text: `Test message ${__VU}:${__ITER}`
    });

    const routeRes = http.post(`${BASE_URL}/api/v1/messages/process-async`, payload, params);
    check(routeRes, {
        'async route is status 202': (r) => r.status === 202,
    });

    sleep(1); // Simulate real user pacing
}
