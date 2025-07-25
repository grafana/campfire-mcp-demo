#!/usr/bin/env python3
"""
Load Generation Script for Simplified Metrics Demo App
Generates traffic to create interesting metrics patterns
"""

import time
import random
import requests
import argparse
from concurrent.futures import ThreadPoolExecutor

class LoadGenerator:
    def __init__(self, base_url="http://localhost:8000", max_workers=5):
        self.base_url = base_url
        self.max_workers = max_workers
        self.running = False

    def make_request(self, endpoint, delay=None):
        """Make a single request to the specified endpoint"""
        try:
            if delay:
                time.sleep(delay)
            response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
            return response.status_code, response.elapsed.total_seconds()
        except Exception as e:
            print(f"Request failed: {e}")
            return None, None

    def generate_normal_load(self, duration=60, requests_per_second=2):
        """Generate normal application load"""
        print(f"Generating normal load for {duration} seconds at {requests_per_second} RPS...")

        end_time = time.time() + duration
        endpoints = ['/', '/api/users', '/health']

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while time.time() < end_time and self.running:
                endpoint = random.choice(endpoints)
                executor.submit(self.make_request, endpoint)
                time.sleep(1.0 / requests_per_second)

    def generate_spike_load(self, duration=30, requests_per_second=10):
        """Generate traffic spike"""
        print(f"Generating spike load for {duration} seconds at {requests_per_second} RPS...")

        end_time = time.time() + duration

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while time.time() < end_time and self.running:
                # Mix of different endpoints during spike
                endpoints = ['/', '/api/users', '/api/load', '/health']
                weights = [0.3, 0.4, 0.2, 0.1]  # More load on /api/load
                endpoint = random.choices(endpoints, weights=weights)[0]

                executor.submit(self.make_request, endpoint)
                time.sleep(1.0 / requests_per_second)

    def generate_error_pattern(self, duration=60, error_rate=0.15):
        """Generate requests that cause errors"""
        print(f"Generating error pattern for {duration} seconds with {error_rate*100}% error rate...")

        end_time = time.time() + duration

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while time.time() < end_time and self.running:
                # Focus on endpoints that can generate errors
                endpoint = '/api/users'  # This endpoint has a 5% error rate built-in
                executor.submit(self.make_request, endpoint)
                time.sleep(0.5)  # 2 RPS

    def generate_slow_requests(self, duration=60):
        """Generate slow requests to show latency patterns"""
        print(f"Generating slow request pattern for {duration} seconds...")

        end_time = time.time() + duration

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            while time.time() < end_time and self.running:
                # Focus on the slow endpoint
                executor.submit(self.make_request, '/api/load')
                time.sleep(2)  # Slow down requests to let them complete

    def run_demo_scenario(self):
        """Run a complete demo scenario with different patterns"""
        print("Starting complete demo scenario...")
        self.running = True

        scenarios = [
            ("Normal Load", lambda: self.generate_normal_load(120, 3)),
            ("Traffic Spike", lambda: self.generate_spike_load(60, 15)),
            ("Recovery Period", lambda: self.generate_normal_load(60, 2)),
            ("Error Pattern", lambda: self.generate_error_pattern(90)),
            ("Slow Requests", lambda: self.generate_slow_requests(90)),
            ("Final Normal Load", lambda: self.generate_normal_load(120, 3))
        ]

        for name, scenario_func in scenarios:
            if not self.running:
                break
            print(f"\n--- {name} ---")
            scenario_func()
            if self.running:
                print("Waiting 30 seconds before next scenario...")
                time.sleep(30)

        print("\nDemo scenario completed!")

    def stop(self):
        """Stop the load generator"""
        self.running = False

def main():
    parser = argparse.ArgumentParser(description='Load Generator for Metrics Demo')
    parser.add_argument('--url', default='http://localhost:8000',
                       help='Base URL of the application')
    parser.add_argument('--scenario', choices=['normal', 'spike', 'errors', 'slow', 'demo'],
                       default='demo', help='Load pattern to generate')
    parser.add_argument('--duration', type=int, default=120,
                       help='Duration in seconds for single scenarios')
    parser.add_argument('--rps', type=int, default=3,
                       help='Requests per second for normal load')

    args = parser.parse_args()

    generator = LoadGenerator(args.url)

    try:
        if args.scenario == 'normal':
            generator.running = True
            generator.generate_normal_load(args.duration, args.rps)
        elif args.scenario == 'spike':
            generator.running = True
            generator.generate_spike_load(args.duration, args.rps * 3)
        elif args.scenario == 'errors':
            generator.running = True
            generator.generate_error_pattern(args.duration)
        elif args.scenario == 'slow':
            generator.running = True
            generator.generate_slow_requests(args.duration)
        elif args.scenario == 'demo':
            generator.run_demo_scenario()
    except KeyboardInterrupt:
        print("\nStopping load generator...")
        generator.stop()

if __name__ == '__main__':
    main()