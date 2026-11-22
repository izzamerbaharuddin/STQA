"""
PyTodo Pro - Week 5 performance test (Locust).

Workload (see Week 5 report, Section 5):
    - Up to 20 concurrent simulated users, spawn rate 2/sec
    - Each simulated user registers its own account and seeds 5-10 tasks
      on start, then repeatedly hits the busiest read/write endpoints with
      1-3 seconds of think time between requests.

Run:
    pip install locust
    python app.py                                  # in one terminal, local test instance
    locust -f locustfile.py --host http://127.0.0.1:5000   # in another

Then open http://localhost:8089, set Users=20, Spawn rate=2, and run for
at least 3 minutes to capture the steady-state numbers asked for in the
Week 5 report (avg/median/p95 response time, requests/sec, error rate).

This targets only the group's own local instance; it is not run against
any shared or third-party system.
"""

import random
import uuid

from locust import HttpUser, task, between


CATEGORIES = ["Work", "Personal", "Study", "Urgent", None]


class PyTodoProUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Each simulated user registers its own account and seeds some
        tasks, so list/dashboard queries run against realistic row counts
        instead of an empty table."""
        self.username = f"perf_{uuid.uuid4().hex[:10]}"
        self.password = "Perf12345"
        resp = self.client.post(
            "/api/register",
            json={"username": self.username, "password": self.password},
            name="/api/register",
        )
        if resp.status_code != 201:
            # Fall back to logging in, in case of an unlikely username clash.
            self.client.post(
                "/api/login",
                json={"username": self.username, "password": self.password},
                name="/api/login",
            )

        self.task_ids = []
        for i in range(random.randint(5, 10)):
            create = self.client.post(
                "/api/tasks",
                json={
                    "title": f"Seed task {i}",
                    "category_id": None,
                    "due_date": None,
                },
                name="/api/tasks [seed]",
            )
            if create.status_code == 201:
                self.task_ids.append(create.json()["id"])

    @task(4)
    def view_task_list_web(self):
        """GET / - the heaviest page: joins category name per row."""
        self.client.get("/", name="/ (task list)")

    @task(4)
    def view_task_list_api(self):
        """GET /api/tasks - JSON equivalent, exercised with filters."""
        params = random.choice(
            [
                {},
                {"status": "open"},
                {"status": "done"},
                {"category": random.choice(["Work", "Study"])},
            ]
        )
        self.client.get("/api/tasks", params=params, name="/api/tasks")

    @task(2)
    def view_dashboard(self):
        """GET /api/dashboard - aggregates over all of the user's tasks."""
        self.client.get("/api/dashboard", name="/api/dashboard")

    @task(1)
    def create_task(self):
        """POST /api/tasks - the write path."""
        resp = self.client.post(
            "/api/tasks",
            json={"title": f"Load-test task {uuid.uuid4().hex[:6]}"},
            name="/api/tasks [create]",
        )
        if resp.status_code == 201:
            self.task_ids.append(resp.json()["id"])
