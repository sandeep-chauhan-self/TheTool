#!/usr/bin/env python3
from app import app
import os
import tempfile

# Set test database
os.environ['DB_PATH'] = os.path.join(tempfile.gettempdir(), 'test_trading_app.db')

app.config['TESTING'] = True

with app.test_client() as client:
    resp = client.post('/analyze', json={})
    print(f"Status: {resp.status_code}")
    print(f"Data: {resp.get_data()}")
    print(f"JSON: {resp.get_json()}")
