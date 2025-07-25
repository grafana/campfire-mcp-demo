# Campfire MCP Demo

An example application that generates metrics, logs, and traces based on different scenarios to accelerate testing in observability systems. Complete observability stack with Flask, Prometheus, Loki, Tempo, and Grafana.


## About This Demo

This application provides a complete observability stack (metrics, logs, and traces) for experimenting with the [Grafana MCP Server](https://github.com/grafana/mcp-grafana) from LLM clients like Claude, Cursor, and others. It generates realistic data patterns that let you query Prometheus and Loki datasources using natural language through the MCP interface, without needing to write PromQL/LogQL manually. See MCP repo for more.


## Quick Start

```bash
# 1. Setup dependencies
make setup

# 2. Start the stack
make docker-up

# 3. Generate demo traffic
make demo
```

**Access points:**
- **Metrics App**: http://localhost:8000
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **Tempo**: http://localhost:3200/api/search (tracing)

## Testing Scenarios

The app generates realistic patterns for testing observability tools:

- **Normal traffic** - Steady baseline metrics
- **Traffic spikes** - Load testing scenarios
- **Error patterns** - Simulate failures and debugging
- **Slow requests** - Performance analysis scenarios

## Architecture

```
                    ┌─→ Prometheus ──┐
Flask App ──────────┤  (Port 9090)   ├─→ Grafana (Port 3000)
(Port 8000)         ├─→ Loki ────────┤
                    └─→ Tempo ───────┘
                       (Port 3200)
```

## Available Data

### Metrics (Prometheus)
- `http_requests_total` - Request counts by endpoint/status
- `http_request_duration_seconds` - Request latency histogram (percentiles, averages)
- `active_users_count` - Simulated active users (50-200 range)

### Traces (Tempo)
- **Distributed traces** - Full request flows with timing
- **Custom spans** - Database operations, processing steps
- **Error tracking** - Failed operations with context

### Logs (Loki)
- **Structured JSON logs** - Request/response logging
- **Error tracking** - Detailed error information
- **Performance monitoring** - Slow request detection

### Example PromQL Queries

```promql
# Request rate by endpoint
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Average response time
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

## Endpoints

| Endpoint | Behavior |
|----------|----------|
| `/` | Normal response |
| `/api/users` | Fast, 5% error rate |
| `/api/load` | Slow processing (1-5s) |
| `/health` | Health check |
| `/metrics` | Prometheus metrics |

## Commands

```bash
# Setup
make setup              # Install dependencies
make docker-up          # Start services
make docker-down        # Stop services

# Testing
make test               # Run integration tests

# Load Generation
make demo               # Complete demo scenario
make load-normal        # Normal traffic (300s)
make load-spike         # Traffic spike (60s)
make load-errors        # Error patterns (180s)

# Code Quality
make lint-check         # Check code style
make lint-fix           # Fix linting issues
```

## Requirements

- Python 3.11+
- Docker & Docker Compose
- [uv](https://docs.astral.sh/uv/) package manager


## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

