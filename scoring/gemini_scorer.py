import os
import json
import logging
from typing import TypedDict
from google import genai
from google.genai import types
from google.genai.errors import APIError

logger = logging.getLogger(__name__)

class ScoreResult(TypedDict):
    score: int
    justificativa: str

class GeminiScorer:
    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("⚠️ ALERTA: A variável GEMINI_API_KEY não foi encontrada no ambiente.")
        
        self.client = genai.Client()
        self.modelo_nome: str = 'gemini-2.5-flash'
        
        # Otimização de prompt (redução de tokens, aumento do determinismo e pouca conversa)
        # Técnicas aplicadas: Instruções declarativas concisas, pouca redundância de tokens e pouca margem a variações.
        self.contexto_thiago: str = """Você é um validador de ATS extremamente técnico e rigoroso. Avalie a aderência de vagas ao perfil do candidato Thiago.

PERFIL DO CANDIDATO:
- Objetivos: Analista de Dados, Analista de BI, Analista de Automação (nível Júnior).
- Habilidades: SQL, Python, Excel, Power BI, Google Looker Studio, n8n, APIs REST, Webhooks, Git, GitHub.
- Formação: Análise de Dados e Big Data Science (conclusão em 2026).
- Idioma: Inglês básico.
- Restrição crítica: Vagas de suporte, atendimento, vendas, customer success (CS/CX) devem receber nota < 40, mesmo com experiência anterior. Foco exclusivo em transição para dados/automação.

REGRAS DE PONTUAÇÃO (0-100):
- [90-100]: Match ideal. Dados/BI/Automação Jr que exige Python, SQL, n8n ou Power BI.
- [70-89]: Match muito bom. Dados/BI com requisitos adicionais em aprendizado ou Analista de Processos/Negócios.
- [40-69]: Match parcial. Exige experiência sênior, muitas tecnologias adicionais ou inglês fluente mandatório.
- [0-39]: Baixa aderência. Suporte, CS/CX, vendas ou tecnologias não dominadas (ex. Java, C#).

JSON SCHEMA:
{
  "score": integer,
  "justificativa": "Texto conciso de até 3 linhas focado na aderência técnica, falando diretamente ao Thiago."
}

Exemplo 1 (Sucesso):
Input: {"titulo": "Analista de Dados Júnior", "empresa": "TechCorp", "descricao": "Dashboard Power BI, SQL e Python."}
Output: {"score": 95, "justificativa": "Thiago, esta vaga é perfeita. Ela exige exatamente sua stack principal (Power BI, SQL e Python) em nível Júnior."}

Exemplo 2 (Penalidade):
Input: {"titulo": "Analista de Suporte Técnico", "empresa": "Help S/A", "descricao": "Atendimento ao cliente e suporte de sistemas de CRM."}
Output: {"score": 20, "justificativa": "Thiago, esta vaga deve ser evitada. O foco é suporte e atendimento, o que vai contra o seu objetivo de transição para dados."}

REQUISITO DE SAÍDA: Retorne APENAS o JSON especificado, sem markdown, tags ```json ou qualquer outro texto."""

    def avaliar_vaga(self, titulo: str, empresa: str, descricao: str) -> ScoreResult:
        """Envia os dados da vaga para o Gemini e retorna o score formatado."""
        # Formato de entrada estruturado em JSON para maior consistência e determinismo
        prompt_usuario = json.dumps({
            "titulo": titulo,
            "empresa": empresa,
            "descricao": descricao
        }, ensure_ascii=False)
        
        logger.info("Analisando vaga com o novo SDK do Gemini: %s (%s)...", titulo, empresa)
        
        try:
            resposta = self.client.models.generate_content(
                model=self.modelo_nome,
                contents=prompt_usuario,
                config=types.GenerateContentConfig(
                    system_instruction=self.contexto_thiago,
                    response_mime_type="application/json",
                    temperature=0.0  # Maximiza o determinismo das pontuações e explicações
                )
            )
            
            if not resposta or not resposta.text:
                raise ValueError("Resposta da API do Gemini retornou vazia ou nula.")
                
            dados_estruturados: ScoreResult = json.loads(resposta.text)
            return dados_estruturados
            
        except APIError as e:
            logger.error("Erro específico da API do Gemini: %s", e)
            return {
                "score": 0, 
                "justificativa": "Falha na comunicação com o serviço de inteligência artificial (Gemini)."
            }
        except json.JSONDecodeError as e:
            logger.error("Erro ao decodificar JSON retornado pelo Gemini: %s", e)
            return {
                "score": 0, 
                "justificativa": "A inteligência artificial retornou um formato de dados inválido."
            }
        except Exception as e:
            logger.error("Erro inesperado ao avaliar vaga com o Gemini: %s", e)
            return {
                "score": 0, 
                "justificativa": f"Ocorreu um erro inesperado no processamento da vaga: {e}"
            }

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

    