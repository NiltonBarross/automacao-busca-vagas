# Data model
- Profile: nome opcional, formação, experiências, competências com domínio, idiomas, anos opcionais,
  senioridades confirmadas, complementos; versão monotônica e created_at.
  Cadastro Usuário: email/telefone, cidade/UF, LinkedIn/portfólio, título/resumo, certificações,
  texto e nome original do currículo. Campos novos têm defaults para compatibilidade com versões antigas.
  Domínio de competência pode ser não informado e gera pendência de confirmação.
- SearchConfig: nome/termos/sinônimos, modalidades/senioridades, cidades Cidade/UF, mínimo opcional,
  salário ausente (pendência ou excluir), filtros localização/salário (obrigatório ou preferência),
  evitar obrigatório/preferência, afirmativa (sinalizar ou excluir), limites e pesos somando 100.
- SearchRun: ID, perfil e critérios snapshot, status, etapa, contadores e lista de erros.
  running → completed | partial | failed | cancelled | limited | interrupted.
- Job: fonte, source_id opcional, chave canônica única, URL, título, empresa/cidade/modalidade,
  senioridade, descrição/requisitos/texto bruto, salário mensal BRL explícito opcional, first/last_seen.
- RunJob: PK(run_id, job_key), termos únicos, snapshot do anúncio; FK run/job.
- Evaluation: persistida com RunJob, versão rules-v1, perfil snapshot, evidências, cobertura e pendências.
- UserJobState: PK job_key, estado nova/revisar/favorita/candidatura registrada/descartada e notas.
Cada conexão habilita foreign_keys; transações atômicas por vaga. Reencontro mantém first_seen e estado.
