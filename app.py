#!/usr/bin/env python3
"""
Simplified Metrics Demo App
Generates basic HTTP request and active user metrics with comprehensive logging
"""

import json
import logging
import random
import sys
import threading
import time
import os

from flask import Flask, g, request
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource

# Store application start time at module level
app_start_time = time.time()


# Configure structured logging
class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logs"""

    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add extra fields if present - check for the attribute safely
        extra_fields = getattr(record, "extra_fields", None)
        if extra_fields:
            log_entry.update(extra_fields)

        return json.dumps(log_entry)


# Set up logging
def setup_logging():
    """Configure application logging"""
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Console handler with structured format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    formatter = StructuredFormatter()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Suppress Flask's default request logging to avoid duplicates
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    return logging.getLogger(__name__)


# Initialize logging
logger = setup_logging()

# Set up OpenTelemetry tracing
def setup_tracing():
    """Configure OpenTelemetry tracing"""
    # Set up the tracer provider with resource information
    resource = Resource.create({
        "service.name": "metrics-demo-app",
        "service.version": "1.0.0",
        "deployment.environment": "development"
    })

    trace.set_tracer_provider(TracerProvider(resource=resource))

    # Configure OTLP exporter to send traces to Tempo
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo:4317"),
        insecure=True
    )

    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

    logger.info(
        "OpenTelemetry tracing configured",
        extra={"extra_fields": {"component": "tracing", "action": "setup"}}
    )

# Initialize tracing
setup_tracing()

app = Flask(__name__)

# Development configuration for better live reload
app.config["ENV"] = "development"
app.config["DEBUG"] = True
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Instrument Flask and requests for automatic tracing
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()

# Get tracer for custom spans
tracer = trace.get_tracer(__name__)

# Create a custom registry
registry = CollectorRegistry()

# Define metrics - keeping only the essentials
request_count = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
    registry=registry,
)

request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "status"],
    registry=registry,
)

active_users = Gauge(
    "active_users_count", "Number of currently active users", registry=registry
)


class MetricsUpdater:
    """Background thread to update active users metric"""

    def __init__(self):
        self.running = True
        self.thread = threading.Thread(target=self._update_loop)
        self.thread.daemon = True
        self.logger = logging.getLogger(f"{__name__}.MetricsUpdater")

    def start(self):
        self.thread.start()
        self.logger.info(
            "Metrics updater started",
            extra={"extra_fields": {"component": "metrics_updater", "action": "start"}},
        )

    def stop(self):
        self.running = False
        self.logger.info(
            "Metrics updater stopped",
            extra={"extra_fields": {"component": "metrics_updater", "action": "stop"}},
        )

    def _update_loop(self):
        while self.running:
            try:
                # Simulate active users count
                user_count = random.randint(50, 200)
                active_users.set(user_count)

                # Log metrics update
                self.logger.debug(
                    "Active users metric updated",
                    extra={
                        "extra_fields": {
                            "component": "metrics_updater",
                            "metric": "active_users_count",
                            "value": user_count,
                        }
                    },
                )

                # Occasionally log warnings about high user count
                if user_count > 180:
                    self.logger.warning(
                        "High user count detected",
                        extra={
                            "extra_fields": {
                                "component": "metrics_updater",
                                "metric": "active_users_count",
                                "value": user_count,
                                "threshold": 180,
                            }
                        },
                    )

                time.sleep(5)  # Update every 5 seconds

            except Exception as e:
                self.logger.error(
                    "Error updating metrics",
                    extra={
                        "extra_fields": {
                            "component": "metrics_updater",
                            "error": str(e),
                            "error_type": type(e).__name__,
                        }
                    },
                )
                time.sleep(5)


# Request logging middleware
@app.before_request
def log_request_info():
    """Log incoming requests"""
    g.start_time = time.time()

    logger.info(
        "Incoming request",
        extra={
            "extra_fields": {
                "component": "request_handler",
                "method": request.method,
                "endpoint": request.endpoint or request.path,
                "path": request.path,
                "remote_addr": request.remote_addr,
                "user_agent": request.headers.get("User-Agent", "Unknown"),
                "request_id": f"req_{int(g.start_time * 1000000)}",
            }
        },
    )


@app.after_request
def log_response_info(response):
    """Log response information"""
    if hasattr(g, "start_time"):
        duration_seconds = time.time() - g.start_time
        duration_ms = duration_seconds * 1000  # Convert to milliseconds for logging

        # Record request duration in histogram
        request_duration.labels(
            method=request.method,
            endpoint=request.endpoint or request.path,
            status=str(response.status_code)
        ).observe(duration_seconds)

        log_level = logging.INFO
        if response.status_code >= 400:
            log_level = (
                logging.ERROR if response.status_code >= 500 else logging.WARNING
            )

        logger.log(
            log_level,
            "Request completed",
            extra={
                "extra_fields": {
                    "component": "request_handler",
                    "method": request.method,
                    "endpoint": request.endpoint or request.path,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                    "response_size_bytes": (
                        len(response.get_data()) if response.get_data() else 0
                    ),
                    "request_id": f"req_{int(g.start_time * 1000000)}",
                }
            },
        )

        # Log slow requests
        if duration_ms > 1000:  # More than 1 second
            logger.warning(
                "Slow request detected",
                extra={
                    "extra_fields": {
                        "component": "performance",
                        "endpoint": request.endpoint or request.path,
                        "duration_ms": round(duration_ms, 2),
                        "threshold_ms": 1000,
                    }
                },
            )

    return response


# Start metrics updater
metrics_updater = MetricsUpdater()
metrics_updater.start()


@app.route("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    logger.debug(
        "Metrics endpoint accessed",
        extra={"extra_fields": {"component": "metrics", "action": "scrape"}},
    )
    return generate_latest(registry), 200, {"Content-Type": CONTENT_TYPE_LATEST}


@app.route("/")
def home():
    """Home endpoint"""
    logger.info(
        "Home page accessed",
        extra={"extra_fields": {"component": "web", "page": "home"}},
    )

    # Simulate some processing time
    processing_time = random.uniform(0.1, 0.5)
    time.sleep(processing_time)

    # Record request
    request_count.labels(method="GET", endpoint="/", status="200").inc()

    logger.debug(
        "Home page processing completed",
        extra={
            "extra_fields": {
                "component": "web",
                "page": "home",
                "processing_time_ms": round(processing_time * 1000, 2),
            }
        },
    )

    return "Welcome to the Simplified Metrics Demo App!"


@app.route("/api/users")
def api_users():
    """API endpoint that occasionally generates errors"""
    with tracer.start_as_current_span("fetch_users") as span:
        logger.info(
            "Users API endpoint accessed",
            extra={"extra_fields": {"component": "api", "endpoint": "users"}},
        )

        # Add span attributes
        span.set_attribute("api.endpoint", "users")
        span.set_attribute("api.operation", "fetch_users")

        # Simulate database query
        with tracer.start_as_current_span("database.query") as db_span:
            db_span.set_attribute("db.operation", "SELECT")
            db_span.set_attribute("db.table", "users")

            # Simulate processing time
            processing_time = random.uniform(0.05, 0.3)
            time.sleep(processing_time)

            # Simulate occasional errors (5% chance)
            if random.random() < 0.05:
                error_msg = "Database connection timeout"
                db_span.set_attribute("error", True)
                db_span.set_attribute("error.message", error_msg)
                span.set_attribute("error", True)

                logger.error(
                    "API error occurred",
                    extra={
                        "extra_fields": {
                            "component": "api",
                            "endpoint": "users",
                            "error": error_msg,
                            "error_type": "database_timeout",
                            "processing_time_ms": round(processing_time * 1000, 2),
                        }
                    },
                )
                request_count.labels(method="GET", endpoint="/api/users", status="500").inc()
                return "Internal Server Error", 500

        # Record successful request
        request_count.labels(method="GET", endpoint="/api/users", status="200").inc()

        users = ["alice", "bob", "charlie"]
        span.set_attribute("users.count", len(users))

        logger.info(
            "Users API request successful",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "users",
                    "user_count": len(users),
                    "processing_time_ms": round(processing_time * 1000, 2),
                }
            },
        )

        return {"users": users, "count": len(users)}


@app.route("/api/load")
def simulate_load():
    """Endpoint to simulate heavier processing"""
    with tracer.start_as_current_span("heavy_processing") as span:
        logger.info(
            "Load simulation endpoint accessed",
            extra={"extra_fields": {"component": "api", "endpoint": "load"}},
        )

        # Simulate heavy processing
        processing_time = random.uniform(1.0, 3.0)

        # Add span attributes
        span.set_attribute("api.endpoint", "load")
        span.set_attribute("api.operation", "heavy_processing")
        span.set_attribute("processing.expected_duration_ms", round(processing_time * 1000, 2))

        logger.warning(
            "Starting heavy processing",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "load",
                    "expected_duration_ms": round(processing_time * 1000, 2),
                }
            },
        )

        # Simulate multiple processing steps
        with tracer.start_as_current_span("data_processing") as data_span:
            data_span.set_attribute("step", "data_transformation")
            time.sleep(processing_time * 0.6)

        with tracer.start_as_current_span("computation") as comp_span:
            comp_span.set_attribute("step", "heavy_computation")
            comp_span.set_attribute("complexity", "O(n²)")
            time.sleep(processing_time * 0.4)

        request_count.labels(method="GET", endpoint="/api/load", status="200").inc()

        actual_duration = round(processing_time * 1000, 2)
        span.set_attribute("processing.actual_duration_ms", actual_duration)

        logger.info(
            "Heavy processing completed",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "load",
                    "actual_duration_ms": actual_duration,
                    "status": "completed",
                }
            },
        )

        return {
            "message": "Heavy processing completed",
            "duration_ms": actual_duration,
        }


@app.route("/health")
def health():
    """Health check endpoint"""
    logger.debug(
        "Health check accessed",
        extra={"extra_fields": {"component": "health", "action": "check"}},
    )

    request_count.labels(method="GET", endpoint="/health", status="200").inc()

    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "active_users": (
            active_users._value._value if hasattr(active_users._value, "_value") else 0
        ),
        "uptime_seconds": time.time() - app_start_time,
    }

    logger.info(
        "Health check completed",
        extra={
            "extra_fields": {
                "component": "health",
                "status": health_status["status"],
                "active_users": health_status["active_users"],
            }
        },
    )

    return health_status


@app.route("/api/status/<int:code>")
def test_status_code(code):
    """Endpoint to test different HTTP status codes"""
    logger.info(
        "Status code test endpoint accessed",
        extra={
            "extra_fields": {
                "component": "api",
                "endpoint": "status_test",
                "requested_status_code": code,
            }
        },
    )

    # Simulate some processing time
    processing_time = random.uniform(0.05, 0.2)
    time.sleep(processing_time)

    # Record request with the actual status code
    request_count.labels(method="GET", endpoint="/api/status", status=str(code)).inc()

    # Generate appropriate response based on status code
    if code == 200:
        response_data = {"message": "OK", "status_code": code}
        logger.info(
            "Status test successful",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "processing_time_ms": round(processing_time * 1000, 2),
                }
            },
        )
        return response_data, 200

    elif code == 400:
        error_msg = "Bad Request - Invalid input provided"
        logger.warning(
            "Bad request simulated",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "error": error_msg,
                    "error_type": "bad_request",
                }
            },
        )
        return {"error": error_msg, "status_code": code}, 400

    elif code == 401:
        error_msg = "Unauthorized - Authentication required"
        logger.warning(
            "Unauthorized access simulated",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "error": error_msg,
                    "error_type": "unauthorized",
                }
            },
        )
        return {"error": error_msg, "status_code": code}, 401

    elif code == 403:
        error_msg = "Forbidden - Access denied"
        logger.warning(
            "Forbidden access simulated",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "error": error_msg,
                    "error_type": "forbidden",
                }
            },
        )
        return {"error": error_msg, "status_code": code}, 403

    elif code == 404:
        error_msg = "Not Found - Resource does not exist"
        logger.warning(
            "Not found simulated",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "error": error_msg,
                    "error_type": "not_found",
                }
            },
        )
        return {"error": error_msg, "status_code": code}, 404

    elif code == 429:
        error_msg = "Too Many Requests - Rate limit exceeded"
        logger.warning(
            "Rate limit simulated",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "error": error_msg,
                    "error_type": "rate_limit",
                }
            },
        )
        return {"error": error_msg, "status_code": code}, 429

    elif code == 500:
        error_msg = "Internal Server Error - Something went wrong"
        logger.error(
            "Internal server error simulated",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "error": error_msg,
                    "error_type": "internal_error",
                }
            },
        )
        return {"error": error_msg, "status_code": code}, 500

    elif code == 502:
        error_msg = "Bad Gateway - Upstream service unavailable"
        logger.error(
            "Bad gateway simulated",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "error": error_msg,
                    "error_type": "bad_gateway",
                }
            },
        )
        return {"error": error_msg, "status_code": code}, 502

    elif code == 503:
        error_msg = "Service Unavailable - Server is temporarily unavailable"
        logger.error(
            "Service unavailable simulated",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "error": error_msg,
                    "error_type": "service_unavailable",
                }
            },
        )
        return {"error": error_msg, "status_code": code}, 503

    else:
        # For any other code, return a generic response
        logger.info(
            f"Custom status code {code} simulated",
            extra={
                "extra_fields": {
                    "component": "api",
                    "endpoint": "status_test",
                    "status_code": code,
                    "message": "custom_status_code",
                }
            },
        )
        return {"message": f"Custom status code {code}", "status_code": code}, code


@app.route("/api/random-status")
def random_status():
    """Endpoint that returns random HTTP status codes for testing"""
    # Define possible status codes with weights (more common ones have higher weight)
    status_codes = [
        200,
        200,
        200,
        200,
        200,
        200,
        400,
        401,
        403,
        404,
        429,
        500,
        502,
        503,
    ]
    chosen_code = random.choice(status_codes)

    logger.info(
        "Random status endpoint accessed",
        extra={
            "extra_fields": {
                "component": "api",
                "endpoint": "random_status",
                "chosen_status_code": chosen_code,
            }
        },
    )

    # Redirect to the status code testing endpoint
    return test_status_code(chosen_code)


if __name__ == "__main__":
    logger.info(
        "Starting Simplified Metrics Demo Application",
        extra={
            "extra_fields": {
                "component": "application",
                "action": "startup",
                "version": "1.0.0",
                "port": 8000,
            }
        },
    )

    print("Starting Simplified Metrics Demo Application...")
    print("Metrics available at: http://localhost:8000/metrics")
    print("Application endpoints:")
    print("  - http://localhost:8000/")
    print("  - http://localhost:8000/api/users")
    print("  - http://localhost:8000/api/load")
    print("  - http://localhost:8000/health")
    print("  - http://localhost:8000/api/status/<code>  (test specific status codes)")
    print("  - http://localhost:8000/api/random-status  (random status codes)")
    print("\nExposing metrics:")
    print("  - http_requests_total (method, endpoint, status)")
    print("  - http_request_duration_seconds (method, endpoint, status)")
    print("  - active_users_count")
    print("\nGenerating structured JSON logs:")
    print("  - Request/response logging with status codes")
    print("  - Error tracking by status code")
    print("  - Performance monitoring")
    print("  - Component-specific logs")
    print("\nGenerating distributed traces:")
    print("  - OpenTelemetry traces sent to Tempo")
    print("  - Custom spans for database operations")
    print("  - Error tracking in traces")
    print("  - Processing step breakdown")
    print("\nExample status code queries:")
    print("  - http://localhost:8000/api/status/404")
    print("  - http://localhost:8000/api/status/500")
    print("  - http://localhost:8000/api/random-status")
    print("\n🔄 Live reload enabled - code changes will auto-restart the server")

    try:
        # Enhanced development server configuration
        app.run(
            host="0.0.0.0",
            port=8000,
            debug=True,
            use_reloader=True,
            use_debugger=True,
            threaded=True,
            extra_files=None,  # Flask will auto-detect Python files
        )
    except KeyboardInterrupt:
        logger.info(
            "Application shutdown requested",
            extra={
                "extra_fields": {
                    "component": "application",
                    "action": "shutdown",
                    "reason": "keyboard_interrupt",
                }
            },
        )
        metrics_updater.stop()
    except Exception as e:
        logger.error(
            "Application crashed",
            extra={
                "extra_fields": {
                    "component": "application",
                    "action": "crash",
                    "error": str(e),
                    "error_type": type(e).__name__,
                }
            },
        )
        raise
