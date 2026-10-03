from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import base64
import json
import re
import unicodedata
from urllib.parse import unquote, urlsplit, urlunsplit

MODES = ["remoto", "híbrido", "presencial", "não informada"]
SENIORITIES = ["estágio", "júnior", "pleno", "sênior", "liderança", "não informada"]
STATES = ["nova", "revisar", "favorita", "candidatura registrada", "descartada"]
LEVELS = ["básico", "intermediário", "avançado"]


def now():
    return datetime.now(timezone.utc).isoformat()


def fold(text):
    return "".join(c for c in unicodedata.normalize("NFKD", str(text).lower()) if not unicodedata.combining(c))


def contains(text, term):
    return bool(re.search(r"(?<!\w)" + re.escape(fold(term)) + r"(?!\w)", fold(text)))


def canonical_url(url):
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    if parts.scheme != "https" or not host.endswith(".gupy.io") or parts.username or parts.port:
        raise ValueError("Link deve ser um anúncio HTTPS da Gupy.")
    path = parts.path.rstrip("/")
    if re.fullmatch(r"/jobs/\d+", path):
        return urlunsplit(("https", host, path, "", ""))
    if path.startswith("/job/"):
        token = unquote(path.split("/job/", 1)[1])
        try:
            job_id = json.loads(base64.b64decode(token + "=" * (-len(token) % 4)))["jobId"]
            if re.fullmatch(r"\d+", str(job_id)):
                return f"https://{host}/jobs/{job_id}"
        except (ValueError, KeyError, TypeError, UnicodeDecodeError):
            pass
    raise ValueError("Formato de link de anúncio não reconhecido.")


@dataclass
class Profile:
    name: str = ""
    education: str = ""
    experience: str = ""
    skills: dict = field(default_factory=dict)
    languages: str = ""
    years: float | None = None
    seniorities: list = field(default_factory=list)
    extra: str = ""
    version: int = 0

    def validate(self):
        if self.years is not None and not 0 <= self.years <= 80:
            raise ValueError("Anos de experiência devem estar entre 0 e 80.")
        if any(not k.strip() or v not in LEVELS for k, v in self.skills.items()):
            raise ValueError("Cada competência exige nome e domínio básico/intermediário/avançado.")
        if any(s not in SENIORITIES for s in self.seniorities):
            raise ValueError("Senioridade declarada inválida.")


@dataclass
class SearchConfig:
    name: str = "Minha busca"
    terms: list = field(default_factory=list)
    synonyms: dict = field(default_factory=dict)
    seniorities: list = field(default_factory=lambda: SENIORITIES.copy())
    modes: list = field(default_factory=lambda: ["remoto"])
    cities: list = field(default_factory=list)
    location_required: bool = True
    min_salary: float | None = None
    salary_required: bool = True
    missing_salary: str = "pendência"
    exclude_terms: list = field(default_factory=list)
    deprioritize_terms: list = field(default_factory=list)
    affirmative: str = "sinalizar"
    max_pages: int = 2
    max_jobs: int = 20
    max_seconds: int = 180
    weights: list = field(default_factory=lambda: [35, 45, 20])

    def validate(self):
        if not self.terms or any(not isinstance(t, str) or not t.strip() for t in self.terms):
            raise ValueError("Informe ao menos um termo de busca.")
        if len(self.terms) > 20:
            raise ValueError("Use até 20 termos por busca.")
        if not self.modes or any(m not in MODES for m in self.modes):
            raise ValueError("Selecione modalidades válidas.")
        if not self.seniorities or any(s not in SENIORITIES for s in self.seniorities):
            raise ValueError("Selecione senioridades válidas.")
        if any(m in self.modes for m in ["híbrido", "presencial"]) and not self.cities:
            raise ValueError("Informe uma cidade/UF para busca local.")
        if any(not re.fullmatch(r".+/[A-Za-z]{2}", city.strip()) for city in self.cities):
            raise ValueError("Use cidade/UF, por exemplo Cidade/UF.")
        if not (1 <= self.max_pages <= 10 and 1 <= self.max_jobs <= 100 and 30 <= self.max_seconds <= 900):
            raise ValueError("Limites: 1–10 páginas, 1–100 vagas, 30–900 segundos.")
        if self.min_salary is not None and self.min_salary <= 0:
            raise ValueError("Salário mínimo deve ser positivo.")
        if len(self.weights) != 3 or min(self.weights) < 0 or sum(self.weights) != 100:
            raise ValueError("Os três pesos devem ser não negativos e somar 100.")
        if self.missing_salary not in ["pendência", "excluir"] or self.affirmative not in ["sinalizar", "excluir"]:
            raise ValueError("Política de ausência/afirmativa inválida.")
        if any(not k.strip() or not isinstance(v, list) or any(not str(x).strip() for x in v)
               for k, v in self.synonyms.items()):
            raise ValueError("Sinônimos devem ter nome e alternativas não vazios.")


@dataclass
class Job:
    url: str
    title: str = ""
    company: str | None = None
    location: str | None = None
    mode: str = "não informada"
    seniority: str = "não informada"
    description: str = ""
    requirements: str = ""
    raw_text: str = ""
    salary: float | None = None
    published_at: str | None = None
    extraction: str = "incompleta"
    source: str = "gupy"

    def __post_init__(self):
        self.url = canonical_url(self.url)

    @property
    def key(self):
        # Source ID includes the tenant to avoid collisions across company subdomains.
        return self.source + ":" + self.url.split("https://", 1)[1]

    def to_dict(self):
        return asdict(self)
