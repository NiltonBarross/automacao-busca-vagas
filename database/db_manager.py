import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path
from datetime import datetime

class JobDatabase:
    def __init__(self):
        """Inicializa a conexão com o Google Sheets."""
        self.diretorio_atual = Path(__file__).resolve().parent
        self.raiz_projeto = self.diretorio_atual.parent
        self.caminho_credenciais = self.raiz_projeto / "config" / "google_credentials.json"
        
        self.scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        self.nome_planilha = "Job_Hunter_Database"
        self.aba_principal = None
        
        self._conectar()

    def _conectar(self):
        """Estabelece a conexão com a API do Google Sheets."""
        try:
            credenciais = Credentials.from_service_account_file(
                self.caminho_credenciais, scopes=self.scopes
            )
            cliente = gspread.authorize(credenciais)
            planilha = cliente.open(self.nome_planilha)
            self.aba_principal = planilha.sheet1
            print("✅ Conectado ao Google Sheets com sucesso!")
        except Exception as e:
            print(f"❌ Erro ao conectar no banco de dados: {e}")
            raise

    def inicializar_banco(self):
        """Cria o cabeçalho (Schema) da planilha se ela estiver vazia."""
        valores_linha_1 = self.aba_principal.row_values(1)
        
        cabecalho = [
            "ID_Vaga", "Titulo", "Empresa", "Localizacao", 
            "Descricao", "Data_Coleta", "Score_IA", "Analise_IA", "Status"
        ]
        
        if not valores_linha_1:
            print("Planilha vazia. Criando as colunas (Schema)...")
            self.aba_principal.insert_row(cabecalho, index=1)
            self.aba_principal.format('A1:I1', {'textFormat': {'bold': True}})
            print("✅ Estrutura criada com sucesso!")
        else:
            print("✔️ O banco de dados já possui colunas estruturadas.")

    def vaga_existe(self, id_vaga):
        """
        Verifica se o ID_Vaga já está no banco de dados para evitar duplicidade.
        """
        try:
            # Pega todos os valores da coluna 1 (ID_Vaga)
            ids_existentes = self.aba_principal.col_values(1)
            return id_vaga in ids_existentes
        except Exception as e:
            print(f"Erro ao verificar duplicidade: {e}")
            return False

    def salvar_vaga(self, dados_vaga):
        """
        Salva uma nova vaga no banco de dados se não for duplicada.
        Espera receber um dicionário com os dados da vaga.
        """
        id_vaga = dados_vaga.get("ID_Vaga")
        
        if not id_vaga:
            print("❌ Erro: A vaga não possui um ID válido.")
            return False

        if self.vaga_existe(id_vaga):
            print(f"⚠️ Ignorado: A vaga '{id_vaga}' já existe no banco.")
            return False
            
        # Transforma o dicionário em uma lista na ordem exata das colunas
        linha = [
            id_vaga,
            dados_vaga.get("Titulo", ""),
            dados_vaga.get("Empresa", ""),
            dados_vaga.get("Localizacao", ""),
            dados_vaga.get("Descricao", ""),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"), # Gera a data/hora atual
            dados_vaga.get("Score_IA", ""),
            dados_vaga.get("Analise_IA", ""),
            dados_vaga.get("Status", "Coletada")
        ]
        
        try:
            self.aba_principal.append_row(linha)
            print(f"✅ Nova vaga salva: {dados_vaga.get('Titulo')} na {dados_vaga.get('Empresa')}")
            return True
        except Exception as e:
            print(f"❌ Erro ao salvar a vaga: {e}")
            return False

# ==========================================
    # INTEGRAÇÃO COM A INTELIGÊNCIA ARTIFICIAL
    # ==========================================

    def obter_vagas_sem_score(self) -> list:
        """
        Busca todas as vagas que ainda não passaram pelo crivo da IA.
        Retorna uma lista de dicionários, incluindo a linha exata da planilha.
        """
        try:
            # Puxa todos os dados usando a linha 1 como chave do dicionário
            registros = self.aba_principal.get_all_records()
            vagas_pendentes = []
            
            # enumerate cria um contador automático (indice) enquanto percorre a lista
            for indice, vaga in enumerate(registros):
                # Se o campo 'Score_IA' estiver vazio, essa vaga precisa ser avaliada
                if not vaga.get('Score_IA'):
                    # O índice 0 do Python equivale à linha 2 do Sheets
                    vaga['linha_planilha'] = indice + 2 
                    vagas_pendentes.append(vaga)
                    
            print(f"🔍 Encontradas {len(vagas_pendentes)} vagas aguardando análise da IA.")
            return vagas_pendentes
            
        except Exception as e:
            print(f"❌ Erro ao buscar vagas sem score: {e}")
            return []

    def atualizar_score(self, linha: int, score: int, justificativa: str) -> bool:
        """
        Atualiza o Score (Coluna G) e a Análise (Coluna H) em uma única requisição (Lote).
        """
        try:
            # Define o intervalo dinâmico, ex: "G2:H2"
            intervalo = f"G{linha}:H{linha}"
            
            # O gspread exige que os dados para atualização em lote sejam uma matriz (lista de listas)
            valores = [[score, justificativa]]
            
            # Executa a atualização
            self.aba_principal.update(range_name=intervalo, values=valores)
            
            print(f"💾 Score {score} salvo com sucesso na linha {linha}.")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao salvar o score na linha {linha}: {e}")
            return False

# ==========================================
# TESTE DE EXECUÇÃO E INSERÇÃO
# ==========================================
if __name__ == "__main__":
    # 1. Instancia o banco e garante as colunas
    db = JobDatabase()
    db.inicializar_banco()
    
    # 2. Cria uma vaga fictícia para testar a escrita
    vaga_teste = {
        "ID_Vaga": "https://linkedin.com/jobs/12345",
        "Titulo": "Especialista em Customer Success",
        "Empresa": "Tech SaaS Corp",
        "Localizacao": "Remoto",
        "Descricao": "Vaga focada em retenção e CX com uso de dados...",
    }
    
    print("\n--- Testando Inserção ---")
    # Tenta salvar a primeira vez (deve funcionar)
    db.salvar_vaga(vaga_teste)
    
    print("\n--- Testando Duplicidade ---")
    # Tenta salvar exatamente a mesma vaga de novo (deve ser bloqueado pelo sistema)
    db.salvar_vaga(vaga_teste)

    
    