import time

from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response


app = FastAPI(
    title="OpsMind API",
    description="Production Incident & Recovery Platform",
    version="0.1.0",
)

REQUEST_COUNT = Counter(
    "opsmind_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "opsmind_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"],
)

fault_mode = {
    "latency": False,
    "error": False,
}


@app.middleware("http")
async def metrics_middleware(request, call_next):

    start = time.time()

    try:
        response = await call_next(request)
        status = response.status_code
        return response

    finally:
        duration = time.time() - start

        REQUEST_LATENCY.labels(
            request.method,
            request.url.path,
        ).observe(duration)

        REQUEST_COUNT.labels(
            request.method,
            request.url.path,
            str(status),
        ).inc()


@app.get("/")
def root():

    return {
        "application": "OpsMind",
        "service": "api",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


@app.get("/ready")
def readiness():

    return {
        "status": "ready"
    }


@app.get("/metrics")
def metrics():

    return Response(
        generate_latest(),
        media_type="text/plain",
    )


@app.get("/api/incidents")
def incidents():

    return {
        "active_incidents": []
    }


@app.post("/api/faults/latency")
def enable_latency():

    fault_mode["latency"] = True

    return {
        "fault": "latency",
        "enabled": True
    }


@app.post("/api/faults/500")
def enable_error():

    fault_mode["error"] = True

    return {
        "fault": "http_500",
        "enabled": True
    }


@app.post("/api/faults/reset")
def reset_faults():

    fault_mode["latency"] = False
    fault_mode["error"] = False

    return {
        "faults": "reset"
    }


@app.get("/api/test")
def test_endpoint():

    if fault_mode["latency"]:
        time.sleep(3)

    if fault_mode["error"]:
        raise HTTPException(
            status_code=500,
            detail="Injected production failure",
        )

    return {
        "message": "Everything is working"
    }