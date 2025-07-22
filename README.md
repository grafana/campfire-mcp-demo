# Grafana MCP Server Demo

This project demonstrates how to create a comprehensive observability stack with a metrics-generating application, Prometheus, and Grafana, specifically designed to showcase the capabilities of the **Grafana MCP Server**.

## Demo flow

Set up the app:

```bash
docker-compose up
```

Then run

```bash
make demo
```

to create some demo metrics including errors.

Ask cursor the following questions:

- Can you create a dashbard in my Grafana instance including the http requests rate of the app?
GIve a moniroting title to the dashboard.

- Can you now add some latency metrics and then add them to the dashboard as well?

## 🎯 Overview

The demo consists of:
- **Metrics Application**: A Python Flask app that generates various types of metrics (counters, gauges, histograms, summaries)
- **Prometheus**: Scrapes and stores metrics from the application
- **Grafana**: Visualizes metrics with pre-configured dashboards

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Metrics App    │    │   Prometheus    │    │    Grafana      │
│  (Port 8000)    │───▶│  (Port 9090)    │───▶│  (Port 3000)    │
│                 │    │                 │    │                 │
│ • HTTP metrics  │    │ • Scraping      │    │ • Dashboards    │
│ • System stats  │    │ • Storage       │    │ • Alerting      │
│ • Custom gauges │    │ • PromQL        │    │ • MCP Server    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Docker and Docker Compose
- Git

### 1. Clone and Setup

```bash
git clone <repository-url>
cd campfire

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start the Infrastructure

```bash
# Start Prometheus and Grafana
docker-compose up -d

# Check services are running
docker-compose ps
```

### 3. Start the Metrics Application

```bash
# Start the Flask application
python app.py
```

The application will be available at:
- **Metrics App**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

### 4. Generate Traffic

```bash
# Generate sample traffic to create interesting metrics
python scripts/generate_load.py --scenario demo
```

## 📊 Available Metrics

The application generates the following metrics:

### HTTP Metrics
- `http_requests_total`: Counter of HTTP requests by method, endpoint, and status
- `http_request_duration_seconds`: Histogram of request durations
- `http_response_size_bytes`: Summary of response sizes

### System Metrics
- `system_cpu_usage_percent`: Current CPU usage
- `system_memory_usage_bytes`: Current memory usage

### Application Metrics
- `active_users_count`: Simulated active user count
- `database_connections_active`: Simulated database connections
- `application_errors_total`: Counter of application errors by type and severity
- `application_info`: Info metric with application metadata

## 🎛️ Application Endpoints

| Endpoint | Description | Behavior |
|----------|-------------|----------|
| `/` | Home page | Normal response time (0.1-2s) |
| `/api/users` | User API | Fast response, 5% error rate |
| `/api/load` | Heavy processing | Slow response (1-5s) |
| `/health` | Health check | Fast, always successful |
| `/metrics` | Prometheus metrics | Exposes all metrics |

## 📈 Grafana Dashboard

The project includes a pre-configured dashboard "Metrics Demo Dashboard" with panels showing:

1. **HTTP Request Rate**: Real-time request rates by endpoint
2. **CPU Usage**: System CPU utilization gauge
3. **Response Time Percentiles**: 50th and 95th percentile response times
4. **Active Users**: Current active user count
5. **Memory Usage**: System memory consumption
6. **Error Rate**: Application error rates by type

## Demo Scenarios

### Scenario 1: Performance Analysis
1. Start with normal load generation
2. Query request rates and response times
3. Analyze system resource usage
4. Identify performance bottlenecks

### Scenario 2: Traffic Spike Investigation
1. Generate traffic spike using load script
2. Monitor real-time metrics through MCP
3. Correlate different metric types
4. Show system behavior under load

### Scenario 3: Error Pattern Detection
1. Generate error patterns
2. Query error rates by type and severity
3. Investigate affected endpoints
4. Demonstrate troubleshooting workflow

### Scenario 4: Dashboard Management
1. Search and retrieve dashboards
2. Analyze panel configurations
3. Extract and modify queries
4. Create custom visualizations

## Utility Scripts

### Load Generator
```bash
# Normal load (default)
python scripts/generate_load.py --scenario normal --duration 300 --rps 3

# Traffic spike
python scripts/generate_load.py --scenario spike --duration 60 --rps 15

# Error generation
python scripts/generate_load.py --scenario errors --duration 180

# Slow requests
python scripts/generate_load.py --scenario slow --duration 120

# Complete demo scenario
python scripts/generate_load.py --scenario demo
```

### Reset Everything
```bash
# Stop all services
docker-compose down -v

# Remove volumes and restart
docker-compose up -d

# Restart the application
python app.py
```
