from fastapi.testclient import TestClient

from debatrix.main import app


def test_mock_debate_flow(tmp_path, monkeypatch):

    monkeypatch.setenv("DEBATRIX_DB", str(tmp_path / "test.db"))
    c = TestClient(app)
    d = c.post(
        "/api/debates",
        json={
            "topic": "Should AI be regulated?",
            "side": "for",
            "persona": "Socratic",
            "provider": "mock",
        },
    ).json()
    events = c.post(
        f"/api/debates/{d['id']}/turn",
        json={"argument": "Everyone knows AI must be stopped."},
    )
    assert events.status_code == 200 and "text/event-stream" in events.headers["content-type"]
    assert "@@POSITION@@" not in events.text
    assert '"type": "done"' in events.text and '"type": "user"' in events.text
    assert c.get(f"/api/debates/{d['id']}").json()["turns"][0]["argument"].startswith("Everyone")
    assert c.post(f"/api/debates/{d['id']}/judge").json()["scores"]


def test_all_read_endpoints_and_unknown_debate(tmp_path, monkeypatch):

    monkeypatch.setenv("DEBATRIX_DB", str(tmp_path / "api.db"))
    client = TestClient(app)
    assert client.get("/api/health").json()["status"] == "ok"
    assert len(client.get("/api/topics").json()) == 6
    assert client.get("/api/debates/missing").status_code == 404
    assert client.post("/api/debates/missing/judge").status_code == 404


def test_input_validation_and_judge_bounds(tmp_path, monkeypatch):

    monkeypatch.setenv("DEBATRIX_DB", str(tmp_path / "validation.db"))
    client = TestClient(app)
    assert client.post("/api/debates", json={}).status_code == 422
    debate = client.post("/api/debates", json={"topic": "Test", "provider": "mock"}).json()
    assert debate["persona"] == "Socratic"
    result = client.post(f"/api/debates/{debate['id']}/judge").json()
    assert all(0 <= row["score"] <= 10 for row in result["scores"].values())
    assert 0 <= result["overall"] <= 10


def test_unreachable_ollama_falls_back_to_mock(tmp_path, monkeypatch):
    import debatrix.main as main
    from debatrix.llm.providers import ProviderUnavailable

    monkeypatch.setenv("DEBATRIX_DB", str(tmp_path / "fallback.db"))
    original_stream_turn = main.stream_turn

    def fail_ollama(provider, *args):
        if provider.name == "ollama":
            raise ProviderUnavailable("offline")
        return original_stream_turn(provider, *args)

    monkeypatch.setattr(main, "stream_turn", fail_ollama)
    client = TestClient(app)
    debate = client.post("/api/debates", json={"topic": "Test", "provider": "ollama"}).json()
    response = client.post(
        f"/api/debates/{debate['id']}/turn", json={"argument": "A measured argument."}
    )
    assert response.status_code == 200
    assert '"fallback": true' in response.text
    assert '"type": "done"' in response.text
