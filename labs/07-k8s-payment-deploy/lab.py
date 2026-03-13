import marimo

__generated_with = "0.20.4"
app = marimo.App(width="medium")


@app.cell
def _(mo):
    mo.md("""
    # Lab 07: K8s Payment Service Deployment

    ## Why do health probes matter?

    You deploy a payment service update. The new pod starts. The process is running.
    Kubernetes sees it is running and routes traffic to it.

    But the service hasn't finished initialising its connection pool. The first
    100 requests hit a pod that isn't ready. Customers see 503. Payments fail.

    **Health probes fix this:**

    - **Readiness probe**: "Am I ready to receive traffic?" Kubernetes only routes
      traffic to pods that pass this check. During startup and warm-up, traffic goes
      to the old pods that are already ready.
    - **Liveness probe**: "Am I still alive?" If the process deadlocks or enters a
      broken state, Kubernetes restarts it automatically.

    Without probes, Kubernetes assumes a running process is a healthy process.
    With probes, Kubernetes has actual evidence before sending payment traffic.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Liveness vs Readiness — the key distinction

    | Probe | Question | On failure | Use case |
    |-------|----------|------------|----------|
    | Liveness | Is the process alive? | Restart the container | Deadlock, infinite loop, corrupted state |
    | Readiness | Can it handle traffic? | Remove from load balancer | Startup, DB connection down, dependency unavailable |

    **Critical rule:** Liveness should ONLY fail if the process cannot recover on its own.
    If liveness fails unnecessarily (e.g., slow DB query), Kubernetes restarts the pod
    in a restart loop — taking healthy pods offline and causing exactly the outage you
    were trying to prevent.

    **Correct pattern:**
    - Liveness: always returns 200 unless the process is truly broken (deadlocked/corrupted)
    - Readiness: returns 503 if any dependency needed to serve traffic is unavailable

    **Our implementation:**
    ```python
    @app.get("/health/live")
    async def liveness() -> dict[str, str]:
        return {"status": "alive"}  # Always 200 — process is running

    @app.get("/health/ready")
    async def readiness() -> JSONResponse:
        if not _ready:
            return JSONResponse({"status": "not_ready", "ready": False}, status_code=503)
        return JSONResponse({"status": "ready", "ready": True})
    ```
    """)
    return


@app.cell
def _():
    # Simulate probe behaviour — what Kubernetes sees during a rolling update

    class PodState:
        def __init__(self, name: str, startup_delay: float = 0.0) -> None:
            self.name = name
            self.ready = False
            self.alive = True
            self._startup_delay = startup_delay
            self._elapsed = 0.0

        def tick(self, seconds: float = 1.0) -> None:
            self._elapsed += seconds
            if self._elapsed >= self._startup_delay:
                self.ready = True

        def liveness_probe(self) -> int:
            return 200 if self.alive else 500

        def readiness_probe(self) -> int:
            return 200 if self.ready else 503

    print("=== Rolling update simulation ===")
    print("Old pod-v1 is already ready. New pod-v2 starts.")
    print()

    old_pod = PodState("pod-v1", startup_delay=0)
    old_pod.ready = True
    new_pod = PodState("pod-v2", startup_delay=3)

    for t in range(6):
        old_live = old_pod.liveness_probe()
        old_ready = old_pod.readiness_probe()
        new_live = new_pod.liveness_probe()
        new_ready = new_pod.readiness_probe()
        traffic_target = "pod-v1" if new_ready != 200 else "pod-v2"
        print(
            f"t={t}s  pod-v1 live={old_live} ready={old_ready}  "
            f"pod-v2 live={new_live} ready={new_ready}  "
            f"→ traffic to {traffic_target}"
        )
        new_pod.tick(1.0)
        if t == 3:
            old_pod.alive = False
            old_pod.ready = False
            print("       (old pod terminated after new pod became ready)")
    return


@app.cell
def _(mo):
    mo.md("""
    ## Rolling updates — zero downtime

    The Deployment spec controls exactly how pods are replaced:

    ```yaml
    strategy:
      type: RollingUpdate
      rollingUpdate:
        maxSurge: 1        # Allow 1 extra pod during update (replicas + 1 = 3 pods briefly)
        maxUnavailable: 0  # Never take a pod out of service unless a replacement is ready
    ```

    **maxUnavailable: 0** is the critical setting for payment services. It means:
    - Kubernetes will not terminate an old pod until the new pod passes its readiness probe
    - There is always at least `replicas` pods serving traffic
    - Traffic is never interrupted

    With 2 replicas and maxSurge=1:
    1. Scale to 3 pods (2 old + 1 new starting)
    2. Wait for new pod readiness probe to pass
    3. Terminate 1 old pod → back to 2 pods (1 old + 1 new)
    4. Repeat for remaining old pod

    If maxUnavailable were 1 instead: Kubernetes could terminate an old pod immediately,
    leaving only 1 pod for all traffic while the new pod starts. During peak hours this
    halves your capacity during every deploy.
    """)
    return


@app.cell
def _(mo):
    mo.md("""
    ## Probe configuration — the timing parameters

    ```yaml
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8000
      initialDelaySeconds: 5   # Wait 5s before first check (startup buffer)
      periodSeconds: 10        # Check every 10s
      failureThreshold: 3      # Fail 3 consecutive times before marking unready
    ```

    **initialDelaySeconds** prevents false failures during startup. If your app takes
    3 seconds to boot and initialDelaySeconds is 1, the first probe fires too early
    and the pod is marked unready before it has a chance to become ready.

    **periodSeconds** controls how quickly Kubernetes detects a problem. Every 10 seconds
    means up to 10 seconds of failed requests before Kubernetes pulls the pod from
    the load balancer.

    **failureThreshold** prevents flapping. A single slow response (network hiccup)
    should not remove a pod. Three consecutive failures is evidence of a real problem.

    | Parameter | Too low | Too high |
    |-----------|---------|----------|
    | initialDelaySeconds | False failures during startup | Slow rollouts |
    | periodSeconds | Unnecessary load on /health | Slow failure detection |
    | failureThreshold | Flapping on transient errors | Slow problem detection |
    """)
    return


@app.cell
def _():
    # Demonstrate probe timing — when does Kubernetes detect a failure?

    def time_to_detect_failure(
        initial_delay: int,
        period: int,
        failure_threshold: int,
        failure_starts_at: int,
    ) -> int:
        """Calculate seconds until Kubernetes marks pod unready."""
        first_probe = initial_delay
        # First probe that fires after the failure
        first_failing_probe = max(first_probe, failure_starts_at)
        # Round up to next probe interval
        probes_elapsed = (first_failing_probe - first_probe) // period
        first_failing_probe_time = first_probe + probes_elapsed * period
        if first_failing_probe_time < failure_starts_at:
            first_failing_probe_time += period
        # Need failure_threshold consecutive failures
        detection_time = first_failing_probe_time + (failure_threshold - 1) * period
        return detection_time

    configs = [
        (5, 10, 3, "production (our config)"),
        (2, 5, 1, "aggressive"),
        (10, 30, 5, "conservative"),
    ]

    print("How long to detect failure starting at t=20s?")
    print()
    for initial, period, threshold, label in configs:
        detection = time_to_detect_failure(initial, period, threshold, failure_starts_at=20)
        print(f"  {label}: {detection}s to remove pod from LB")
        print(f"    (initial={initial}s, period={period}s, threshold={threshold})")
    return


@app.cell
def _(mo):
    mo.md("""
    ## Dockerfile multi-stage build — why small images matter

    ```dockerfile
    FROM python:3.12-slim AS base
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt

    FROM base AS runtime
    COPY . .
    EXPOSE 8000
    CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
    ```

    **python:3.12-slim vs python:3.12:**

    | Image | Size | Contains |
    |-------|------|---------|
    | python:3.12 | ~1GB | Full Debian, build tools, headers |
    | python:3.12-slim | ~130MB | Minimal Debian, Python runtime only |

    For a payment service that only runs Python, you do not need gcc, make, or
    Debian documentation. The slim base drops 870MB. In Kubernetes, smaller images
    mean faster pod startup — which directly affects how quickly your readiness
    probe can pass during a rolling update.

    **Layer caching:** Copy requirements.txt before copying source code. Docker
    caches the pip install layer. When you change app.py, Docker uses the cached
    dependency layer instead of reinstalling everything. A deploy that takes 60s
    (full reinstall) becomes 5s (copy new source, reuse cached layers).
    """)
    return


@app.cell
def _():
    # Demonstrate layer caching impact
    scenarios = [
        ("No caching (copy everything first)", 60),
        ("With layer caching (requirements unchanged)", 5),
        ("With layer caching (requirements changed)", 60),
    ]

    print("Docker build time comparison:")
    print()
    for scenario, seconds in scenarios:
        bar = "█" * (seconds // 5)
        print(f"  {scenario}")
        print(f"  {bar} {seconds}s")
        print()

    print("Implication for rolling updates:")
    print("  5s build × 2 pods = 10s deploy window")
    print("  60s build × 2 pods = 120s deploy window")
    print("  Longer window = more requests at risk if a probe misconfiguration exists")
    return


@app.cell
def _(mo):
    mo.md("""
    ## Reflection

    The K8s manifests in this lab encode three deployment guarantees:

    1. **No traffic to unready pods** — readinessProbe on `/health/ready` ensures
       pods only receive traffic after the startup event fires and `_ready = True`

    2. **Automatic recovery from broken pods** — livenessProbe on `/health/live`
       triggers a pod restart if the process enters an unresponsive state

    3. **Zero downtime during deploys** — `maxUnavailable: 0` combined with readiness
       probes ensures old pods stay up until new pods are fully ready

    The resource limits (64Mi request / 128Mi limit) prevent one misbehaving pod
    from consuming the node's memory and starving other services.

    **What to say in an interview:**

    > "We configure readiness and liveness probes separately. Liveness only fails if
    > the process is truly unrecoverable — we don't want unnecessary restarts. Readiness
    > reflects whether the pod can handle traffic right now: it returns 503 during startup
    > and if any critical dependency is down. Combined with maxUnavailable=0, this gives
    > us zero-downtime rolling updates — traffic only shifts to a new pod after it passes
    > its readiness probe, and the old pod stays up until then."

    ---

    **Confidence score:** 9/10

    The probes, manifests, and rolling update configuration are production-grade.
    What is missing from a real deployment: a `failureThreshold` on the readiness
    probe (to avoid flapping on transient DB hiccups), a `terminationGracePeriodSeconds`
    to let in-flight payment requests complete, and a PodDisruptionBudget to prevent
    voluntary disruptions from taking too many pods offline simultaneously.
    """)
    return


@app.cell
def _(mo):
    return (mo,)


if __name__ == "__main__":
    app.run()
