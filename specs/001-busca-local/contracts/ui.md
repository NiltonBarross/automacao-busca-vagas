# UI/application contract
Salvar perfil valida competências (nome/domínio) sem preencher conhecimento presumido.
Salvar busca valida termos, modalidades e cidade/UF quando há modalidade local; limites 1..10 páginas,
1..100 vagas, 30..900 segundos. Pesos não negativos, soma 100. Nada inicia coleta ao salvar.
Iniciar recebe cópias serializadas; retorna ID. Rerun nunca dispara busca novamente.
Cancelar apenas marca Event. O trabalhador fecha o browser e persiste estado final.
Resultados consultam run_id e snapshot; lista vazia legítima tem evidência do portal.
CSV usa UTF-8 BOM, ponto e vírgula e aspas; células com prefixos de fórmula são neutralizadas.
Estado/nota pessoal usa job_key, permanece após reavaliação. Nenhuma candidatura automática.

Estado no cadastro define as cidades disponíveis; vazio mantém Cidade desabilitada. Nos critérios,
selecionar estados define Cidades da busca; múltiplas cidades são persistidas como Cidade/UF.
Sugestão usa dados profissionais salvos, limite de 3.000 caracteres, até quatro termos e chave
em ambiente/sessão. Resposta inválida/falha aciona fallback; origem é identificada na interface.
Sugerir termos permite editar e salvar sem coleta. Sugerir e pesquisar inicia uma única execução
e salva uma cópia com sufixo sugerida, mantendo salário/localização/limites/exclusões.
Rerun e navegação horizontal nunca iniciam chamadas IA ou coleta automaticamente.
