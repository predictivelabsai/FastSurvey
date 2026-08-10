from __future__ import annotations

import csv
import importlib
import io
import json
import sys

from starlette.testclient import TestClient


def build_client(tmp_path, monkeypatch):
    monkeypatch.setenv("FASTSURVEY_DB", str(tmp_path / "fastsurvey.sqlite"))
    monkeypatch.setenv("FASTSURVEY_SECRET", "test-session-secret")
    # Keep tests deterministic even when a developer has a real key in .env.
    monkeypatch.setenv("XAI_API_KEY", "")
    for module in ("web_app", "ui", "ai", "auth", "db"):
        sys.modules.pop(module, None)
    app_module = importlib.import_module("web_app")
    return TestClient(app_module.app), app_module


def register(client):
    response = client.post(
        "/register",
        data={"name": "Research Admin", "email": "admin@example.com", "password": "correct horse battery staple"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def create_survey(client):
    response = client.post(
        "/surveys/design",
        data={"message": "Understand why mid-market customers churn after trying feature X, and add pricing trade-offs."},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return int(response.headers["location"].split("/")[2])


def test_public_landing_and_operations(tmp_path, monkeypatch):
    client, _ = build_client(tmp_path, monkeypatch)
    landing = client.get("/")
    assert landing.status_code == 200
    assert "Ask better questions" in landing.text
    assert 'href="/login"' in landing.text
    assert "FastSME" in landing.text
    assert 'src="/static/product-demo.gif"' in landing.text
    assert "Integration partners" in landing.text
    demo = client.get("/static/product-demo.gif")
    assert demo.status_code == 200
    assert demo.headers["content-type"] == "image/gif"
    assert client.get("/healthz").json() == {"status": "ok", "service": "FastSurvey", "ai": "local-demo"}
    assert client.get("/robots.txt").status_code == 200


def test_auth_and_designer_revision(tmp_path, monkeypatch):
    client, app_module = build_client(tmp_path, monkeypatch)
    register(client)
    survey_id = create_survey(client)
    page = client.get(f"/surveys/{survey_id}/design")
    assert page.status_code == 200
    assert "Conversation path" in page.text
    assert "pricing factors" in page.text

    revision = client.post(
        f"/surveys/{survey_id}/design/message",
        data={"message": "Make it shorter and probe harder on emotion."},
    )
    assert revision.status_code == 200
    survey = app_module.db.get_survey(survey_id)
    assert survey["guide"]["estimated_minutes"] <= 4
    assert "felt" in survey["guide"]["probing_strategy"]["vague_answers"]


def test_complete_interview_extract_and_export(tmp_path, monkeypatch):
    client, app_module = build_client(tmp_path, monkeypatch)
    register(client)
    survey_id = create_survey(client)
    client.post(f"/surveys/{survey_id}/status")
    survey = app_module.db.get_survey(survey_id)

    consent = client.get(f"/s/{survey['slug']}")
    assert consent.status_code == 200
    assert "I agree" in consent.text
    started = client.post(f"/s/{survey['slug']}/start", data={"website": ""}, follow_redirects=False)
    assert started.status_code == 303
    token = started.headers["location"].split("/")[-1]

    answers = [
        "I manage operations for a 200-person SaaS company and needed a reliable workflow.",
        "The setup broke when permissions were unclear, so our team went back to spreadsheets.",
        "Six out of ten because the core idea was useful but onboarding created too much uncertainty.",
        "Show permissions before activation and provide a guided test run for the whole team.",
        "One final detail: it would have restored trust before our renewal decision.",
    ]
    for answer in answers:
        response = client.post(f"/i/{token}/message", data={"message": answer})
        assert response.status_code == 200
        if "Response complete" in response.text:
            break

    conversation = app_module.db.get_conversation(token)
    assert conversation["status"] == "complete"
    assert app_module.db.answers_for_conversation(conversation["id"])

    json_export = client.get(f"/surveys/{survey_id}/export.json")
    assert json_export.status_code == 200
    payload = json_export.json()
    assert payload["responses"][0]["transcript"]
    assert payload["responses"][0]["answers"]

    csv_export = client.get(f"/surveys/{survey_id}/export.csv")
    records = list(csv.DictReader(io.StringIO(csv_export.text)))
    assert records
    assert records[0]["objective_key"].startswith("objective_")


def test_cross_account_survey_access_is_denied(tmp_path, monkeypatch):
    client, _ = build_client(tmp_path, monkeypatch)
    register(client)
    survey_id = create_survey(client)
    client.get("/logout")
    client.post("/register", data={"name": "Other", "email": "other@example.com", "password": "another secure password"})
    response = client.get(f"/surveys/{survey_id}")
    assert response.status_code == 404
