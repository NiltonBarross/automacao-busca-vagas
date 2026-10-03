from threading import Event
from job_hunter.application.search import SearchService
from job_hunter.domain.models import Job, Profile, SearchConfig
from job_hunter.collectors.gupy import CollectionError, GupyCollector, StopCollection
from job_hunter.storage.sqlite import Store
from unittest.mock import Mock
import pytest


class FixtureCollector:
    def __init__(self, config, cancel, progress):
        self.cancel, self.progress = cancel, progress

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def jobs(self, term, cache):
        self.progress("page", "Página fictícia")
        if term == "falha":
            raise CollectionError("rede", "Falha fictícia")
        job = Job(url="https://fictional.gupy.io/jobs/123", title="BI")
        cache[job.key] = job
        yield job
        if term == "cancelar":
            self.cancel.set()
            raise StopCollection("cancelled")


def test_partial_failure_continues_terms_and_cancellation_preserves(tmp_path):
    store = Store(tmp_path / "db.sqlite")
    service = SearchService(store)
    profile = Profile()
    config = SearchConfig(terms=["falha", "BI"])
    run_id = store.create_run(profile, config)
    service.execute(run_id, profile, config, Event(), FixtureCollector)
    assert store.run(run_id)["status"] == "partial"
    assert len(store.results(run_id)) == 1
    config.terms = ["cancelar", "BI"]
    run_id = store.create_run(profile, config)
    service.execute(run_id, profile, config, Event(), FixtureCollector)
    assert store.run(run_id)["status"] == "cancelled"
    assert len(store.results(run_id)) == 1
    assert store.run(run_id)["terms_done"] == 0


def test_restarts_keep_results_and_mark_interrupted(tmp_path):
    store = Store(tmp_path / "db.sqlite")
    run_id = store.create_run(Profile(), SearchConfig(terms=["BI"]))
    store.record_job(run_id, Job(url="https://fictional.gupy.io/jobs/123"), "BI", {})
    SearchService(store)
    assert store.run(run_id)["status"] == "interrupted"
    assert len(store.results(run_id)) == 1


def test_http_block_is_not_retried_and_transient_is_bounded():
    collector = GupyCollector(SearchConfig(terms=["BI"]), Event(), lambda *_: None)
    page = Mock()
    page.goto.return_value.status = 403
    with pytest.raises(CollectionError, match="403") as exc:
        collector.navigate(page, "https://fictional.gupy.io/jobs/123")
    assert exc.value.kind == "bloqueio" and page.goto.call_count == 1
    page.reset_mock()
    page.goto.return_value.status = 503
    with pytest.raises(CollectionError):
        collector.navigate(page, "https://fictional.gupy.io/jobs/123")
    assert page.goto.call_count == 2


def test_cancelled_collector_does_not_navigate():
    cancel = Event()
    cancel.set()
    collector = GupyCollector(SearchConfig(terms=["BI"]), cancel, lambda *_: None)
    page = Mock()
    with pytest.raises(StopCollection):
        collector.navigate(page, "https://fictional.gupy.io/jobs/123")
    page.goto.assert_not_called()
