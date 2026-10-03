# Validação — 001-busca-local

Data: 02/10/2026 (America/Sao_Paulo). Perfil pessoal não utilizado na validação.

## Verificação offline
` .venv/Scripts/python.exe -m pytest -q `: **12 testes passaram**, com dependências fixadas em requirements.txt.
Cobrem perfil versionado/reabertura, critérios locais, deduplicação, estados pessoais, histórico por
execução, CSV com fórmulas neutralizadas, JSON-LD, negação/desejável, salário ausente, afirmativa,
continuidade após falha, cancelamento preservando resultados, reinício, bloqueio sem retentativa,
retentativa transitória limitada, paginação repetida e vazio explícito em Chromium interceptado.
Streamlit AppTest salvou perfil/critérios, rejeitou busca local sem cidade e marcou favorito no resultado.
`pip check`: nenhum requisito quebrado. `compileall`: sem erros. `git diff --check`: sem erros.

## Navegador local
Servidor em 127.0.0.1:8501. Playwright verificou navegação Perfil → Critérios → Executar e revisar.
Controles de formação/competências/idiomas e critérios renderizados; nenhum erro JavaScript.
Capturas locais inspecionadas em data/ui-profile.png e data/ui-criteria.png; fora do Git.
Nenhum perfil pessoal ou fixture foi inserido no banco de uso real.

## Smoke real
Executado em 02/10/2026 às 22:49 (fuso São Paulo), `scripts/smoke.py`.
Termo Power BI, uma página, duas vagas, prazo 90 segundos; sem cookies de usuário ou credenciais.
- Leega, https://leega.gupy.io/jobs/12611328: JSON-LD, 4.264 caracteres de descrição e 1.269 de requisitos.
- Smarthis, https://smarthis.gupy.io/jobs/12613169: fallback textual, 5.782 caracteres e 812 de requisitos;
  sem JSON-LD, marcada incompleta, sem nota, para revisão manual.
Duas vagas preservadas. Status limited por limite de duas vagas; um aviso de extração incompleta.
Relatório local em data/smoke-report.json. Repetição encontrou dois anúncios existentes e registrou
as duplicatas sem duplicar os registros nem apagar o histórico.

O primeiro smoke revelou espera de visibilidade em script JSON-LD, que é invisível. Corrigido para
esperar h1 visível. A segunda execução coletou os dados descritos acima. Disponibilidade da fonte
é observação desta amostra, não garantia. Paginação real multipágina não foi exercitada nesta amostra;
o contrato de avanço/repetição foi verificado offline com navegador real.

## Revisão Ponytail
Skill full aplicada e revisão de complexidade realizada.
Removidos sete arquivos do fluxo legado, incluindo a interface abstrata com um coletor, perfil fixo
Gemini e persistência Sheets. Removidas dependências Google/IA, OpenAI, PostgreSQL e ORM do lock.
Sem factories, interfaces com uma implementação, camada de IA vazia ou integrações especulativas.
Heurísticas e limite de uma execução por processo têm limites documentados; validações preservadas.
O código novo corresponde aos comportamentos pedidos, com stdlib onde suficiente.

## Limitações e revisão humana
Pesos 35/45/20 são experimentais e configuráveis. Ainda falta calibração humana numa amostra.
Fallback DOM não recebe score. Formação/idiomas/domínio avançado exigem revisão explícita.
IA opcional, Sheets e fontes adicionais foram adiados conforme a ordem do plano de entrada.
