from pathlib import Path
from streamlit.testing.v1 import AppTest
from job_hunter.storage.sqlite import Store
from job_hunter.domain.models import Job
from job_hunter.scoring.rules import evaluate


def test_profile_and_local_search_validation(tmp_path, monkeypatch):
    path = tmp_path / "ui.sqlite"
    monkeypatch.setenv("JOB_HUNTER_DB", str(path))
    app = AppTest.from_file(str(Path(__file__).parents[2] / "app.py")).run(timeout=15)
    assert not app.exception
    app.text_input[0].set_value("Pessoa Fictícia")
    app.text_area[2].set_value("SQL: avançado")
    app.button[0].click().run()
    assert Store(path).load_profile().skills == {"SQL": "avançado"}
    app.sidebar.radio[0].set_value("Critérios").run()
    assert not app.exception
    app.text_area[0].set_value("Analista de BI")
    app.multiselect[1].set_value(["presencial"])
    app.button[0].click().run()
    assert any("cidade" in error.value for error in app.error)
    app.text_area[2].set_value("Cidade Fictícia/XX")
    app.button[0].click().run()
    assert Store(path).load_search().cities == ["Cidade Fictícia/XX"]
    store = Store(path)
    profile, config = store.load_profile(), store.load_search()
    run_id = store.create_run(profile, config)
    job = Job(url="https://fictional.gupy.io/jobs/123", title="Analista de BI", company="Empresa Fictícia",
              location="Cidade Fictícia/XX", mode="presencial", extraction="json-ld",
              description="Responsabilidades e atribuições: elaborar relatórios de BI e desenvolver consultas em SQL para apoiar análises.", requirements="SQL obrigatório")
    store.record_job(run_id, job, "Analista de BI", evaluate(job, profile, config))
    store.update_run(run_id, status="completed")
    app.sidebar.radio[0].set_value("Executar e revisar").run()
    assert not app.exception
    next(widget for widget in app.selectbox if widget.label == "Estado pessoal").set_value("favorita")
    next(button for button in app.button if button.label == "Salvar acompanhamento").click().run()
    assert store.results(run_id)[0]["state"] == "favorita"
