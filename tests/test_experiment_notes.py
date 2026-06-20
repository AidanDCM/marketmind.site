"""Slice 38: POST/GET /experiment/{id}/notes endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from marketmind.api.app import app
from marketmind.db.engine import make_engine
from marketmind.db.models import Base


@pytest.fixture
def test_engine():
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    app.state.engine = engine
    yield engine
    app.state.engine = None


@pytest.fixture
def client(test_engine):
    with TestClient(app) as c:
        yield c


def _create_experiment(client, experiment_id: str = "exp_notes_001") -> None:
    client.post("/snapshots", json={
        "experiment_id": experiment_id,
        "product_name": "Test Product",
        "break_even_cac": 20.0,
        "snapshot_date": "2026-06-15",
        "orders": 3,
        "total_ad_spend": 60.0,
        "total_revenue": 180.0,
    })


def test_add_note_returns_note(client):
    _create_experiment(client)
    resp = client.post("/experiment/exp_notes_001/notes", json={"body": "paused FB ads today"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["body"] == "paused FB ads today"
    assert data["experiment_id"] == "exp_notes_001"
    assert "id" in data
    assert "created_at" in data


def test_get_notes_empty_before_add(client):
    _create_experiment(client)
    resp = client.get("/experiment/exp_notes_001/notes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_notes_returns_all_in_order(client):
    _create_experiment(client)
    client.post("/experiment/exp_notes_001/notes", json={"body": "first note"})
    client.post("/experiment/exp_notes_001/notes", json={"body": "second note"})
    client.post("/experiment/exp_notes_001/notes", json={"body": "third note"})

    resp = client.get("/experiment/exp_notes_001/notes")
    notes = resp.json()
    assert len(notes) == 3
    assert [n["body"] for n in notes] == ["first note", "second note", "third note"]


def test_add_note_404_for_unknown_experiment(client):
    resp = client.post("/experiment/nonexistent/notes", json={"body": "some note"})
    assert resp.status_code == 404


def test_add_note_422_for_empty_body(client):
    _create_experiment(client)
    resp = client.post("/experiment/exp_notes_001/notes", json={"body": "   "})
    assert resp.status_code == 422


def test_get_notes_returns_empty_for_unknown_experiment(client):
    resp = client.get("/experiment/nonexistent/notes")
    assert resp.status_code == 200
    assert resp.json() == []


def test_notes_isolated_between_experiments(client):
    _create_experiment(client, "exp_note_a")
    _create_experiment(client, "exp_note_b")
    client.post("/experiment/exp_note_a/notes", json={"body": "note for A"})
    client.post("/experiment/exp_note_b/notes", json={"body": "note for B"})

    notes_a = client.get("/experiment/exp_note_a/notes").json()
    notes_b = client.get("/experiment/exp_note_b/notes").json()
    assert len(notes_a) == 1 and notes_a[0]["body"] == "note for A"
    assert len(notes_b) == 1 and notes_b[0]["body"] == "note for B"
