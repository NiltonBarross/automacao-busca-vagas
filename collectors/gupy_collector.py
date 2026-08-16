from playwright.sync_api import sync_playwright
import time
from collectors.base_collector import BaseCollector

class GupyCollector(BaseCollector):
    def __init__(self):
        super().__init__()
        self.url_base = "https://portal.gupy.io/job-search/term="

    def buscar_vagas(self, termo_busca: str, localizacao: str = "") -> list:
        print(f"🔍 Iniciando busca na Gupy por: '{termo_busca}'...")
        vagas_coletadas = []
        
        termo_url = termo_busca.replace(" ", "%20")
        url_busca = f"{self.url_base}{termo_url}"
        
        # WHITELIST RESILIENTE (Tolerância a Truncamento):
        # "rio de jan" pega a versão cortada. "- rj" pega a UF no final do card.
        locais_desejados = ["rio de janeiro", "rio de jan", "- rj", "remoto"]
        
        # BLACKLIST: Bloqueia vagas exclusivas PCD
        termos_pcd = ["afirmativa", "exclusiva para pcd", "exclusivo pcd", "exclusiva pcd"]

        with sync_playwright() as p:
            navegador = p.chromium.launch(headless=False) 
            pagina = navegador.new_page()
            
            print(f"🌐 Acessando: {url_busca}")
            pagina.goto(url_busca)
            pagina.wait_for_load_state('networkidle')
            
            pagina_atual = 1

            while True:
                print(f"📄 Vasculhando a página {pagina_atual}...")
                time.sleep(3) 
                
                cartoes_vaga = pagina.locator('a').filter(has=pagina.locator('h3'))
                quantidade_vagas = cartoes_vaga.count()
                
                if quantidade_vagas == 0:
                    print("⚠️ Nenhum cartão de vaga encontrado nesta página.")
                    break
                    
                for i in range(quantidade_vagas):
                    cartao = cartoes_vaga.nth(i)
                    
                    try:
                        titulo = cartao.locator('h3').inner_text()
                        texto_cartao = cartao.inner_text().lower()
                        
                        # 1. Filtro Negativo (Blacklist)
                        if any(termo in texto_cartao for termo in termos_pcd):
                            continue
                        
                        # 2. Filtro Positivo (Whitelist)
                        # Se não tiver 'remoto', '- rj' ou 'rio de jan', a vaga é descartada.
                        if not any(loc in texto_cartao for loc in locais_desejados):
                            continue

                        link = cartao.get_attribute('href')
                        if link and link.startswith('/'):
                            link = f"https://portal.gupy.io{link}"
                            
                        vaga_formatada = self.formatar_vaga(
                            id_vaga=link,
                            titulo=titulo,
                            empresa="Empresa no Cartão", 
                            localizacao="Verificar link", 
                            descricao="Descrição detalhada disponível no link."
                        )
                        vagas_coletadas.append(vaga_formatada)
                        
                    except Exception as e:
                        continue

                botao_proximo = pagina.locator('button[aria-label*="róxima"], button[aria-label*="next"]')
                
                if botao_proximo.count() > 0 and botao_proximo.is_enabled():
                    print("➡️ Indo para a próxima página...")
                    botao_proximo.click()
                    pagina_atual += 1
                    pagina.wait_for_load_state('networkidle')
                else:
                    print("✅ Fim dos resultados ou última página alcançada.")
                    break

            navegador.close()
            
        return vagas_coletadas


        