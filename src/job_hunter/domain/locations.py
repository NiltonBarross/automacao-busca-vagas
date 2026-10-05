"""Catálogo público do IBGE, disponível também sem internet."""
from functools import lru_cache
from importlib.resources import files
import json


@lru_cache(maxsize=1)
def catalogue():
    return json.loads(files("job_hunter.domain").joinpath("municipalities.json").read_text(encoding="utf-8"))["states"]


def states():
    return sorted(catalogue(), key=lambda uf: catalogue()[uf]["name"])


def state_label(uf):
    return f"{catalogue()[uf]['name']} ({uf})" if uf else "Selecione um estado"


def cities(uf):
    return list(catalogue().get(uf, {}).get("cities", []))
