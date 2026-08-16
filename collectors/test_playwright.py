from playwright.sync_api import sync_playwright
from base_collector import BaseCollector

# Nossa classe de teste HERDA as regras do BaseCollector
class TesteNavegador(BaseCollector):
    
    # Somos obrigados a criar esta função, senão o BaseCollector gera erro
    def buscar_vagas(self, termo_busca: str, localizacao: str):
        print("Iniciando os motores do Playwright...")
        
        # Inicia o gerenciador de contexto do Playwright
        with sync_playwright() as p:
            # Lança o navegador Chromium. 
            # headless=False faz o navegador aparecer fisicamente na sua tela!
            print("Abrindo o navegador...")
            navegador = p.chromium.launch(headless=False)
            
            pagina = navegador.new_page()
            
            print("Acessando o site de exemplo...")
            pagina.goto("https://example.com")
            
            # Extrai uma informação real da internet (o título da página)
            titulo_pagina = pagina.title()
            print(f"Sucesso! Título capturado: '{titulo_pagina}'")
            
            # Fecha o navegador para não consumir memória
            navegador.close()

            # Usa o método herdado da classe base para formatar o dado!
            vaga_falsa = self.formatar_vaga(
                id_vaga="id-teste-001",
                titulo=titulo_pagina,
                empresa="Playwright Inc.",
                localizacao=localizacao,
                descricao="Teste de infraestrutura do sistema de coleta."
            )
            
            return [vaga_falsa]

# ==========================================
# EXECUÇÃO DO TESTE
# ==========================================
if __name__ == "__main__":
    robo = TesteNavegador()
    resultado = robo.buscar_vagas(termo_busca="Teste", localizacao="Brasil")
    
    print("\n--- Resultado Formatado pela Classe Base ---")
    print(resultado)

