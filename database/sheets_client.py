import gspread
from google.oauth2.service_account import Credentials
from pathlib import Path

# ==========================================
# 1. CONFIGURAÇÃO DE CAMINHOS (PATH RESOLUTION)
# ==========================================
# Descobre dinamicamente onde este arquivo (sheets_client.py) está e sobe duas pastas
# para achar a raiz do projeto.
DIRETORIO_ATUAL = Path(__file__).resolve().parent
RAIZ_DO_PROJETO = DIRETORIO_ATUAL.parent
CAMINHO_CREDENCIAIS = RAIZ_DO_PROJETO / "config" / "google_credentials.json"

# ==========================================
# 2. ESCOPOS DE PERMISSÃO
# ==========================================
# Dizemos ao Google o que nosso robô quer fazer (ver e editar planilhas e drive)
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def testar_conexao():
    """
    Função inicial para testar a comunicação entre o Python e o Google Sheets.
    """
    print("Iniciando teste de conexão com o banco de dados (Google Sheets)...")
    
    try:
        # Passo A: Autenticação
        print(f"Procurando credenciais em: {CAMINHO_CREDENCIAIS}")
        credenciais = Credentials.from_service_account_file(
            CAMINHO_CREDENCIAIS, scopes=SCOPES
        )
        
        # Passo B: Autorização com gspread
        cliente = gspread.authorize(credenciais)
        
        # Passo C: Abrir a Planilha
        nome_planilha = "Job_Hunter_Database"
        print(f"Tentando acessar a planilha: '{nome_planilha}'...")
        planilha = cliente.open(nome_planilha)
        aba_principal = planilha.sheet1
        
        # Passo D: Teste de Escrita (Escrevendo nas células A1 e B1)
        print("Escrevendo dados de teste...")
        aba_principal.update_acell('A1', 'Sistema Job Hunter')
        aba_principal.update_acell('B1', 'Conexão Bem Sucedida!')
        
        print("✅ SUCESSO! A conexão foi estabelecida e os dados foram gravados.")
        print("Vá até o seu Google Drive e abra a planilha para conferir.")

    # Tratamento de erros específicos:
    except FileNotFoundError:
        print("❌ ERRO: Arquivo 'google_credentials.json' não encontrado na pasta config.")
        print("Verifique se o nome do arquivo está exato e se ele está dentro de /config.")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ ERRO: A planilha '{nome_planilha}' não foi encontrada.")
        print("Verifique se você criou a planilha com esse nome exato e se compartilhou com o e-mail do robô.")
    except Exception as erro:
        print(f"❌ ERRO INESPERADO: Ocorreu um erro não mapeado: {erro}")

# Esta linha garante que o teste só rode se executarmos este arquivo diretamente
if __name__ == "__main__":
    testar_conexao()

