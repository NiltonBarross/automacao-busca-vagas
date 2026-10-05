"""Real Chromium with intercepted fictional pages; no Gupy network traffic."""
from pathlib import Path
from threading import Event
import pytest
from job_hunter.collectors.gupy import GupyCollector, CollectionError
from job_hunter.domain.models import SearchConfig


def test_pagination_repetition_and_explicit_empty():
    fixture = Path(__file__).parents[1] / "fixtures"
    card = (fixture / "listing.html").read_text(encoding="utf-8")
    detail = (fixture / "detail.html").read_text(encoding="utf-8")
    events = []
    config = SearchConfig(terms=["BI"], max_pages=3, max_seconds=30)
    with GupyCollector(config, Event(), lambda kind, value: events.append(kind)) as collector:
        def listing(route):
            body = "<main>0 resultados</main>" if "empty" in route.request.url else card + '<button aria-label="Próxima" onclick="document.querySelector(\'a\').href=document.querySelector(\'a\').href.includes(\'123\')?\'https://fictional.gupy.io/jobs/456\':\'https://fictional.gupy.io/jobs/123\'">Próxima</button>'
            route.fulfill(status=200, content_type="text/html; charset=utf-8", body=body)
        collector.listing.route("**/*", listing)
        collector.detail.route("**/*", lambda route: route.fulfill(status=200, content_type="text/html; charset=utf-8", body=detail))
        cache = {}
        with pytest.raises(CollectionError, match="Página repetida"):
            list(collector.jobs("BI", cache))
        assert len(cache) == 2 and events.count("page") == 3
        assert list(collector.jobs("empty", {})) == []
        assert "empty" in events
