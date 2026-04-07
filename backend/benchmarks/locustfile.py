"""Load test for the labeling workflow.

Simulates all labelers of a project labeling images concurrently.
Each Locust user picks a labeler from the project and loops:
  1. POST /assignments  (get next pending image)
  2. POST /images/{id}/label  (submit random label)

Usage:
    # Headless (CLI) — auto-detects labeler count:
    make benchmark PROJECT_ID=<uuid> [BENCHMARK_DURATION=60s]

    # With web UI:
    make benchmark-ui PROJECT_ID=<uuid>

Environment variables:
    PROJECT_ID       (required)  UUID of the project to benchmark.
"""

import itertools
import logging
import os
import random
import sys

import requests
from locust import HttpUser, between, events, task

logger = logging.getLogger(__name__)

PROJECT_ID: str = os.environ.get("PROJECT_ID", "")
if not PROJECT_ID:
    sys.exit("ERROR: PROJECT_ID environment variable is required")

# Shared state populated once at test start
_project_labels: list[str] = []
_labeler_cycle: itertools.cycle | None = None


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Fetch project details once before spawning users."""
    global _project_labels, _labeler_cycle

    host = environment.host or "http://localhost:8000"

    resp = requests.get(f"{host}/v1/projects/{PROJECT_ID}")
    if resp.status_code != 200:
        sys.exit(f"ERROR: Could not fetch project {PROJECT_ID}: {resp.status_code} {resp.text}")

    project = resp.json()
    _project_labels = list(project["labels"])
    labelers = project.get("labelers", [])

    if not labelers:
        sys.exit(f"ERROR: Project {PROJECT_ID} has no labelers assigned")
    if not _project_labels:
        sys.exit(f"ERROR: Project {PROJECT_ID} has no labels defined")

    _labeler_cycle = itertools.cycle(labelers)
    logger.info(
        "Benchmark ready: project=%s labels=%s labelers=%d",
        PROJECT_ID,
        _project_labels,
        len(labelers),
    )


class LabelerUser(HttpUser):
    """Simulates a labeler requesting assignments and submitting labels."""

    wait_time = between(0.1, 0.5)

    def on_start(self):
        labeler = next(_labeler_cycle)
        self.labeler_id = labeler["id"]
        self.labeler_username = labeler["username"]
        logger.info("Labeler started: %s (%s)", self.labeler_username, self.labeler_id)

    @task
    def label_image(self):
        # 1. Request assignment
        with self.client.post(
            f"/v1/projects/{PROJECT_ID}/assignments",
            json={"labeler_id": self.labeler_id},
            catch_response=True,
        ) as resp:
            if resp.status_code == 204:
                resp.success()
                logger.info("No more pending images for %s", self.labeler_username)
                self.environment.runner.quit()
                return
            if resp.status_code != 201:
                resp.failure(f"Assignment failed: {resp.status_code}")
                return
            assignment = resp.json()

        image_id = assignment["id"]
        assignment_id = assignment["assignment_id"]

        # 2. Submit random label
        label = random.choice(_project_labels)
        with self.client.post(
            f"/v1/projects/{PROJECT_ID}/images/{image_id}/label",
            json={
                "labeler_id": self.labeler_id,
                "assignment_id": assignment_id,
                "label": label,
            },
            catch_response=True,
        ) as resp:
            if resp.status_code != 201:
                resp.failure(f"Label failed: {resp.status_code}")
            else:
                resp.success()
