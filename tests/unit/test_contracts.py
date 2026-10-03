import json
from pathlib import Path
import pytest
from job_hunter.domain.models import Job, Profile, SearchConfig
from job_hunter.normalization.gupy import parse_detail, parse_cards
from job_hunter.scoring.rules import evaluate

FIXTURES = Path(__file__).parents[1] / "fixtures"


def test_location_and_limits_are_validated():
    with pytest.raises(ValueError, match="cidade"):
        SearchConfig(terms=["BI"], modes=["presencial"]).validate()
    with pytest.raises(ValueError):
        SearchConfig(terms=["BI"], max_jobs=0).validate()


def test_jsonld_and_canonical_identity():
    card = parse_cards((FIXTURES / "listing.html").read_text(encoding="utf-8"))[0]
    job = parse_detail((FIXTURES / "detail.html").read_text(encoding="utf-8"), card)
    assert job.title == "Analista de BI Pleno" and job.company == "Empresa Fictícia"
    assert "SQL" in job.requirements and job.mode == "remoto"
    assert job.key == Job(url="https://fictional.gupy.io/jobs/123").key
    assert job.salary is None


def test_rules_unknown_optional_negation_and_education():
    config = SearchConfig(terms=["BI"], seniorities=["pleno"])
    profile = Profile(skills={"SQL": "avançado"}, seniorities=["pleno"], education="Publicidade")
    job = Job(url="https://fictional.gupy.io/jobs/123", title="Analista de BI Pleno",
              description="Responsabilidades: criar dashboards. Requisitos e qualificações:\nSQL obrigatório.\nPython desejável.\nNão é necessário Git.\nSuperior em área correlata.",
              requirements="SQL obrigatório.\nPython desejável.\nNão é necessário Git.\nSuperior em área correlata.", seniority="pleno", mode="remoto", extraction="json-ld")
    result = evaluate(job, profile, config)
    assert result["score"] is not None and result["eligibility"] != "excluída"
    assert any("formação" in x.lower() for x in result["pending"])
    assert not any("Git" in x and "não declarada" in x for x in result["pending"])
    assert any("desejável" in x.lower() for x in result["pending"])
    assert all(e["job"] and e["profile"] for e in result["evidence"])
    assert evaluate(Job(url=job.url, title=job.title), profile, config)["score"] is None


def test_missing_salary_and_explicit_affirmative():
    job = Job(url="https://fictional.gupy.io/jobs/123", title="BI", mode="remoto")
    config = SearchConfig(terms=["BI"], min_salary=6000, missing_salary="excluir")
    assert evaluate(job, Profile(), config)["eligibility"] == "excluída"
    config.min_salary = None
    job.description = "Também para PcD; todos podem se candidatar."
    assert evaluate(job, Profile(), config)["eligibility"] != "excluída"
    job.description = "Vaga exclusiva para PcD."
    assert any("afirmativa" in s.lower() for s in evaluate(job, Profile(), config)["pending"])
