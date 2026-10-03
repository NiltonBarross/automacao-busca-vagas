# Busca Vagas Constitution

## Core Principles

### I. Configuração privada e editável
Perfil, competências e critérios MUST ficar no armazenamento local e ser editáveis na interface.
Dados pessoais, bancos, credenciais e exportações MUST ser ignorados pelo Git e CodeGraph.

### II. Funcionamento local e camadas independentes
O MVP MUST funcionar no Windows sem serviços pagos ou credenciais Google. Domínio e aplicação
MUST ser independentes de Streamlit e IA. IA MUST permanecer desligada no MVP.

### III. Evidências e incertezas
Avaliações MUST citar anúncio e perfil declarado. Ausências MUST gerar pendências.
Score MUST ordenar revisão sem estimar contratação. Pesos experimentais MUST ser identificados.

### IV. Falhas observáveis e resultados preservados
Coleta MUST ter limites, timeouts, deduplicação e detecção de repetição. Bloqueios MUST encerrar
acesso sem contorno. Cancelamento e falhas MUST preservar resultados já gravados.

### V. Contratos verificados e créditos preservados
Mudanças MUST validar coleta, avaliação e persistência com fixtures fictícias. Smoke tests reais
MUST ser separados dos testes offline. Licença MIT e créditos MUST ser mantidos.

## Constraints
Sem candidaturas automáticas. Não inferir atributos pessoais ou salários. Não apresentar fixtures
como vagas reais. Endpoints internos não constituem API pública. Integrações futuras MUST ser
opcionais e isoladas. O plano local com contexto pessoal MUST permanecer fora de publicação.

## Development Workflow
Usar inicialização oficial e templates resolvidos do Spec Kit. Manter spec, plan, tasks e evidências
por entrega. CodeGraph MUST ser reconstruído após mudanças relevantes e conferido no código.
Os testes dos comportamentos alterados MUST passar antes da entrega.

## Governance
Alterações exigem motivo documentado, versão semântica e revisão de impacto. Instruções explícitas
do usuário prevalecem. Cada plano MUST verificar os princípios antes e depois do desenho técnico.

**Version**: 1.0.0 | **Ratified**: 2026-10-02 | **Last Amended**: 2026-10-02
