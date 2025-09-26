import pandas as pd
import pickle
import os

# ##############################################################################
# FASE DE ANÁLISE DA REDE
# ##############################################################################
def analisar_rede():
    """
    Carrega o estado inicial da rede salvo pelo main.py e exibe um
    dashboard com as principais características do sistema.
    """
    print("--- Dashboard de Análise da Rede Elétrica ---")
    
    # 1. Carrega o arquivo da rede salvo pelo main.py
    nome_arquivo = 'rede_inicial.pkl'
    try:
        with open(nome_arquivo, 'rb') as f:
            net = pickle.load(f)
        print(f"\nSucesso! Arquivo '{nome_arquivo}' carregado.")
        print(f"Analisando a rede: {net.name} ({len(net.bus)} barras)\n")
    except FileNotFoundError:
        print(f"\nERRO: Arquivo '{nome_arquivo}' não encontrado.")
        print("   -> Por favor, execute o script 'main.py' para gerar o arquivo.")
        return
    except Exception as e:
        print(f"\nERRO ao carregar o arquivo da rede: {e}")
        return

    # 2. Análise da Geração Existente
    print("--- GERAÇÃO CONVENCIONAL (ESTADO BASE) ---")
    potencia_geradores_convencionais = net.gen.p_mw.sum()
    
    # --- CORREÇÃO AQUI: Verifica se existem conexões externas antes de somar ---
    potencia_conexoes_externas = 0.0
    if not net.ext_grid.empty and 'p_mw' in net.ext_grid.columns:
        potencia_conexoes_externas = net.ext_grid.p_mw.sum()
    # --------------------------------------------------------------------

    potencia_total_convencional = potencia_geradores_convencionais + potencia_conexoes_externas
    
    print(f"Potência Total Instalada: {potencia_total_convencional:,.2f} MW")
    print(f"  -> Geradores Internos: {potencia_geradores_convencionais:,.2f} MW ({len(net.gen)} unidades)")
    print(f"  -> Conexões Externas: {potencia_conexoes_externas:,.2f} MW ({len(net.ext_grid)} unidades)")
    
    if not net.gen.empty:
        net.gen['tipo_fonte'] = 'Convencional'
        soma_por_tipo = net.gen.groupby('tipo_fonte').p_mw.sum()
        print("\nSoma de potência por tipo de fonte:")
        print(soma_por_tipo.to_string())

    # 3. Análise das Cargas (Consumidores)
    print("\n--- CARGAS (CONSUMIDORES) ---")
    cargas = net.load
    potencia_total_cargas = cargas.p_mw.sum()
    
    limiar_cidade_grande = cargas.p_mw.quantile(0.80)
    
    cidades_grandes = cargas[cargas.p_mw >= limiar_cidade_grande]
    cidades_interior = cargas[cargas.p_mw < limiar_cidade_grande]
    
    print(f"Potência Total Demandada: {potencia_total_cargas:,.2f} MW")
    print(f"Número Total de Cargas: {len(cargas)}")
    print(f"\nClassificação das Cargas (Limiar > {limiar_cidade_grande:.2f} MW):")
    print(f"  -> Grandes Centros: {len(cidades_grandes)} cargas, somando {cidades_grandes.p_mw.sum():,.2f} MW")
    print(f"  -> Cidades de Interior: {len(cidades_interior)} cargas, somando {cidades_interior.p_mw.sum():,.2f} MW")

# ##############################################################################
# ORQUESTRADOR DO DASHBOARD
# ##############################################################################
if __name__ == "__main__":
    analisar_rede()