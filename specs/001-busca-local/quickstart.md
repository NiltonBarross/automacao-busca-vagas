# Quickstart validation
1. Executar scripts/start.ps1 após instalar Python 3.11+; preencher um perfil fictício e salvar busca.
2. Fechar/reabrir interface: conferir dados. Busca presencial sem cidade deve falhar.
3. Rodar .venv/Scripts/python.exe -m pytest: testes offline não usam a rede Gupy.
4. Rodar .venv/Scripts/python.exe scripts/smoke.py: uma página, duas vagas, 90 segundos; conferir relatório.
5. Iniciar busca, cancelar e revisar resultado parcial; reencontrar favorita preserva estado.
6. Exportar CSV e conferir texto, link, notas e pendências; sem fórmulas executáveis.
Dados em data/ são privados e ignorados. IA permanece desativada.
