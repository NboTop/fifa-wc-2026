"""
Test suite for WC 2026 Intelligence Platform backend.

Runs against the real app with real model loading (Hugging Face download +
sklearn/xgboost engines) — matching how the app actually behaves in
production rather than mocking the core inference path. Model files are
small enough (~70MB total) that this stays fast after the first run.

Run: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture(scope="module")
def client():
    # `with` triggers the lifespan (model download + engine load) exactly
    # once for the whole test module, same as a real server boot.
    with TestClient(app) as c:
        yield c


# ── Health ─────────────────────────────────────────────────────────────────

def test_health_reports_all_engines_loaded(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["engines"]["predictor"] is True
    assert data["engines"]["players"] is True


def test_health_accepts_head_for_uptime_monitors(client):
    # Regression test: UptimeRobot's default check is HEAD, not GET.
    # /health previously 405'd on HEAD until this was fixed.
    res = client.head("/health")
    assert res.status_code == 200


# ── Match Predictor ───────────────────────────────────────────────────────

def test_predict_returns_valid_probability_distribution(client):
    res = client.post("/api/v1/predict", json={"team_a": "Argentina", "team_b": "Spain"})
    assert res.status_code == 200
    data = res.json()

    for key in ("team_a", "team_b", "team_a_win", "draw", "team_b_win", "predicted", "confidence"):
        assert key in data

    total = data["team_a_win"] + data["draw"] + data["team_b_win"]
    assert 99.0 <= total <= 101.0  # allow rounding slack

    assert data["predicted"] in (data["team_a"], data["team_b"], "Draw")
    assert 0 <= data["confidence"] <= 100


def test_predict_rejects_too_short_team_names(client):
    res = client.post("/api/v1/predict", json={"team_a": "F", "team_b": "N"})
    assert res.status_code == 422


def test_predict_is_order_independent(client):
    """
    Regression test for the home-team-bias bug: predicting A vs B and B vs A
    should describe the *same* underlying matchup, just mirrored. Before the
    fix, swapping team order shifted win probability toward whichever team
    was passed as team_a — this asserts that no longer happens beyond a
    small tolerance from floating point / model averaging.
    """
    forward = client.post("/api/v1/predict", json={"team_a": "France", "team_b": "England"}).json()
    reverse = client.post("/api/v1/predict", json={"team_a": "England", "team_b": "France"}).json()

    # forward's team_a_win should roughly equal reverse's team_b_win, and vice versa
    assert abs(forward["team_a_win"] - reverse["team_b_win"]) < 2.0
    assert abs(forward["team_b_win"] - reverse["team_a_win"]) < 2.0
    assert abs(forward["draw"] - reverse["draw"]) < 2.0


def test_predictions_list_has_no_pending_matches(client):
    """
    Data-integrity check: the tournament is complete, so every tracked
    prediction should have a result — total_predictions should equal played.
    Intentionally not hard-coding the count (70) since that's a snapshot,
    not a stable contract; this checks the *relationship* instead.
    """
    res = client.get("/api/v1/accuracy")
    assert res.status_code == 200
    data = res.json()
    assert data["played"] == data["total_predictions"]
    assert 0 <= data["accuracy"] <= 100


def test_predictions_list_items_have_expected_shape(client):
    res = client.get("/api/v1/predictions")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) > 0
    row = data[0]
    for key in ("team_a", "team_b", "predicted", "confidence", "stage"):
        assert key in row


# ── Player Analyzer ───────────────────────────────────────────────────────

def test_nations_list_is_populated(client):
    res = client.get("/api/v1/nations")
    assert res.status_code == 200
    nations = res.json()
    assert isinstance(nations, list)
    assert len(nations) >= 40  # all 48 WC nations minus any edge-case exclusions
    assert "Argentina" in nations


def test_cluster_profiles_has_six_archetypes(client):
    res = client.get("/api/v1/clusters")
    assert res.status_code == 200
    profiles = res.json()
    assert len(profiles) == 6


def test_players_for_known_nation_have_stat_fields(client):
    res = client.get("/api/v1/players/Argentina")
    assert res.status_code == 200
    players = res.json()
    assert len(players) > 0
    p = players[0]
    for key in ("short_name", "overall", "cluster_name", "pace", "shooting"):
        assert key in p


def test_players_for_unknown_nation_returns_404(client):
    res = client.get("/api/v1/players/Atlantis")
    assert res.status_code == 404


# ── Sentiment (structure only — external API can legitimately be flaky) ────

def test_sentiment_stats_returns_expected_shape(client):
    """
    Only checks response shape, not live Reddit data — Arctic Shift is a
    free third-party service with no uptime SLA, so asserting on live
    fetch success here would make this test flaky for reasons outside
    the app's own control.
    """
    res = client.get("/api/v1/sentiment/stats")
    assert res.status_code == 200
    data = res.json()
    for key in ("total", "positive", "negative", "neutral", "reddit_configured"):
        assert key in data
