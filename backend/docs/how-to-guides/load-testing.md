# Load Testing

Run realistic labeling simulations against a running uLabel instance using [Locust](https://locust.io/).
Given a project UUID, the load test spawns one concurrent user per labeler and loops through the assign-then-label cycle until time runs out or all images are labeled.

## Prerequisites

- The backend running (`make dev` or `docker compose up app`)
- A project with labelers assigned and pending images

## Quick start

```bash
make benchmark PROJECT_ID=<uuid>
```

This will:

1. Fetch the project details (labels and labelers) from the API
2. Spawn one Locust user per labeler
3. Each user loops: `POST /assignments` &rarr; `POST /label` (random label)
4. Run for 60 seconds and print a summary

## Configuration

| Variable | Default | Description |
|---|---|---|
| `PROJECT_ID` | *(required)* | UUID of the project to benchmark |
| `BENCHMARK_DURATION` | `60s` | How long the test runs |
| `BENCHMARK_USERS` | `0` (auto) | Number of concurrent users. `0` = one per labeler |
| `BENCHMARK_URL` | `http://localhost:8000` | API base URL |

### Examples

```bash
# Run for 2 minutes
make benchmark PROJECT_ID=<uuid> BENCHMARK_DURATION=120s

# Override user count (e.g. stress test with 50 users)
make benchmark PROJECT_ID=<uuid> BENCHMARK_USERS=50

# Point to a remote instance
make benchmark PROJECT_ID=<uuid> BENCHMARK_URL=https://api.example.com
```

## Web UI mode

Locust includes a web dashboard for real-time monitoring:

```bash
make benchmark-ui PROJECT_ID=<uuid>
```

Then open [http://localhost:8089](http://localhost:8089) to configure the number of users and spawn rate, and see live charts of request throughput, response times, and failure rates.

## How it works

The load test is implemented in `benchmarks/locustfile.py` with two components:

- **`on_test_start`** — Runs once before spawning users. Fetches `GET /v1/projects/{PROJECT_ID}` to discover the project's labels and labelers.
- **`LabelerUser`** — Each user simulates one labeler in a loop:
    1. `POST /v1/projects/{id}/assignments` to get the next pending image
    2. `POST /v1/projects/{id}/images/{image_id}/label` with a random label from the project
    3. If `204 No Content` (no more images), the test stops early

When `BENCHMARK_USERS=0` (default), the Makefile queries the project API to count labelers and passes the result as `--users` to Locust.

## Using results as a benchmark

The test output includes Locust's standard metrics: request count, failure rate, median/average/p95/p99 response times, and requests per second.

To use this as a **benchmark** (comparing performance across changes):

1. Run the test under consistent conditions (same dataset size, same hardware)
2. Note the RPS and p99 latency from the summary
3. Make your change (e.g. new index, pool size tweak, code optimization)
4. Re-run and compare

You can also export results to CSV for tracking over time by removing the `--only-summary` flag and adding `--csv=results` to the Locust command.
