<!-- CODEGRAPH_START -->
## CodeGraph

In repositories indexed by CodeGraph (a `.codegraph/` directory exists at the repo root), reach for it BEFORE grep/find or reading files when you need to understand or locate code:

- **MCP tool** (when available): `codegraph_explore` answers most code questions in one call — the relevant symbols' verbatim source plus the call paths between them, including dynamic-dispatch hops grep can't follow. Name a file or symbol in the query to read its current line-numbered source. If it's listed but deferred, load it by name via tool search.
- **Shell** (always works): `codegraph explore "<symbol names or question>"` prints the same output.

If there is no `.codegraph/` directory, skip CodeGraph entirely — indexing is the user's decision.
<!-- CODEGRAPH_END -->

## Projeto Busca Vagas
- Use os artefatos em specs/001-busca-local/ e a constituição em .specify/memory/constitution.md.
- Execute .venv/Scripts/python.exe -m pytest -q; smoke real é opt-in via scripts/smoke.py.
- Não ler/indexar/versionar dados pessoais em data/, exportações, .env ou o plano privado.
- Ponytail full ativo: reutilize stdlib/dependências existentes e mantenha só abstrações necessárias.
- Domínio/aplicação não dependem de Streamlit. IA opcional só sugere termos (autorizada em 05/10/2026); coleta/avaliação funcionam sem IA. Sheets permanece fora deste MVP.
- Preserve LICENSE e crédito ao original. Reindexe após alterações relevantes com codegraph index.
