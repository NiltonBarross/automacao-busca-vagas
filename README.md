# Busca Vagas — aplicativo local

Configure seu perfil no navegador, salve buscas na Gupy e revise anúncios com evidências.
O MVP usa Python, Streamlit, SQLite e Playwright. Não exige credenciais Google ou serviços pagos.

## Executar no Windows

Requisito: Python 3.11 ou superior. Nesta máquina o ambiente `.venv` já está preparado.

```powershell
.\scripts\start.ps1
```

Abra http://127.0.0.1:8501. Preencha **Usuário**, salve **Critérios** e abra **Executar e revisar**.
Em **Usuário → Cadastro**, reúna contato, cidade/UF, links, resumo, formação, certificações,
experiências, competências e idiomas. **Usuário → Currículo** permite consultar o texto e baixar
o documento original registrado localmente. Campos ausentes e domínio não informado exigem revisão.
Competências aceitam domínio não informado, básico, intermediário ou avançado. Selecione estado e cidade no cadastro.
Nos critérios, selecione estados e uma ou mais cidades para híbrido/presencial; remoto é tratado separadamente.
O catálogo público do IBGE funciona offline (snapshot de 05/10/2026).
A busca começa em **Iniciar busca** ou **Sugerir e pesquisar**; salvar e navegar não iniciam coleta.

Instalação manual reproduzível:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e . --no-deps
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --browser.gatherUsageStats false
```

## Comportamento

- Perfil versionado, várias buscas salvas e critérios copiados para cada execução.
- Limites de tempo/páginas/vagas, progresso, falhas por operação e cancelamento cooperativo.
- Descrição/requisitos via JSON-LD; fallback textual fica sinalizado como incompleto e sem nota.
- Score experimental com evidências e pesos editáveis; dados ausentes geram pendências.
- Deduplicação, histórico por execução, favoritos, observações, estado de candidatura e CSV.

A nota ordena a revisão e não estima chance de contratação. Os pesos ainda precisam de revisão humana.
As regras usam correspondências literais e sinônimos configurados, não interpretação semântica completa.
Condições de formação, idiomas, domínio avançado e vagas afirmativas são apresentadas para confirmação.
`Também para PcD` não é automaticamente considerado restrição de elegibilidade.
A ausência de um anúncio numa busca não prova seu encerramento.

Cancelar preserva anúncios já gravados e espera a operação corrente terminar (timeout de até 30 s).
Bloqueios de acesso são registrados sem tentativa de contorno. A fonte pode mudar e exigir ajuste.
Anúncios excluídos ficam disponíveis na opção **Mostrar vagas excluídas pelos critérios**.

## Dados privados

Banco padrão: `data/jobs.sqlite`. Perfil, bancos, exportações, credenciais, `.codegraph/` e o plano
local original ficam fora do Git. SQLite contém dados pessoais em texto; proteja os arquivos e
faça backup com o aplicativo parado. Nunca publique o conteúdo de `data/`.
O diretório deste checkout está no OneDrive: a sincronização dessa pasta depende da configuração
pessoal do OneDrive. Para manter o banco fora dela, configure `JOB_HUNTER_DB` no ambiente antes de abrir.
`.env.example` documenta a variável; o aplicativo não carrega `.env` automaticamente.

IA é opcional e acionada somente nos botões de sugestão. Um resumo profissional limitado é enviado
ao provedor configurado; nome, contato e links são removidos antes do envio. Confira o resumo na
interface. O currículo completo, anúncios e snapshots não são enviados para avaliação por IA.
Candidaturas são feitas por você. Google Sheets e novas fontes continuam fora do escopo.

## Sugestões com Groq

Em **Executar e revisar**, escolha uma busca salva. Abra **Configurar Groq e conferir o resumo enviado**
e informe sua chave no campo protegido, ou configure `GROQ_API_KEY` no ambiente antes de iniciar.
A chave digitada fica na sessão do navegador; não é salva no banco.
Use **Sugerir termos** para revisar/editar e salvar, ou **Sugerir e pesquisar** para iniciar uma cópia
da busca com novos termos, preservando localização, salário, exclusões e limites.

Envio limitado a 3.000 caracteres, até quatro termos, saída de até 350 tokens (600 no modelo de reserva).
Respostas bem-sucedidas do mesmo resumo/provedor são reutilizadas em memória até reiniciar o servidor;
falhas não são armazenadas no cache. A IA escolhe termos; a coleta e avaliação continuam locais.

Fallback: `GROQ_MODEL` (padrão `llama-3.1-8b-instant`) → `GROQ_FALLBACK_MODEL`
(padrão `openai/gpt-oss-20b`) → provedor opcional → sugestão local de título/competências.
Para adicionar um provedor compatível, configure `AI_FALLBACK_BASE_URL` (HTTPS, incluindo `/v1`),
`AI_FALLBACK_MODEL` e `AI_FALLBACK_API_KEY`. Cada tentativa tem timeout de 10 segundos;
origem e falhas aparecem na interface. Sem chave, a alternativa local funciona sem tokens.
Consulte a [API Groq](https://console.groq.com/docs/openai) e os [modelos disponíveis](https://console.groq.com/docs/models).

## Verificar

```powershell
.\.venv\Scripts\python.exe -m pytest -q
# Opcional: coleta real pequena, separada dos testes offline
.\.venv\Scripts\python.exe scripts\smoke.py
```

Os testes offline usam exemplos fictícios e páginas interceptadas; não consultam a rede Gupy.
O smoke grava um relatório técnico sem perfil pessoal em `data/smoke-report.json`.
Veja [validação](specs/001-busca-local/validation.md), [especificação](specs/001-busca-local/spec.md)
e [desenvolvimento](docs/development.md).

## Origem e licença

Fork de [othiagom/automacao-busca-vagas](https://github.com/othiagom/automacao-busca-vagas),
de Thiago Marques Ramalho, baseline `562daf8` (21/08/2026). Mantém histórico, créditos e licença MIT.
O fluxo anterior com perfil fixo, Gemini e Sheets foi substituído; está preservado no histórico Git.
Veja [LICENSE](LICENSE). Esta versão adiciona a interface e o armazenamento local.
