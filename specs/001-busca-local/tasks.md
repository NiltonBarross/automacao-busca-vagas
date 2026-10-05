# Tasks: Busca local
**Input**: spec.md, plan.md, research.md, data-model.md, contracts/ui.md
**Tests**: solicitados na FR-011; offline com fixtures fictícias; smoke real separado.

## Phase 1: Setup
- [x] T001 Preservar upstream/licença e inicializar Spec Kit/CodeGraph em .specify/ e AGENTS.md.
- [x] T002 Fixar dependências e preparar execução Windows em pyproject.toml e scripts/start.ps1.

## Phase 2: Foundational
- [x] T003 Definir validação, contratos e chave canônica em src/job_hunter/domain/models.py.
- [x] T004 Implementar transações, snapshots e estados em src/job_hunter/storage/sqlite.py.

## Phase 3: US1 Configurar (P1)
**Independent Test**: salvar/reabrir/editar dados fictícios sem código.
- [x] T005 [US1] Escrever testes de persistência/validação em tests/integration/test_storage.py.
- [x] T006 [US1] Implementar formulários de perfil/critérios em src/job_hunter/ui/app.py.

## Phase 4: US2 Coletar (P2)
**Independent Test**: fixtures de anúncio/vazio/falha e cancelamento; smoke separado.
- [x] T007 [US2] Escrever contratos/classificação em tests/unit/test_contracts.py e tests/fixtures/.
- [x] T008 [US2] Implementar normalização JSON-LD/DOM em src/job_hunter/normalization/gupy.py.
- [x] T009 [US2] Implementar limites/falhas/paginação em src/job_hunter/collectors/gupy.py.
- [x] T010 [US2] Implementar filtros/evidências/pesos ajustáveis em src/job_hunter/scoring/rules.py.
- [x] T011 [US2] Implementar snapshots/worker/cancelamento em src/job_hunter/application/search.py.
- [x] T012 [US2] Mostrar progresso e histórico em src/job_hunter/ui/app.py.

## Phase 5: US3 Revisar (P3)
**Independent Test**: favorito preservado em reencontro; CSV neutraliza fórmula.
- [x] T013 [US3] Escrever testes de estados/exportação em tests/integration/test_storage.py.
- [x] T014 [US3] Implementar CSV em src/job_hunter/exports/csv.py.
- [x] T015 [US3] Implementar resultados/filtros/ordenação/notas em src/job_hunter/ui/app.py.

## Phase 6: Polish
- [x] T016 Validar interface via tests/integration/test_ui.py e teste no navegador local.
- [x] T017 Documentar baseline, instalação e backlog em README.md e docs/development.md.
- [x] T018 Registrar smoke real via scripts/smoke.py em specs/001-busca-local/validation.md.
- [x] T019 Aplicar Ponytail review, verificar convergência e atualizar CodeGraph em docs/development.md.

## Dependencies & Execution Order
Setup → domínio/storage → US1 → US2 → US3 → validação. Testes de cada história antes da implementação.
Exemplos paralelos: testes storage e fixtures; CSV e documentação. Não exigem agentes adicionais.

## Implementation Strategy
MVP incremental. IA para sugestões autorizada em 05/10/2026; Sheets/novas fontes continuam posteriores.
Ponytail full: sqlite3, dataclasses, threading, csv; sem ORM, factories ou protocolos de uma implementação.

## Phase 7: Cadastro Usuário — solicitação de 03/10/2026
- [x] T020 [US1] Expandir Profile com contato, localização, resumo, cursos e currículo em src/job_hunter/domain/models.py.
- [x] T021 [US1] Criar Usuário com Cadastro/Currículo e salvar sem perder documento em src/job_hunter/ui/app.py.
- [x] T022 [US1] Preservar perfis antigos e confirmar domínio ausente em tests/integration/test_storage.py e src/job_hunter/scoring/rules.py.
- [x] T023 [US1] Verificar formulários/consulta e proteção do PDF em tests/integration/test_ui.py e .gitignore.

## Phase 8: Localidades, Groq e navegação — solicitação de 05/10/2026
- [x] T024 [US1] Catálogo oficial IBGE empacotado e seletores dependentes para cadastro e busca.
- [x] T025 [US2] Sugestões Groq com resumo limitado, saída validada, cache e fallback extensível/local, sem SDK.
- [x] T026 [US2] Revisar/editar termos ou sugerir e iniciar uma única busca, preservando filtros e busca original.
- [x] T027 Navegação horizontal e tema responsivo usando Impeccable Operate/polish e Ponytail full.
- [x] T028 Testar offline seletores, minimização, JSON inválido, fallback/cache e execução; inspecionar desktop/mobile.
- [x] T029 Atualizar evidências/documentação, reindexar CodeGraph e entregar preview local.
