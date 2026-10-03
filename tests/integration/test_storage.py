from job_hunter.domain.models import Job, Profile, SearchConfig
from job_hunter.storage.sqlite import Store
from job_hunter.exports.csv import export_csv


def test_profile_versions_and_search_reopen(tmp_path):
    path = tmp_path / "db.sqlite"
    store = Store(path)
    profile = Profile(education="Formação fictícia", skills={"SQL": "básico"})
    assert store.save_profile(profile) == 1
    profile.skills["SQL"] = "avançado"
    assert store.save_profile(profile) == 2
    config = SearchConfig(terms=["Analista de dados"], cities=["Cidade Fictícia/XX"])
    store.save_search(config)
    reopened = Store(path)
    assert reopened.load_profile().skills == {"SQL": "avançado"}
    assert reopened.load_profile().version == 2
    assert reopened.load_search().cities == ["Cidade Fictícia/XX"]


def test_dedup_state_history_and_csv(tmp_path):
    store = Store(tmp_path / "db.sqlite")
    p, c = Profile(), SearchConfig(terms=["SQL"])
    job = Job(url="https://fictional.gupy.io/jobs/123?source=x", title="=1+1", description="SQL")
    first = store.create_run(p, c)
    assert store.record_job(first, job, "SQL", {"score": None})
    store.set_state(job.key, "favorita", "@note")
    second = store.create_run(p, c)
    job.description = "SQL atualizado"
    assert not store.record_job(second, job, "SQL", {"score": 42})
    store.record_job(second, job, "Dados", {"score": 42})
    rows = store.results(second)
    assert len(rows) == 1 and rows[0]["state"] == "favorita"
    assert rows[0]["terms"] == ["SQL", "Dados"]
    assert store.results(first)[0]["job"]["description"] == "SQL"
    exported = export_csv(rows).decode("utf-8-sig")
    assert "'=1+1" in exported and "'@note" in exported
