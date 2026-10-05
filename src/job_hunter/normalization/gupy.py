import json
import re
from bs4 import BeautifulSoup
from job_hunter.domain.models import Job, fold, contains


def text(html):
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return "\n".join(line.strip() for line in soup.get_text("\n").splitlines() if line.strip())


def seniority(title):
    for level, aliases in {"estágio": ["estagiario", "estagio"], "júnior": ["junior", "jr"],
                           "pleno": ["pleno", "pl"], "sênior": ["senior", "sr"],
                           "liderança": ["lead", "gerente", "coordenador"]}.items():
        if any(contains(title, alias) for alias in aliases):
            return level
    return "não informada"


def parse_cards(html):
    cards = []
    for anchor in BeautifulSoup(html, "html.parser").select("a:has(h3)"):
        title = anchor.select_one("h3").get_text(" ", strip=True)
        raw = anchor.get_text("\n", strip=True)
        company = anchor.select_one("p")
        location = anchor.select_one('[data-testid="job-location"]')
        mode = next((m for m in ["híbrido", "remoto", "presencial"] if contains(raw, m)), "não informada")
        try:
            cards.append(Job(url=anchor.get("href", ""), title=title,
                             company=company.get_text(strip=True) if company else None,
                             location=location.get_text(strip=True) if location else None,
                             mode=mode, seniority=seniority(title), raw_text=raw))
        except ValueError:
            continue
    return cards


def postings(value):
    if isinstance(value, list):
        for item in value:
            yield from postings(item)
    elif isinstance(value, dict):
        if "JobPosting" in ([value.get("@type")] if isinstance(value.get("@type"), str) else value.get("@type", [])):
            yield value
        if "@graph" in value:
            yield from postings(value["@graph"])


def requirement_section(description):
    lines = description.splitlines()
    start = next((i + 1 for i, line in enumerate(lines) if fold(line.strip()).startswith("requisitos e qualificacoes")), None)
    if start is None:
        return ""
    end = next((i for i in range(start, len(lines)) if fold(lines[i]).startswith(("informacoes adicionais", "etapas do processo"))), len(lines))
    return "\n".join(lines[start:end])


def parse_detail(html, card):
    soup = BeautifulSoup(html, "html.parser")
    structured = None
    for script in soup.select('script[type="application/ld+json"]'):
        try:
            structured = next(postings(json.loads(script.string or script.get_text())), None)
        except (ValueError, TypeError):
            continue
        if structured:
            break
    job = Job(**card.to_dict())
    if structured:
        job.title = structured.get("title") or job.title
        org = structured.get("hiringOrganization") or {}
        if isinstance(org, dict):
            job.company = org.get("name") or job.company
        job.description = text(structured.get("description", "").replace("\\n", "\n"))
        job.published_at = structured.get("datePosted")
        loc = structured.get("jobLocation") or {}
        if isinstance(loc, list):
            loc = loc[0] if loc else {}
        addr = loc.get("address", {}) if isinstance(loc, dict) else {}
        if isinstance(addr, dict) and addr.get("addressLocality"):
            job.location = " / ".join(str(addr[k]) for k in ["addressLocality", "addressRegion"] if addr.get(k))
        if structured.get("jobLocationType") == "TELECOMMUTE":
            job.mode = "remoto"
        # Only explicit monthly BRL values can be compared with a monthly salary preference.
        salary = structured.get("baseSalary") or {}
        salary = salary if isinstance(salary, dict) else {}
        value = salary.get("value", {})
        if salary.get("currency") == "BRL" and isinstance(value, dict) and value.get("unitText") == "MONTH":
            amount = value.get("value", value.get("minValue"))
            if isinstance(amount, (int, float)) and amount > 0:
                job.salary = amount
        job.extraction = "json-ld" if len(job.description) >= 80 else "incompleta"
    else:
        main = soup.select_one("main") or soup
        job.description = text(str(main))
        # DOM fallback needs manual verification; generic body text never receives a strong score.
        job.extraction = "incompleta"
    job.requirements = requirement_section(job.description)
    job.raw_text = text(html)
    job.seniority = seniority(job.title)
    return job
