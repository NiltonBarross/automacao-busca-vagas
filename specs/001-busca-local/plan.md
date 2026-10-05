# Implementation Plan: Busca local e revisão
**Branch**: `feat/perfil-e-filtros` | **Date**: 2026-10-02 | **Spec**: [spec.md](spec.md)
**Input**: specs/001-busca-local/spec.md

## Summary
Aplicativo local com formulários privados, coleta Gupy isolada, regras experimentais com evidências,
SQLite e resultados por execução. Preservar o original como referência histórica, sem acioná-lo pelo app.

## Technical Context
**Language/Version**: Python 3.12.14 (mínimo 3.11)
**Primary Dependencies**: Streamlit 1.65.0, Playwright 1.63.0, BeautifulSoup 4.14.3
**Storage**: SQLite local em data/, WAL e conexões por operação
**Testing**: pytest 9.1.1, fixtures fictícias e Streamlit AppTest; smoke separado
**Target Platform**: Windows, navegador localhost
**Project Type**: aplicação web local
**Performance Goals**: UI responde durante coleta; cancelamento após operação de até 30 s
**Constraints**: IA opcional apenas para termos, sem Sheets, sem dados pessoais versionados; um worker por processo
**Scale/Scope**: uma pessoa, até 100 vagas e 10 páginas por termo, até 15 minutos

## Constitution Check
Antes da pesquisa: PASS — dados locais, camadas isoladas, evidências e falhas explícitas.
Após desenho: PASS — Event cooperativo, snapshots/avaliações por run, CSV seguro, fixtures separadas.
Pesos experimentais 35/45/20 editáveis, sem afirmar que foram calibrados em amostra humana.

## Project Structure
### Documentation (this feature)
Spec, plan, research, data-model, contracts/ui.md, quickstart, tasks e validation em specs/001-busca-local/.
### Source Code (repository root)
app.py e src/job_hunter/{ui,application,domain,collectors,normalization,scoring,storage,exports}/.
Testes em tests/{unit,integration,fixtures}/; scripts/start.ps1, scripts/smoke.py; docs/development.md.
**Structure Decision**: uma distribuição Python local; módulos pequenos por responsabilidade.

## Architecture Decisions
- Worker thread cria e fecha Playwright síncrono; nunca chama Streamlit. Event sinaliza cancelamento.
- UI usa fragment periódico e dados persistidos; registro de worker impede duplicação em reruns.
- Prazo monotônico global e timeouts reduzidos ao tempo restante; persistir vaga antes de continuar.
- Preferir JSON-LD JobPosting validado no detalhe; fallback DOM explícito marca extração incompleta.
- Portal: cartões com links Gupy e paginação por botão; detectar IDs repetidos; vazio só com evidência.
- Regras: literal/sinônimos declarados, negação/desejável identificados; requisito ambíguo vira pendência.
- Score com denominador fixo 100, evidências por componente; ausência de descrição suficiente dá None.
- Local/salário podem excluir ou apenas gerar preferência; desconhecidos seguem política explícita.
- Unicidade fonte/ID (subdomínio + ID) com fallback URL sem query; histórico preserva snapshot da vaga.
- Groq opcional para termos conforme solicitação de 05/10/2026; demais integrações ficam no backlog.

## Complexity Tracking
Nenhuma violação. Threads são necessárias para cancelar enquanto UI permanece responsiva.

## Evolução de 05/10/2026
- Catálogo oficial IBGE com 27 UFs e 5.571 municípios em recurso JSON empacotado; seletores dependentes sem chamadas durante navegação.
- Suggestions usa urllib/json/hashlib/dataclasses, sem SDK adicional. Resumo <=3.000 caracteres, até quatro termos, 600 tokens incluindo raciocínio baixo nos GPT-OSS (350 em outros modelos). Padrões GPT-OSS 20B/120B confirmados na API de modelos da conta durante teste autenticado.
- Cadeia: GROQ_MODEL → GROQ_FALLBACK_MODEL → provedor compatível opcional → título/competências locais. Até 10 s por tentativa; 401/403 não repete a mesma chave.
- Cache limitado a 64 respostas bem-sucedidas em memória por hash do resumo e configuração; mudanças relevantes invalidam, falhas não ficam no cache.
- Streamlit usa segmented_control, seletores e botões nativos, tema azul sóbrio e layout estreito responsivo, seguindo Impeccable Operate/polish e Ponytail full.
- Constitution Check após emenda 1.1.0: PASS — acionamento explícito, minimização, chaves fora do banco, filtros preservados e funcionamento offline sem IA.
