import os
import json
from google import genai
from google.genai import types

class GeminiScorer:
    def __init__(self):
        # O novo SDK puxa a variável GEMINI_API_KEY do ambiente automaticamente!
        # Mas mantemos a validação para te avisar caso você esqueça de setar no terminal.
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("⚠️ ALERTA: A variável GEMINI_API_KEY não foi encontrada no terminal.")
        
        # Inicializa o cliente moderno
        self.client = genai.Client()
        self.modelo_nome = 'gemini-2.5-flash'
        
        # O "cérebro" agora entra como uma Instrução de Sistema (System Instruction),
        # isolando a regra de negócios dos dados da vaga.
        self.contexto_thiago = """
        Você é um Tech Recruiter Sênior e Analista de ATS. Sua missão é avaliar a aderência de uma vaga de emprego ao perfil do candidato Thiago.
        
        PERFIL DO CANDIDATO (Thiago Marques Ramalho):
        - Foco de Carreira: Analista de Dados, Analista de BI, Analista de Automação (Nível Júnior).
        - Experiência Prática Atual: Automação de processos eliminando 100% de trabalho manual, uso de Python, n8n, APIs REST, Webhooks e Google Gemini.
        - Hard Skills: SQL, Python, Excel, Power BI, Google Looker Studio, n8n, Git, GitHub.
        - Formação: Análise de Dados e Big Data Science (Senac RJ - 2026).
        - Idioma: Inglês Básico.
        - ATENÇÃO: O candidato quer FAZER TRANSIÇÃO. Vagas de 'Customer Success', 'Customer Experience', 'Atendimento' ou 'Suporte' devem ser severamente penalizadas, mesmo que ele tenha experiência anterior nelas.

        REGRAS DE PONTUAÇÃO (0 a 100):
        - 90 a 100: Match perfeito para Dados, BI ou Automação Júnior. Pede as ferramentas que ele domina (Python, SQL, n8n, Power BI).
        - 70 a 89: Match muito bom. Analista de Negócios/Processos ou vaga de dados que pede algumas coisas que ele ainda está aprendendo.
        - 40 a 69: Match parcial. Pede experiência sênior que ele não tem, ou exige inglês fluente mandatório.
        - 0 a 39: Baixa aderência. Vagas exclusivas de Customer Success, Suporte, Vendas, ou que exijam stacks totalmente diferentes (ex: Java, C#, Front-end puro).

        SAÍDA OBRIGATÓRIA:
        Você deve retornar EXCLUSIVAMENTE um objeto JSON válido, sem marcações markdown, com as chaves:
        {
            "score": <numero_inteiro>,
            "justificativa": "<texto curto de até 3 linhas explicando o motivo da nota, falando diretamente para o Thiago>"
        }
        """

    def avaliar_vaga(self, titulo: str, empresa: str, descricao: str) -> dict:
        """Envia os dados da vaga para o Gemini e retorna o score formatado."""
        prompt_usuario = f"TÍTULO: {titulo}\nEMPRESA: {empresa}\nDESCRIÇÃO: {descricao}"
        
        try:
            print(f"🧠 Analisando vaga com o novo SDK do Gemini: {titulo} ({empresa})...")
            
            # A chamada moderna da API
            resposta = self.client.models.generate_content(
                model=self.modelo_nome,
                contents=prompt_usuario,
                config=types.GenerateContentConfig(
                    system_instruction=self.contexto_thiago,
                    response_mime_type="application/json"
                )
            )
            
            # Converte a string JSON que o Gemini devolveu em um dicionário Python
            dados_estruturados = json.loads(resposta.text)
            return dados_estruturados
            
        except Exception as e:
            print(f"❌ Erro ao avaliar vaga com o Gemini: {e}")
            return {"score": 0, "justificativa": f"Erro na análise via API: {e}"}

# ==========================================
# BLOCO DE TESTE ISOLADO
# ==========================================
if __name__ == "__main__":
    vaga_teste = {
        "titulo": "Analista de Dados Júnior",
        "empresa": "Tech DataCorp",
        "descricao": "Buscamos um analista para criar dashboards no Power BI e automatizar rotinas de extração de dados com Python e SQL. Modelo remoto. Desejável conhecimento em APIs."
    }
    
    scorer = GeminiScorer()
    resultado = scorer.avaliar_vaga(
        titulo=vaga_teste["titulo"],
        empresa=vaga_teste["empresa"],
        descricao=vaga_teste["descricao"]
    )
    
    print("\n--- 🎯 RESULTADO DA IA ---")
    print(f"Score: {resultado.get('score')}/100")
    print(f"Justificativa: {resultado.get('justificativa')}")

    