import time
from database.db_manager import JobDatabase
from collectors.gupy_collector import GupyCollector
from scoring.gemini_scorer import GeminiScorer

def orquestrar_sistema():
    print("🚀 Iniciando o Job Hunter AI (Coleta + Scoring)...\n")
    
    # ==========================================
    # 1. INICIALIZAÇÃO DOS MÓDULOS
    # ==========================================
    print("Carregando módulos do sistema...")
    db = JobDatabase()
    db.inicializar_banco()
    
    coletor = GupyCollector()
    
    # Tratamento de erro elegante caso a chave da IA não esteja no terminal
    try:
        ia_scorer = GeminiScorer()
    except ValueError as e:
        print(f"\n⚠️ Módulo de IA desativado: {e}")
        ia_scorer = None

    # ==========================================
    # 2. FASE DE COLETA (GUPY)
    # ==========================================
    print("\n" + "="*40)
    print("🔍 FASE 1: COLETA DE VAGAS")
    print("="*40)
    
    # Usando o nosso termo validado
    termo = "Customer Success"
    vagas_encontradas = coletor.buscar_vagas(termo_busca=termo)
    
    vagas_salvas = 0
    for vaga in vagas_encontradas:
        # Se salvar_vaga retornar True, a vaga era nova
        if db.salvar_vaga(vaga):
            vagas_salvas += 1
            
    print(f"\n✅ Fase 1 concluída. {vagas_salvas} novas vagas salvas no banco.")

    # ==========================================
    # 3. FASE DE INTELIGÊNCIA (SCORING)
    # ==========================================
    print("\n" + "="*40)
    print("🧠 FASE 2: ANÁLISE DE INTELIGÊNCIA ARTIFICIAL")
    print("="*40)
    
    if not ia_scorer:
        print("Pulando a fase de Scoring pois a IA não foi configurada.")
        return

    # O maestro pergunta ao banco o que falta analisar
    vagas_pendentes = db.obter_vagas_sem_score()
    
    if not vagas_pendentes:
        print("✨ Nenhuma vaga pendente de análise no momento.")
    else:
        print(f"Iniciando análise de {len(vagas_pendentes)} vagas pendentes...\n")
        
        for vaga in vagas_pendentes:
            linha = vaga.get('linha_planilha')
            titulo = vaga.get('Titulo', 'Sem Título')
            empresa = vaga.get('Empresa', 'Sem Empresa')
            descricao = vaga.get('Descricao', 'Sem Descrição')
            
            # 1. A IA pensa e devolve o JSON
            resultado_ia = ia_scorer.avaliar_vaga(titulo, empresa, descricao)
            score = resultado_ia.get('score', 0)
            justificativa = resultado_ia.get('justificativa', "Erro na análise.")
            
            # 2. O Banco anota na planilha
            db.atualizar_score(linha, score, justificativa)
            
            # 3. Respiro do servidor (Boas práticas de chamadas de API)
            time.sleep(20)

    print("\n" + "="*40)
    print("🎉 FLUXO DO JOB HUNTER AI FINALIZADO COM SUCESSO!")
    print("="*40)

if __name__ == "__main__":
    orquestrar_sistema()

