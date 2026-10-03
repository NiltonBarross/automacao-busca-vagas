# Research
## Decisão: ambiente e processo
Python 3.12.14 disponível no runtime local; .venv criado sem modificar Python global.
Spec Kit 1.0.13 inicializado oficialmente com codex skills e PowerShell.
CodeGraph 1.6.1 confirmado pelo usuário, instalado oficialmente, índice Python: 8 arquivos/78 nós.
Alternativa rejeitada: criar formatos internos das ferramentas manualmente.
Fontes: https://github.github.io/spec-kit/installation.html e https://github.com/colbymchenry/codegraph.

## Decisão: execução cooperativa
Worker com Event; UI consulta progresso e histórico. Playwright nasce/morre dentro do worker.
Motivo: Streamlit não recomenda chamadas de UI em threads; Playwright não é thread-safe.
Alternativas: loop bloqueante impede cancelar; multiprocessing fica para cancelamento imediato futuro.
Fontes: https://docs.streamlit.io/develop/concepts/design/multithreading
https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment
https://playwright.dev/python/docs/library
https://playwright.dev/python/docs/api/class-page

## Decisão: coleta adaptável
Validar portal ao vivo antes do adaptador; JSON-LD oficial do anúncio quando presente, fallback DOM.
Não assumir API pública. Status de bloqueio, vazio, rede e alteração estrutural separados.
Evidência do smoke será registrada em validation.md; indisponibilidade não equivale a lista vazia.

## Decisão: classificação conservadora
Pesos 35/45/20 experimentais ajustáveis, não calibrados. Descrição insuficiente não recebe score.
Publicidade e qualquer formação só influenciam pendências quando requisito educacional explícito existe.
Sem envio externo de perfil. IA opcional e Sheets fora deste MVP após validação humana.
