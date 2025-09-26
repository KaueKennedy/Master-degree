import pandapower as pp
import pandapower.networks as nw
import os
import numpy as np
import pickle # Importa a biblioteca para salvar/carregar objetos python
import subprocess
import sys

# ##############################################################################
# FASE 1: CONFIGURAÇÃO DO CENÁRIO
# ##############################################################################
def configurar_cenario():
    """
    Configura e retorna todos os parâmetros para um cenário de simulação.
    """
    print("FASE 1: Configurando o cenário...")

    # 1. Configuracoes das fontes renováveis (DERs)
    config_ders = {
        'unidades': [
            # Formato: (id_da_barra, capacidade_mw, nome, tipo_der)
            # Barras escolhidas do caso de 1354 barras
            (3, 150, 'Solar_Farm_1', 'solar'),
            (4, 200, 'Wind_Turbine_1', 'eolico'),
            (10, 100, 'Solar_Farm_2', 'solar'),
        ]
    }

    # 2. Configurações do Armazenamento de Energia (Baterias)
    config_storage = {
        'unidades': [
            # Formato: (barra, potencia_mw, capacidade_mwh, nome)
            # Pares com os DERs nas mesmas barras
            (3, 75.0, 300.0, 'Bateria_1'),
            (4, 100.0, 400.0, 'Bateria_2'),
            (10, 50.0, 200.0, 'Bateria_3'),
        ]
    }
    
    # 3. Configuracoes do Mecanismo de Compensacao (Net Metering)
    config_compensacao = {
        'modelo': 'Net Metering',
        'remuneracao_credito_mwh': 75.0,
    }

    configs = {
        "ders": config_ders,
        "storage": config_storage,
        "compensacao": config_compensacao
    }
    
    return configs

# ##############################################################################
# FASE 2: SIMULAÇÃO DA REDE ELÉTRICA (EM PYTHON)
# ##############################################################################
def simular_rede(configs):
    """
    Carrega um caso de estudo nativo da biblioteca pandapower, adiciona os ativos
    e executa a simulação de fluxo de potência.
    """
    print("\nFASE 2: Iniciando a simulação da rede elétrica...")

    try:
        print("   -> Carregando 'case1354pegase' da biblioteca nativa do pandapower...")
        net = nw.case1354pegase()
        print(f"   -> Sucesso! Rede '{net.name}' com {len(net.bus)} barras foi carregada.")
        
        with open('rede_inicial.pkl', 'wb') as f:
            pickle.dump(net, f)
        print("   -> Rede inicial salva em 'rede_inicial.pkl'.")

    except Exception as e:
        print(f"   -> ERRO ao carregar o caso de estudo nativo: {e}")
        return None

    print("   -> Adicionando DERs à rede...")
    for der_info in configs['ders']['unidades']:
        barra, capacidade_mw, nome, tipo = der_info
        
        # --- CORREÇÃO DEFINITIVA: Busca a barra pelo NOME e obtém o ÍNDICE ---
        bus_index_query = net.bus[net.bus.name == barra]
        if bus_index_query.empty:
            print(f"      -> AVISO: Barra com nome {barra} não encontrada. Pulando DER {nome}.")
            continue
        bus_index = bus_index_query.index[0]
        # ----------------------------------------------------------------------

        gens_na_barra = net.gen[net.gen.bus == bus_index].index
        if not gens_na_barra.empty:
            print(f"      -> Removendo {len(gens_na_barra)} gerador(es) existente(s) na barra {barra}.")
            net.gen.drop(gens_na_barra, inplace=True)
            
        pp.create_gen(net, bus=bus_index, p_mw=capacidade_mw, name=nome, tags=tipo)

    print("   -> Adicionando Baterias à rede...")
    for bat_info in configs['storage']['unidades']:
        barra, potencia_mw, capacidade_mwh, nome = bat_info
        
        # --- CORREÇÃO DEFINITIVA: Busca a barra pelo NOME e obtém o ÍNDICE ---
        bus_index_query = net.bus[net.bus.name == barra]
        if bus_index_query.empty:
            print(f"      -> AVISO: Barra com nome {barra} não encontrada. Pulando Bateria {nome}.")
            continue
        bus_index = bus_index_query.index[0]
        # ----------------------------------------------------------------------

        pp.create_storage(net, bus=bus_index, p_mw=potencia_mw, max_e_mwh=capacidade_mwh, name=nome)
        
    print("   -> Executando a simulação de fluxo de potência (runpp)...")
    try:
        pp.runpp(net, max_iteration=30)
        print("   -> Simulação concluída com sucesso.")
    except Exception as e:
        print(f"   -> ERRO durante a simulação do fluxo de potência: {e}")
        return None
        
    return net

# ##############################################################################
# FASE 3: CÁLCULO DE INDICADORES
# ##############################################################################
def calcular_indicadores(net, configs):
    """
    Calcula os indicadores de desempenho a partir da rede simulada.
    """
    print("\nFASE 3: Calculando indicadores...")
    indicadores = {}

    if net is None or net.res_bus.empty:
        print("   -> Simulação inválida ou não convergiu. Não é possível calcular indicadores.")
        return indicadores
        
    # Indicador Simples: Perdas Totais de Potência Ativa na Rede
    geracao_total_mw = net.res_gen.p_mw.sum() + net.res_ext_grid.p_mw.sum()
    carga_total_mw = net.res_load.p_mw.sum()
    perdas_totais_mw = geracao_total_mw - carga_total_mw
    
    indicadores['perdas_totais_mw'] = perdas_totais_mw
    
    print(f"   -> Indicador calculado: Perdas Totais = {perdas_totais_mw:.2f} MW")
    
    return indicadores

# ##############################################################################
# FASE 4: APRESENTAÇÃO DOS RESULTADOS
# ##############################################################################
def apresentar_resultados(indicadores):
    """Apresenta os resultados dos indicadores calculados."""
    print("\nFASE 4: Apresentando resultados...")
    
    if not indicadores:
        print("   -> Nenhum indicador para apresentar.")
        return

    print("\n--- Impactos da Inserção de DERs e Baterias ---")
    perdas = indicadores.get('perdas_totais_mw')
    if perdas is not None:
        print(f"  - Perdas Totais na Rede: {perdas:.2f} MW")
    else:
        print("  - Perdas Totais na Rede: N/A")

# ##############################################################################
# FASE 5: ORQUESTRADOR PRINCIPAL
# ##############################################################################
def main():
    """Função principal para executar a simulação completa."""
    
    # FASE 1
    configs = configurar_cenario()

    # FASE 2
    net_simulada = simular_rede(configs)

    print("\n" + "="*50)
    print("Executando o Dashboard de Análise da Rede Base...")
    subprocess.run([sys.executable, "dashboard.py"])
    print("="*50 + "\n")

    # FASE 3
    indicadores = calcular_indicadores(net_simulada, configs)
    
    # FASE 4
    apresentar_resultados(indicadores)

if __name__ == "__main__":
    main()