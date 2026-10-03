# UI/application contract
Salvar perfil valida competências (nome/domínio) sem preencher conhecimento presumido.
Salvar busca valida termos, modalidades e cidade/UF quando há modalidade local; limites 1..10 páginas,
1..100 vagas, 30..900 segundos. Pesos não negativos, soma 100. Nada inicia coleta ao salvar.
Iniciar recebe cópias serializadas; retorna ID. Rerun nunca dispara busca novamente.
Cancelar apenas marca Event. O trabalhador fecha o browser e persiste estado final.
Resultados consultam run_id e snapshot; lista vazia legítima tem evidência do portal.
CSV usa UTF-8 BOM, ponto e vírgula e aspas; células com prefixos de fórmula são neutralizadas.
Estado/nota pessoal usa job_key, permanece após reavaliação. Nenhuma candidatura automática.
