# Desenvolvimento

## Baseline
Original: othiagom/automacao-busca-vagas, commit 562daf8 de 21/08/2026.
O coletor usava DOM, Rio de Janeiro/remoto fixos e descrição genérica. Sheets era inicializado
antes da coleta. Falha Gemini virava nota zero. Código substituído por módulos locais isolados;
a implementação original permanece no histórico upstream e a licença MIT foi mantida integralmente.

## Ambiente
Python 3.12.14, Streamlit 1.65.0, Playwright 1.63.0, BeautifulSoup 4.14.3 e pytest 9.1.1.
`requirements.txt` fixa dependências transitivas para Windows/Python 3.12.
Reconstruir lock com `uv pip compile pyproject.toml --extra dev --python .venv/Scripts/python.exe --output-file requirements.txt`.
Para outra versão de Python/SO, revisar compatibilidade e gerar lock próprio antes de afirmar suporte.

## Spec Kit
Instalação oficial PyPI specify-cli 1.0.13, inicializada por:
`specify init --here --force --non-interactive --integration codex --integration-options='--skills' --script ps --ignore-agent-tools`.
Princípios em `.specify/memory/constitution.md`; feature em `specs/001-busca-local/`.
Scripts setup-plan/setup-tasks e resolver foram executados. Skills constitution, specify, plan,
tasks, implement e converge orientam os artefatos. Nenhum arquivo interno foi inventado.
Não existe mecanismo de slash-command no terminal: o agente lê/aplica as skills geradas.
Documentação: https://github.github.io/spec-kit/installation.html.

## CodeGraph
Distribuição confirmada pelo usuário: https://github.com/colbymchenry/codegraph, versão 1.6.1.
Instalação oficial `npm install -g @colbymchenry/codegraph@1.6.1`.
Configuração local criada por `codegraph install --target=codex --location=local --yes --no-permissions`.
Índice criado por `codegraph init --yes`; reconstruir com `codegraph index` ou atualizar com `codegraph sync`.
Consultar `codegraph explore 'símbolo ou arquivo'` antes de localizar código; conferir achados em fonte/testes.
Python foi reconhecido no baseline e no índice final. `.codegraph/` e `.codex/` são locais e ignorados.
O indexador respeita `.gitignore`; dados privados ficam em diretórios ignorados antes da indexação.
Em outro checkout, repetir instalação local e indexação. MCP requer recarregar o agente e confiança
no projeto; a CLI foi utilizada nesta sessão sem alterar confiança global.

## Ponytail
Skill oficial aplicada em modo full após solicitação do usuário:
https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md.
Review: https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail-review/SKILL.md.
Não é necessário instalar um runtime: nesta sessão o agente leu e aplicou as instruções oficiais.
SQLite direto, dataclasses, threading/Event, csv e constraints nativas; sem ORM/factory/interface
com uma implementação. Fluxo legado e dependências Google/IA removidos, sem guardar código morto.
Os exemplos de teste permanecem porque os contratos foram exigidos explicitamente no plano.

## Arquitetura e limites
UI não coleta; SearchService coordena; GupyCollector navega; normalizer preserva texto; rules avalia;
Store usa transações por operação. Worker não chama Streamlit e cria seu próprio Playwright.
Uma execução por processo, cancelamento cooperativo; reinício preserva dados e marca interrupted.
Fallback DOM deliberadamente não recebe score, mesmo com texto extenso, até validar sua estrutura.
Lista vazia exige evidência explícita; paginação precisa mudar links e rejeita assinaturas repetidas.
Links /job/ com jobId codificado são convertidos para /jobs/ID, sem parâmetros de rastreamento.

## Evoluções após revisão do MVP
- Calibrar pesos e heurísticas em amostra revisada manualmente.
- Validar templates DOM de empresas sem JSON-LD; não atribuir confiança indevida ao fallback.
- Mais fontes/Sheets via adaptadores opcionais somente quando necessários.
- IA opcional: consentimento de envio, schema/evidências, cache versionado e erro separado de score.

## Entrega de 05/10/2026
Groq integrado apenas para sugestão de cargos; urllib/json resolvem chamadas sem dependência nova.
Provider é uma configuração de endpoint/modelo/chave para a mesma função REST; nenhum SDK ou
adaptador vazio. Cache limitado em memória, sem guardar chave no banco ou nos snapshots.
Ponytail full/review aplicado ao diff: controles nativos, catálogo JSON público, dataclasses.replace
para preservar filtros e reuso do SearchService existente. Não há estrutura especulativa.

Impeccable oficial aplicado remotamente:
https://github.com/pbakaus/impeccable/blob/main/.agents/skills/impeccable/SKILL.md.
Referências Operate, polish e craft-floor: navegação horizontal, hierarquia sóbria, tema único,
controles acessíveis e inspeção desktop/mobile. Launcher indisponível; contexto foi lido diretamente.
Nenhum runtime de design instalado nem dados privados usados na verificação visual.

Municípios: https://servicodados.ibge.gov.br/api/v1/localidades/municipios?orderBy=nome.
Snapshot público de 05/10/2026 em domain/municipalities.json (27 UFs, 5.571 municípios).
Refresh deve preservar metadados, revisar diferenças e validar catálogo; nenhuma chamada durante uso.
