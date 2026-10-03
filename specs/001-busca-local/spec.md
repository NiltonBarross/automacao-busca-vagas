# Feature Specification: Busca local e revisão de vagas

**Feature Branch**: `feat/perfil-e-filtros`
**Created**: 2026-10-02
**Status**: Ready for implementation
**Input**: Evoluir a referência original conforme o plano privado: perfil/filtros, coleta, regras, histórico e resultados locais.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Configurar perfil e busca (Priority: P1)
A pessoa registra formação, experiências, competências com domínio declarado, idiomas e objetivos separados.
Salva critérios e reabre a aplicação sem editar código.
**Why this priority**: Impede avaliar vagas para um perfil fixo de terceiro.
**Independent Test**: Salvar um perfil fictício, reiniciar armazenamento e conferir todos os campos.
**Acceptance Scenarios**:
1. **Given** formulário vazio, **When** salvar perfil, **Then** nenhuma competência é inferida.
2. **Given** busca local selecionada, **When** cidade está vazia, **Then** rejeitar com instrução clara.
3. **Given** critérios salvos, **When** reabrir, **Then** preservar termos, preferências e limites.

### User Story 2 - Coletar e avaliar (Priority: P2)
A pessoa inicia uma busca limitada, acompanha páginas/vagas/falhas e cancela entre operações.
**Why this priority**: Entrega anúncios reais com incertezas e evidências.
**Independent Test**: Coletor com fixtures offline e smoke real de uma página e duas vagas.
**Acceptance Scenarios**:
1. **Given** anúncio disponível, **When** coletar, **Then** salvar descrição e origem antes de avaliar.
2. **Given** falha ou bloqueio, **When** ocorre, **Then** registrar tipo e preservar resultados parciais.
3. **Given** busca em curso, **When** cancelar, **Then** finalizar após operação corrente preservando vagas.
4. **Given** anúncio ambíguo, **When** avaliar, **Then** apresentar pendências sem inventar qualificações.

### User Story 3 - Revisar e exportar (Priority: P3)
A pessoa filtra e ordena resultados, abre anúncios, marca favoritos/candidaturas e exporta tabela.
**Why this priority**: Transforma coleta em acompanhamento controlado pelo usuário.
**Independent Test**: Reencontrar vaga favorita e conferir histórico, estado e exportação segura.
**Acceptance Scenarios**:
1. **Given** vaga reencontrada, **When** nova busca termina, **Then** manter uma vaga e seu estado pessoal.
2. **Given** resultados parciais, **When** filtrar/exportar, **Then** manter acesso aos dados disponíveis.

### Edge Cases
- Lista vazia explícita difere de falha de extração; repetição de página encerra com aviso.
- Salário/empresa/cidade ausentes permanecem ausentes; elegibilidade afirmativa exige revisão.
- Texto desejável ou negado não vira requisito obrigatório; formação ambígua exige confirmação.
- Reinício do processo marca execuções interrompidas e mantém resultados.

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: Salvar/editar cadastro privado versionado na aba Usuário e critérios sem código ou credenciais. Cadastro inclui contato, cidade/UF, links, título/resumo profissional, formação, certificações, experiências, competências, idiomas e consulta ao currículo local. Domínio não informado é permitido sem inferir nível.
- **FR-002**: Critérios incluem termos/sinônimos, senioridade, modalidades, cidades/UF, salário opcional e tratamento de ausência, exclusões obrigatórias/preferências e limites.
- **FR-003**: Cada execução preserva snapshots, status, contadores, vínculos e erros por termo.
- **FR-004**: Coletar anúncios com limites, timeout, retentativa transitória limitada e progresso real; bloqueio encerra sem contorno.
- **FR-005**: Preservar texto/origem, descrição/requisitos, dados ausentes e datas.
- **FR-006**: Separar elegibilidade, aderência técnica e pendências, com evidência literal e cobertura; pesos experimentais ajustáveis.
- **FR-007**: Deduplicar por fonte/ID ou URL canônica, preservar first_seen/last_seen e estados pessoais.
- **FR-008**: Cancelar cooperativamente e consultar resultados/histórico mesmo após falha parcial.
- **FR-009**: Ordenar/filtrar/exportar CSV e editar estado/observação; neutralizar fórmulas de planilha.
- **FR-010**: Funcionar sem IA/Sheets; manter IA desativada e integrações posteriores fora deste MVP.
- **FR-011**: Testar persistência, classificação, contratos de coleta, cancelamento e interface offline; registrar smoke separado.

### Key Entities
- Profile e SearchConfig: declarações/critério versionados.
- SearchRun: snapshots, estado, limites, contadores e erros.
- Job e RunJob: anúncio canônico e vínculo por execução/termo.
- Evaluation: versão, evidências, cobertura, score opcional e pendências por execução.
- UserJobState: estado e notas independentes de avaliação.

## Success Criteria *(mandatory)*

### Measurable Outcomes
- **SC-001**: Todos os campos salvos sobrevivem à reabertura em teste de integração.
- **SC-002**: Duas buscas com mesmo anúncio mantêm uma vaga, dois vínculos e favorito.
- **SC-003**: Cancelamento preserva 100% das vagas já gravadas, com timeout de operação de até 30 segundos.
- **SC-004**: Cada ponto atribuído tem evidência; descrição insuficiente produz score ausente.
- **SC-005**: Smoke registra resultado real ou motivo verificável de impedimento sem usar fixtures como vagas.

## Assumptions
- Aplicação pessoal local de uma pessoa; interface em português; sem contas multiusuário.
- Cidade, idiomas e experiência serão solicitados na interface, sem perguntar aqui nem inferir.
- IA e integrações são evolução posterior, condicionadas à validação do MVP como permite o plano.
- Cancelamento é cooperativo; score experimental não mede chance de contratação.
