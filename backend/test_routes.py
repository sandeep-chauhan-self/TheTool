"""Simple test script to verify the new analysis routes work"""

import os
import sys
import tempfile

# Set test configuration before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['DB_PATH'] = os.path.join(tempfile.gettempdir(), 'test_trading_app.db')

sys.path.insert(0, os.path.dirname(__file__))

from app import app
from pathlib import Path

def test_routes():
    print("Testing new analysis routes...")

    with app.test_client() as client:
        # Test GET /analyze (should return method not allowed since it's POST only)
        resp = client.get('/analyze')
        assert resp.status_code == 405, f"Expected 405, got {resp.status_code}"
        print("✓ GET /analyze correctly returns 405 (method not allowed)")

        # Test POST /analyze with no data (should return 400)
        resp = client.post('/analyze')
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("✓ POST /analyze with no data correctly returns 400")

        # Test POST /analyze with empty tickers (should return 400)
        resp = client.post('/analyze', json={})
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        print("✓ POST /analyze with empty data correctly returns 400")

        # Test POST /analyze with tickers (should work - creates job)
        resp = client.post('/analyze', json={"tickers": ["INFY.NS"]})
        assert resp.status_code == 202, f"Expected 202, got {resp.status_code}"
        data = resp.get_json()
        assert "job_id" in data, "Response should contain job_id"
        job_id = data["job_id"]
        print(f"✓ POST /analyze created job {job_id}")

        # Test GET /status/<job_id>
        resp = client.get(f'/status/{job_id}')
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        status_data = resp.get_json()
        assert isinstance(status_data, dict), "Status should be a dict"
        print(f"✓ GET /status/{job_id} returned status data")

        # Test cancel job
        resp = client.post(f'/cancel-job/{job_id}')
        assert resp.status_code in [200, 404], f"Expected 200 or 404, got {resp.status_code}"
        print(f"✓ POST /cancel-job/{job_id} returned {resp.status_code}")

        # Test GET /report/<ticker> (should return 404 since no analysis done yet)
        resp = client.get('/report/INFY.NS')
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("✓ GET /report/INFY.NS correctly returns 404 (no analysis yet)")

    print("\nAll route tests passed! ✓")
    return True

if __name__ == "__main__":
    test_routes()
