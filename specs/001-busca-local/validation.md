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

## Atualização Usuário — 03/10/2026
Cadastro ampliado com contato, localização, links, título/resumo profissional, formação, cursos,
experiências, competências e idiomas. Consulta ao texto do currículo e download do original local.
Currículo utilizado somente no armazenamento privado; PDF, texto, importador e capturas ignorados pelo Git.
Níveis de domínio ausentes continuam não informados; anos de experiência não foram calculados.
Campos previamente preenchidos foram preservados. A cidade do cadastro não altera critérios de busca.

14 testes passaram, incluindo compatibilidade com perfis antigos, edição sem perder currículo,
persistência dos novos dados, formulário e pendência de competência com nível não informado.
Navegador confirmou Usuário → Cadastro/Currículo, campos preenchidos e download disponível.
Servidor atualizado após confirmar ausência de buscas em execução.


## Evolução validada em 05/10/2026 — cidades, Groq e navegação
- `.venv/Scripts/python.exe -m pytest -q`: **27 passed**. Fixtures fictícias, sem rede Gupy/Groq.
- Seletores UF/cidade e persistência; híbrido/presencial rejeita cidades vazias; preservação do currículo existente.
- Resumo <=3.000 caracteres inclusive caracteres escapados; remoção de nome, e-mail, telefone, URLs e linhas de contato.
- Contrato REST simulado: JSON/limites/timeout; respostas inválidas acionam fallback; 401 não repete a mesma chave.
- Cache de sucesso sem nova chamada; mudança no resumo invalida; falhas não ficam no cache; provedor adicional configurável.
- AppTest: Sugerir e pesquisar inicia uma vez, mantém modalidade/cidade/salário/exclusões/limites e preserva busca original.
- Chromium em banco fictício separado: navegação, mudança SP→RJ, cidade correspondente, salvamento e sugestão local.
- Inspeção 1440/768/390 px: sem overflow horizontal, sem exceções/UI ou erros JS; navegação com alvos de 44 px e placeholders em português.
- Wheel construído com sucesso; catálogo público IBGE incluído (27 UFs, 5.571 municípios).
- Ponytail full/review: stdlib, controles nativos e módulos existentes; zero novas dependências da aplicação.
- Impeccable Operate/polish/craft-floor aplicado; launcher ausente, contexto lido diretamente; QA com dados fictícios.
- CodeGraph reconstruído: 20 arquivos, 260 nós, 784 arestas; dados privados permanecem ignorados.
- Preview local reiniciado em 127.0.0.1:8501; health responde `ok`.
- **Limite de validação:** nenhuma chave Groq disponível; chamada autenticada real depende de configuração do usuário na interface/ambiente. Novo smoke real Gupy não executado (opt-in).


### Teste autenticado Groq em 05/10/2026
- Credencial fornecida para testes; somente memória do processo, sem arquivo/banco/Git.
- `/models` confirmou GPT-OSS 20B/120B disponíveis; Llama 3.1 retornou 404 e foi substituído no padrão.
- Perfil fictício: GPT-OSS 20B retornou quatro cargos, 268 tokens; repetição confirmou cache sem nova chamada.
- Falha principal simulada: fallback real GPT-OSS 120B retornou termos válidos, 288 tokens.
- Primeira chamada real GPT-OSS 20B: 285 tokens; total das três chamadas bem-sucedidas: 841 tokens.
- Servidor reiniciado com credencial apenas no ambiente do processo. Interface confirmou configuração sem iniciar busca ou enviar currículo pessoal.
- 27 testes offline passaram novamente; CodeGraph reconstruído. A limitação de chamada autenticada registrada acima foi resolvida.
