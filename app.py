#!/usr/bin/env python3
"""
Simplified Metrics Application for Grafana MCP Server Demo
Generates basic HTTP request and active user metrics
"""

import time
import random
import threading
from flask import Flask
from prometheus_client import (
    Counter, Gauge, generate_latest, CollectorRegistry, CONTENT_TYPE_LATEST
)

app = Flask(__name__)

# Development configuration for better live reload
app.config['ENV'] = 'development'
app.config['DEBUG'] = True
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Create a custom registry
registry = CollectorRegistry()

# Define metrics - keeping only the essentials
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

active_users = Gauge(
    'active_users_count',
    'Number of currently active users',
    registry=registry
)

class MetricsUpdater:
    """Background thread to update active users metric"""
    
    def __init__(self):
        self.running = True
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        
    def start(self):
        self.thread.start()
        
    def stop(self):
        self.running = False
        
    def _update_loop(self):
        while self.running:
            try:
                # Simulate active users count
                active_users.set(random.randint(50, 200))
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"Error updating metrics: {e}")
                time.sleep(5)

# Start metrics updater
metrics_updater = MetricsUpdater()
metrics_updater.start()

@app.route('/metrics')
def metrics():
    """Prometheus metrics endpoint"""
    return generate_latest(registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}

@app.route('/')
def home():
    """Home endpoint"""
    # Simulate some processing time
    time.sleep(random.uniform(0.1, 0.5))
    
    # Record request
    request_count.labels(method='GET', endpoint='/', status='200').inc()
    
    return "Welcome to the Simplified Metrics Demo App!"

@app.route('/api/users')
def api_users():
    """API endpoint that occasionally generates errors"""
    # Simulate processing time
    time.sleep(random.uniform(0.05, 0.3))
    
    # Simulate occasional errors (5% chance)
    if random.random() < 0.05:
        request_count.labels(method='GET', endpoint='/api/users', status='500').inc()
        return "Internal Server Error", 500
    
    # Record successful request
    request_count.labels(method='GET', endpoint='/api/users', status='200').inc()
    
    return {"users": ["alice", "bob", "charlie"], "count": 3}

@app.route('/api/load')
def simulate_load():
    """Endpoint to simulate heavier processing"""
    # Simulate heavy processing
    time.sleep(random.uniform(1.0, 3.0))
    
    request_count.labels(method='GET', endpoint='/api/load', status='200').inc()
    
    return {"message": "Heavy processing completed"}

@app.route('/health')
def health():
    """Health check endpoint"""
    request_count.labels(method='GET', endpoint='/health', status='200').inc()
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == '__main__':
    print("Starting Simplified Metrics Demo Application...")
    print("Metrics available at: http://localhost:8000/metrics")
    print("Application endpoints:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/api/users")
    print("  - http://localhost:8000/api/load")
    print("  - http://localhost:8000/health")
    print("\nExposing metrics:")
    print("  - http_requests_total (method, endpoint, status)")
    print("  - active_users_count")
    print("\n🔄 Live reload enabled - code changes will auto-restart the server")
    
    # Enhanced development server configuration
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
        use_reloader=True,
        use_debugger=True,
        threaded=True,
        extra_files=None  # Flask will auto-detect Python files
    )