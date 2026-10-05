import json
from urllib.error import HTTPError, URLError
import pytest

from job_hunter.application.suggestions import Provider, SuggestionService, compact_profile, providers, request_terms
from job_hunter.domain.locations import cities, states
from job_hunter.domain.models import Profile


def test_catalogue_filters_by_state_and_works_offline():
    assert len(states()) == 27
    assert "São Paulo" in cities("SP")
    assert "Rio de Janeiro" not in cities("SP")
    assert "Rio de Janeiro" in cities("RJ")
    assert cities("") == []


def test_summary_is_bounded_and_redacts_contacts():
    p = Profile(name="Pessoa Fictícia", email="pessoa@example.org", phone="(11) 99999-9999",
                skills={"SQL": "avançado"}, resume_text="Pessoa Fictícia\npessoa@example.org\n(11) 99999-9999\n"
                "https://linkedin.com/in/ficticio\nEndereço: Rua Fictícia\nExperiência com SQL " + "x" * 9000)
    text = json.dumps(compact_profile(p), ensure_ascii=False)
    assert len(text) <= 3000
    for value in [p.name, p.email, p.phone, "linkedin.com", "Rua Fictícia"]:
        assert value not in text
    assert "SQL" in text
    escaped = Profile(headline='"' * 160, summary='"' * 350, experience='"' * 500,
                      education='"' * 200, skills={'"' * 60 + str(i): "básico" for i in range(24)}, resume_text='"' * 3000)
    assert len(json.dumps(compact_profile(escaped), ensure_ascii=False)) <= 3000


def test_fallback_caches_success_and_invalidates_changed_profile():
    calls = []
    chain = [Provider("Groq", "https://example.org", "primary", "fake"),
             Provider("Groq", "https://example.org", "reserve", "fake")]
    def transport(provider, summary):
        calls.append(provider.model)
        if provider.model == "primary":
            raise URLError("offline")
        return ["Analista de dados"], {"total_tokens": 100}
    service = SuggestionService(transport)
    profile = Profile(skills={"SQL": "avançado"})
    result = service.suggest(profile, chain)
    assert result["terms"] == ["Analista de dados"] and result["failures"]
    assert service.suggest(profile, chain)["cached"]
    assert calls == ["primary", "reserve"]
    profile.skills["Python"] = "básico"
    service.suggest(profile, chain)
    assert len(calls) == 4


def test_auth_failure_skips_same_key_and_local_failure_is_not_cached():
    calls = []
    def transport(provider, summary):
        calls.append(provider.model)
        raise HTTPError(provider.base_url, 401, "unauthorized", {}, None)
    service = SuggestionService(transport)
    chain = [Provider("Groq", "https://example.org", model, "fake") for model in ["primary", "reserve"]]
    profile = Profile(headline="Analista de dados")
    assert service.suggest(profile, chain)["source"] == "Sugestão local · sem IA"
    service.suggest(profile, chain)
    assert calls == ["primary", "primary"]
    assert service.suggest(profile, [])["terms"] == ["Analista de dados"]
    with pytest.raises(ValueError, match="Preencha"):
        service.suggest(Profile(), [])


@pytest.mark.parametrize("terms", [[], "SQL", [42], ["x" * 81], ["SQL\nPython"], ["SQL"] * 5])
def test_invalid_remote_output_is_rejected(monkeypatch, terms):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, limit):
            return json.dumps({"choices": [{"message": {"content": json.dumps({"terms": terms})}}]}).encode()
    monkeypatch.setattr("job_hunter.application.suggestions.urlopen", lambda *args, **kwargs: Response())
    with pytest.raises(ValueError):
        request_terms(Provider("Groq", "https://example.org", "fake", "fake"), {})


def test_request_uses_compact_json_and_bounded_tokens(monkeypatch):
    def urlopen(request, timeout):
        payload = json.loads(request.data)
        assert request.full_url == "https://example.org/chat/completions"
        assert timeout == 10 and payload["max_completion_tokens"] == 350
        assert len(payload["messages"]) == 2
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return b'{"choices":[{"message":{"content":"{\\"terms\\":[\\"Analista de dados\\"]}"}}],"usage":{"total_tokens":80}}'
        return Response()
    monkeypatch.setattr("job_hunter.application.suggestions.urlopen", urlopen)
    terms, usage = request_terms(Provider("Groq", "https://example.org", "fake", "fake"), {"competencias": ["SQL"]})
    assert terms == ["Analista de dados"] and usage["total_tokens"] == 80


def test_extra_provider_can_be_configured(monkeypatch):
    monkeypatch.setenv("AI_FALLBACK_BASE_URL", "https://example.org/v1/")
    monkeypatch.setenv("AI_FALLBACK_MODEL", "reserve")
    monkeypatch.setenv("AI_FALLBACK_API_KEY", "fake")
    chain = providers("fake-groq")
    assert chain[-1].base_url == "https://example.org/v1"
    assert chain[-1].name == "Provedor reserva"
