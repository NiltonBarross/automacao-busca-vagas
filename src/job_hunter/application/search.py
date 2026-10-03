from dataclasses import asdict
import logging
from threading import Event, Lock, Thread
from job_hunter.collectors.gupy import GupyCollector, CollectionError, StopCollection
from job_hunter.domain.models import Profile, SearchConfig, now
from job_hunter.scoring.rules import evaluate

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, store):
        self.store = store
        self.lock = Lock()
        self.worker = None
        self.cancel_event = Event()
        self.active_id = None
        store.interrupt_running()

    def active(self):
        return bool(self.worker and self.worker.is_alive())

    def start(self, profile, config):
        profile.validate()
        config.validate()
        with self.lock:
            if self.active():
                raise ValueError("Já existe uma busca em execução neste processo.")
            profile = Profile(**asdict(profile))
            config = SearchConfig(**asdict(config))
            self.cancel_event = Event()
            self.active_id = self.store.create_run(profile, config)
            self.worker = Thread(target=self.execute, args=(self.active_id, profile, config, self.cancel_event), daemon=True)
            self.worker.start()
            return self.active_id

    def cancel(self):
        self.cancel_event.set()

    def execute(self, run_id, profile, config, cancel, collector_factory=GupyCollector):
        cache = {}
        stats = {"pages": 0, "jobs": 0, "duplicates": 0, "failures": 0, "terms_done": 0, "errors": []}
        limited = False

        def progress(kind, value):
            nonlocal limited
            if kind == "page":
                stats["pages"] += 1
            elif kind == "page_limit":
                limited = True
            elif kind == "error":
                stats["failures"] += 1
                stats["errors"].append(value)
                logger.warning("Coleta: %s", value)
            self.store.update_run(run_id, **stats, stage=str(value) if kind != "error" else value["message"])

        status = "completed"
        try:
            with collector_factory(config, cancel, progress) as collector:
                for term in config.terms:
                    if cancel.is_set():
                        raise StopCollection("cancelled")
                    self.store.update_run(run_id, term=term)
                    try:
                        for job in collector.jobs(term, cache):
                            result = evaluate(job, profile, config)
                            if not self.store.record_job(run_id, job, term, result):
                                stats["duplicates"] += 1
                            stats["jobs"] = len(cache)
                            self.store.update_run(run_id, **stats, stage="Anúncio salvo e avaliado")
                    except CollectionError as exc:
                        progress("error", {"kind": exc.kind, "term": term, "message": str(exc)})
                        if exc.kind == "bloqueio":
                            status = "partial" if stats["jobs"] else "failed"
                            break
                    stats["terms_done"] += 1
                    self.store.update_run(run_id, **stats)
                else:
                    status = "partial" if stats["failures"] else "limited" if limited else "completed"
        except StopCollection as exc:
            status = exc.status
        except Exception as exc:
            logger.exception("Execução interrompida")
            progress("error", {"kind": "erro de execução", "message": str(exc).splitlines()[0]})
            status = "partial" if stats["jobs"] else "failed"
        finally:
            if cancel.is_set():
                status = "cancelled"
            self.store.update_run(run_id, **stats, status=status, stage="Execução encerrada", finished_at=now())
