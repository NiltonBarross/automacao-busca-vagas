from pathlib import Path
from streamlit.testing.v1 import AppTest
from job_hunter.storage.sqlite import Store
from job_hunter.domain.models import Job, Profile
from job_hunter.application.search import SearchService
from job_hunter.application.suggestions import SuggestionService
from job_hunter.domain.models import SearchConfig
from job_hunter.scoring.rules import evaluate


def test_profile_and_local_search_validation(tmp_path, monkeypatch):
    path = tmp_path / "ui.sqlite"
    monkeypatch.setenv("JOB_HUNTER_DB", str(path))
    Store(path).save_profile(Profile(resume_filename="ficticio.pdf", resume_text="Currículo fictício para teste de preservação."))
    app = AppTest.from_file(str(Path(__file__).parents[2] / "app.py")).run(timeout=15)
    assert not app.exception
    app.text_input[0].set_value("Pessoa Fictícia")
    next(widget for widget in app.text_area if widget.label.startswith("Competências declaradas")).set_value("SQL: avançado")
    next(widget for widget in app.text_input if widget.label == "E-mail").set_value("pessoa@example.org")
    next(widget for widget in app.selectbox if widget.label == "Estado").set_value("SP").run()
    next(widget for widget in app.selectbox if widget.label == "Cidade").set_value("São Paulo")
    app.button[0].click().run()
    assert Store(path).load_profile().skills == {"SQL": "avançado"}
    assert Store(path).load_profile().email == "pessoa@example.org"
    assert Store(path).load_profile().city == "São Paulo"
    assert Store(path).load_profile().resume_text == "Currículo fictício para teste de preservação."
    assert any(tab.label == "Currículo" for tab in app.tabs)
    app.get("button_group")[0].set_value("Critérios").run()
    assert not app.exception
    app.text_area[0].set_value("Analista de BI")
    next(widget for widget in app.multiselect if widget.label == "Modalidades").set_value(["presencial"])
    app.button[0].click().run()
    assert any("cidade" in error.value for error in app.error)
    next(widget for widget in app.multiselect if widget.label == "Estados da busca").set_value(["SP"]).run()
    next(widget for widget in app.multiselect if widget.label == "Cidades da busca").set_value(["São Paulo/SP"])
    app.button[0].click().run()
    assert Store(path).load_search().cities == ["São Paulo/SP"]
    store = Store(path)
    profile, config = store.load_profile(), store.load_search()
    run_id = store.create_run(profile, config)
    job = Job(url="https://fictional.gupy.io/jobs/123", title="Analista de BI", company="Empresa Fictícia",
              location="São Paulo/SP", mode="presencial", extraction="json-ld",
              description="Responsabilidades e atribuições: elaborar relatórios de BI e desenvolver consultas em SQL para apoiar análises.", requirements="SQL obrigatório")
    store.record_job(run_id, job, "Analista de BI", evaluate(job, profile, config))
    store.update_run(run_id, status="completed")
    app.get("button_group")[0].set_value("Executar e revisar").run()
    assert not app.exception
    next(widget for widget in app.selectbox if widget.label == "Estado pessoal").set_value("favorita")
    next(button for button in app.button if button.label == "Salvar acompanhamento").click().run()
    assert store.results(run_id)[0]["state"] == "favorita"


def test_suggest_and_search_preserves_filters_and_runs_once(tmp_path, monkeypatch):
    path = tmp_path / "assistant.sqlite"
    monkeypatch.setenv("JOB_HUNTER_DB", str(path))
    monkeypatch.setenv("GROQ_API_KEY", "fake-test-key")
    store = Store(path)
    store.save_profile(Profile(headline="Analista de dados", skills={"SQL": "avançado"}))
    config = SearchConfig(name="Busca fictícia", terms=["SQL"], modes=["presencial"], cities=["São Paulo/SP"],
                          min_salary=5000, exclude_terms=["vendas"], max_pages=1, max_jobs=2, max_seconds=30)
    store.save_search(config)
    monkeypatch.setattr(SuggestionService, "suggest", lambda *args: {
        "terms": ["Analista de BI"], "source": "Groq fictício", "failures": [], "usage": {}, "cached": False})
    started = []
    def start(service, profile, criteria):
        started.append(criteria)
        run = service.store.create_run(profile, criteria)
        service.store.update_run(run, status="completed")
        return run
    monkeypatch.setattr(SearchService, "start", start)
    app = AppTest.from_file(str(Path(__file__).parents[2] / "app.py")).run(timeout=15)
    app.get("button_group")[0].set_value("Executar e revisar").run()
    next(button for button in app.button if button.label == "Sugerir e pesquisar").click().run()
    assert not app.exception
    assert len(started) == 1
    suggested = store.load_search("Busca fictícia · sugerida")
    assert suggested.terms == ["Analista de BI"]
    for field in ["modes", "cities", "min_salary", "exclude_terms", "max_pages", "max_jobs", "max_seconds"]:
        assert getattr(suggested, field) == getattr(config, field)
    assert store.load_search("Busca fictícia").terms == ["SQL"]
    app.run()
    assert len(started) == 1
