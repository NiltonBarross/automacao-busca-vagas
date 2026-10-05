import re
from job_hunter.domain.models import contains, fold

VERSION = "rules-v1-experimental"
KNOWN_SKILLS = ["SQL", "Python", "Power BI", "DAX", "Power Query", "Excel", "Git", "ETL", "Azure", "Fabric", "Databricks", "Tableau", "Looker", "Power Automate"]


def evaluate(job, profile, config):
    pending, reasons, evidence, preferences = [], [], [], []
    whole = job.title + "\n" + job.description
    eligibility = "sem exclusão explícita"

    def mismatch(message, required):
        nonlocal eligibility
        if required:
            eligibility = "excluída"
            reasons.append(message)
        else:
            preferences.append(message)

    if job.mode == "não informada":
        pending.append("Modalidade não informada; confirmar.")
    if job.mode not in config.modes:
        mismatch(f"Modalidade {job.mode} fora da seleção.", config.location_required)
    if job.mode != "remoto" and config.cities:
        if not job.location or "..." in job.location or contains(job.location, "não informado"):
            pending.append("Localização ausente/incompleta; confirmar cidade/UF.")
        else:
            # ponytail: literal city/state matching; add a geocoder only for observed ambiguity.
            matched = any(contains(job.location, city.split("/")[0].strip()) and
                          (contains(job.location, city.split("/")[1].strip()) or state_name(city.split("/")[1]) in fold(job.location)) for city in config.cities)
            if not matched:
                mismatch(f"Localização {job.location} fora das cidades escolhidas.", config.location_required)
    if job.seniority not in config.seniorities:
        mismatch(f"Senioridade {job.seniority} fora da seleção.", True)
    for term in config.exclude_terms:
        if contains(whole, term):
            mismatch(f"Termo de descarte obrigatório encontrado: {term}.", True)
    for term in config.deprioritize_terms:
        if contains(whole, term):
            preferences.append(f"Termo de menor prioridade: {term}.")
    affirmative = re.search(r"[^\n.]*(?:afirmativa|exclusiv[ao].{0,35}(?:pcd|pessoas|mulheres|negros|negras))[^\n.]*", fold(whole))
    if affirmative:
        pending.append("Condição afirmativa: revisar elegibilidade pessoal. Evidência: " + affirmative.group(0))
        if config.affirmative == "excluir":
            mismatch("Vaga afirmativa excluída por critério explícito.", True)
    if config.min_salary:
        if job.salary is None:
            pending.append("Salário mensal BRL não publicado; confirmar.")
            if config.missing_salary == "excluir":
                mismatch("Salário ausente excluído pelo critério explícito.", True)
        elif job.salary < config.min_salary:
            mismatch(f"Salário publicado {job.salary:g} abaixo de {config.min_salary:g}.", config.salary_required)

    wf, ws, wx = config.weights
    score = 0
    for term in config.terms:
        aliases = [term] + config.synonyms.get(term, [])
        hit = next((alias for alias in aliases if contains(job.title, alias)), None)
        if hit:
            score += wf
            evidence.append({"component": "função", "points": wf, "job": job.title, "profile": f"Objetivo de busca: {term} (correspondência {hit})"})
            break
    if not any(e["component"] == "função" for e in evidence):
        pending.append("Função/atividades sem correspondência literal aos objetivos; revisão manual.")

    # ponytail: conservative sentence heuristics; replace only after a reviewed sample identifies failures.
    active_optional = False
    lines = []
    for line in re.split(r"\n|(?<=[.!?])\s+", job.requirements or job.description):
        if fold(line).strip() in ["diferenciais", "desejavel", "desejáveis", "desejaveis"]:
            active_optional = True
        if fold(line).strip().startswith(("competencias comportamentais", "requisitos obrigatorios")):
            active_optional = False
        lines.append((line, active_optional or bool(re.search(r"desejav|diferencial|sera um plus", fold(line)))))
    mentioned = {skill: [(line, optional) for line, optional in lines if contains(line, skill)
                         and not re.search(r"nao\s+(?:e\s+)?(?:necessari|exigi|precisa)|sem necessidade", fold(line))]
                 for skill in set(KNOWN_SKILLS) | set(profile.skills)}
    mentioned = {k: v for k, v in mentioned.items() if v}
    technical_points = ws / len(mentioned) if mentioned else 0
    for skill, matches in mentioned.items():
        declared = next((s for s in profile.skills if fold(s) == fold(skill)), None)
        line, optional = matches[0]
        if declared:
            score += technical_points
            evidence.append({"component": "competência", "points": round(technical_points, 2), "job": line,
                             "profile": f"{declared}: {profile.skills[declared]} declarado"})
            if profile.skills[declared] == "não informado":
                pending.append(f"Nível de domínio de {skill} não informado; confirmar.")
            if re.search(r"avancad|solida|dominio", fold(line)) and profile.skills[declared] != "avançado":
                pending.append(f"Domínio de {skill} precisa de confirmação: {line}")
        else:
            pending.append(f"Competência {skill} não declarada ({'desejável' if optional else 'menção a confirmar'}): {line}")
    if not mentioned:
        pending.append("Nenhuma competência reconhecida; revisar requisitos manualmente.")

    years = re.search(r"(?:minim[oa]\s*(?:de\s*)?|pelo menos\s*)(\d+)\s*anos", fold(job.requirements))
    confirmed = job.seniority != "não informada" and job.seniority in profile.seniorities
    if years:
        if profile.years is None:
            confirmed = False
            pending.append("Anos de experiência não declarados: " + years.group(0))
        elif profile.years < int(years.group(1)):
            confirmed = False
            pending.append(f"Experiência declarada {profile.years:g} anos abaixo do requisito: {years.group(0)}")
    if confirmed:
        score += wx
        evidence.append({"component": "senioridade", "points": wx, "job": job.title + ("; " + years.group(0) if years else ""),
                         "profile": f"Senioridade declarada: {job.seniority}; anos: {profile.years if profile.years is not None else 'não informados'}"})
    else:
        pending.append("Senioridade/experiência sem confirmação de correspondência.")
    for line, optional in lines:
        if re.search(r"superior|graduacao|formacao|bacharel|ingles|english|idioma", fold(line)):
            pending.append(f"Confirmar formação/idioma ({'desejável' if optional else 'requisito a revisar'}): {line}")
    if job.extraction == "incompleta":
        pending.append("Extração incompleta: anúncio exige revisão manual.")
    sufficient = len(job.description) >= 80 and job.extraction != "incompleta"
    coverage = round(100 * sum([bool(job.title), bool(job.company), bool(job.description), bool(job.requirements),
                               job.mode != "não informada", job.seniority != "não informada"]) / 6)
    return {"version": VERSION, "score": round(min(score, 100), 1) if sufficient else None,
            "coverage": coverage, "eligibility": eligibility, "reasons": reasons,
            "evidence": evidence, "pending": list(dict.fromkeys(pending)), "preferences": preferences,
            "experimental": True}


def state_name(uf):
    pairs = "AC:Acre|AL:Alagoas|AP:Amapa|AM:Amazonas|BA:Bahia|CE:Ceara|DF:Distrito Federal|ES:Espirito Santo|GO:Goias|MA:Maranhao|MT:Mato Grosso|MS:Mato Grosso do Sul|MG:Minas Gerais|PA:Para|PB:Paraiba|PR:Parana|PE:Pernambuco|PI:Piaui|RJ:Rio de Janeiro|RN:Rio Grande do Norte|RS:Rio Grande do Sul|RO:Rondonia|RR:Roraima|SC:Santa Catarina|SP:Sao Paulo|SE:Sergipe|TO:Tocantins"
    return fold(dict(pair.split(":") for pair in pairs.split("|")).get(uf.strip().upper(), "__unknown__"))
