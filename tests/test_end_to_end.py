"""Smoke test that runs all three HTTP services and uses the public Gateway API."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]


def unused_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return int(listener.getsockname()[1])


def wait_for(url: str, process: subprocess.Popen[bytes], log_path: Path) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            log = log_path.read_text(encoding="utf-8", errors="replace")
            raise RuntimeError(f"Serviço terminou antes de iniciar:\n{log}")
        try:
            response = httpx.get(url, timeout=0.5)
            if response.is_success:
                return
        except httpx.HTTPError:
            pass
        time.sleep(0.2)
    log = log_path.read_text(encoding="utf-8", errors="replace")
    raise RuntimeError(f"Tempo esgotado aguardando {url}:\n{log}")


@pytest.fixture(scope="module")
def running_stack() -> Iterator[dict[str, str]]:
    gateway_port, tasks_port, categories_port = (unused_port() for _ in range(3))
    temp_dir = Path(tempfile.mkdtemp(prefix="rest-gateway-e2e-"))
    environment = os.environ.copy()
    environment.pop("AUTH_DATABASE_PATH", None)
    environment.pop("DEMO_ACCOUNT_ENABLED", None)
    environment.update(
        {
            "DJANGO_DB_NAME": str(temp_dir / "tasks.sqlite3"),
            "AUTH_DATABASE_PATH": str(temp_dir / "accounts.sqlite3"),
            "DJANGO_SECRET_KEY": "test-only-django-secret",
            "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost",
            "JWT_SECRET": "test-only-jwt-secret-at-least-32-characters",
            "DEMO_USERNAME": "aluno",
            "DEMO_PASSWORD": "projeto123",
            "TASKS_API_URL": f"http://127.0.0.1:{tasks_port}",
            "CATEGORIES_API_URL": f"http://127.0.0.1:{categories_port}",
            "CORS_ORIGINS": "http://127.0.0.1:5500",
        }
    )

    task_dir = ROOT / "services" / "tasks"
    python = sys.executable
    migration = subprocess.run(
        [python, "manage.py", "migrate", "--noinput"],
        cwd=task_dir,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    if migration.returncode:
        raise RuntimeError(f"Migrações da API de tarefas falharam:\n{migration.stderr}")

    commands = [
        (
            "tasks",
            [python, "manage.py", "runserver", f"127.0.0.1:{tasks_port}", "--noreload"],
            task_dir,
            f"http://127.0.0.1:{tasks_port}/health",
        ),
        (
            "categories",
            [
                python,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                str(ROOT / "services" / "categories"),
                "--host",
                "127.0.0.1",
                "--port",
                str(categories_port),
            ],
            ROOT,
            f"http://127.0.0.1:{categories_port}/health",
        ),
        (
            "gateway",
            [
                python,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                str(ROOT / "gateway"),
                "--host",
                "127.0.0.1",
                "--port",
                str(gateway_port),
            ],
            ROOT,
            f"http://127.0.0.1:{gateway_port}/health",
        ),
    ]

    processes: list[subprocess.Popen[bytes]] = []
    logs: list[object] = []
    try:
        for name, command, cwd, health_url in commands:
            log_handle = (temp_dir / f"{name}.log").open("wb")
            logs.append(log_handle)
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=environment,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
            )
            processes.append(process)
            wait_for(health_url, process, temp_dir / f"{name}.log")

        yield {
            "base_url": f"http://127.0.0.1:{gateway_port}",
            "log_dir": str(temp_dir),
        }
    finally:
        for process in reversed(processes):
            process.terminate()
        for process in reversed(processes):
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for log_handle in logs:
            log_handle.close()


def test_gateway_to_real_microservices_flow(running_stack: dict[str, str]) -> None:
    base_url = running_stack["base_url"]

    unauthorized = httpx.get(f"{base_url}/api/tasks", timeout=3)
    assert unauthorized.status_code == 401

    registration = httpx.post(
        f"{base_url}/auth/register",
        json={"username": "e2e-student", "email": "e2e@example.com", "password": "Safe-password-42"},
        timeout=3,
    )
    assert registration.status_code == 201, registration.text
    token = registration.json()["access_token"]

    token_response = httpx.post(
        f"{base_url}/auth/token",
        json={"username": "e2e-student", "password": "Safe-password-42"},
        timeout=3,
    )
    assert token_response.status_code == 200, token_response.text
    token = token_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    category_response = httpx.get(f"{base_url}/api/categories", headers=headers, timeout=3)
    assert category_response.status_code == 200, category_response.text
    categories = category_response.json()["data"]
    assert {"id": "estudo", "name": "Estudo"} in [
        {"id": category["id"], "name": category["name"]} for category in categories
    ]
    assert category_response.json()["_links"]["tasks"]["href"] == "/api/tasks"

    profile_response = httpx.get(
        f"{base_url}/auth/me",
        headers=headers,
        timeout=3,
    )
    assert profile_response.status_code == 200, profile_response.text
    assert profile_response.json()["user"]["username"] == "e2e-student"

    created = httpx.post(
        f"{base_url}/api/tasks",
        headers=headers,
        json={"title": "Fluxo ponta a ponta", "category_id": "estudo"},
        timeout=3,
    )
    assert created.status_code == 201, created.text
    created_body = created.json()
    assert created_body["data"]["title"] == "Fluxo ponta a ponta"
    assert created_body["data"]["category_id"] == "estudo"
    assert created_body["data"]["completed"] is False
    assert created_body["data"]["_links"]["completion"]["method"] == "PATCH"
    detail_link = created_body["_links"]["self"]["href"]

    completed = httpx.patch(
        f"{base_url}{created_body['data']['_links']['completion']['href']}",
        headers=headers,
        json={"completed": True},
        timeout=3,
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["data"]["completed"] is True

    detail = httpx.get(f"{base_url}{detail_link}", headers=headers, timeout=3)
    assert detail.status_code == 200, detail.text
    assert detail.json()["data"]["id"] == created_body["data"]["id"]
    assert detail.json()["data"]["completed"] is True

    listing = httpx.get(f"{base_url}/api/tasks", headers=headers, timeout=3)
    assert listing.status_code == 200, listing.text
    assert any(task["id"] == created_body["data"]["id"] for task in listing.json()["data"])

    other_registration = httpx.post(
        f"{base_url}/auth/register",
        json={"username": "second-student", "email": "second@example.com", "password": "Another-password-52"},
        timeout=3,
    )
    assert other_registration.status_code == 201, other_registration.text
    other_headers = {
        "Authorization": f"Bearer {other_registration.json()['access_token']}"
    }
    other_listing = httpx.get(f"{base_url}/api/tasks", headers=other_headers, timeout=3)
    assert other_listing.status_code == 200, other_listing.text
    assert other_listing.json()["data"] == []

    invalid_category = httpx.post(
        f"{base_url}/api/tasks",
        headers=headers,
        json={"title": "Categoria inválida", "category_id": "nao-existe"},
        timeout=3,
    )
    assert invalid_category.status_code == 400, invalid_category.text
