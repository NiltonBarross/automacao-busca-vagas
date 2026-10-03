"""Opt-in real smoke, never run as part of the offline test suite."""
from pathlib import Path
import json
import sys
from threading import Event

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from job_hunter.domain.models import Profile, SearchConfig
from job_hunter.storage.sqlite import Store
from job_hunter.application.search import SearchService

root = Path(__file__).resolve().parents[1]
store = Store(root / "data" / "smoke.sqlite")
service = SearchService(store)
config = SearchConfig(name="Smoke técnico sem perfil pessoal", terms=["Power BI"], max_pages=1, max_jobs=2,
                      max_seconds=90, modes=["remoto", "híbrido", "presencial", "não informada"], cities=["São Paulo/SP"], location_required=False)
run_id = store.create_run(Profile(), config)
service.execute(run_id, Profile(), config, Event())
run = store.run(run_id)
report = {"run": run, "jobs": [{"url": r["job"]["url"], "title": r["job"]["title"],
          "extraction": r["job"]["extraction"], "description_chars": len(r["job"]["description"]),
          "requirements_chars": len(r["job"]["requirements"])} for r in store.results(run_id)]}
(root / "data" / "smoke-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(0 if report["jobs"] and all(j["description_chars"] >= 80 for j in report["jobs"]) else 1)
