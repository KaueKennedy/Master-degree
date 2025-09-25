import pandapower as pp
import pandapower.networks as nw
import os
import numpy as np

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
            # Barras válidas para o case118 (1 a 118)
            (10, 50, 'Solar_Farm_1', 'solar'),
            (25, 40, 'Wind_Turbine_1', 'eolico'),
            (80, 30, 'Solar_Farm_2', 'solar'),
        ]
    }

    # 2. Configurações do Armazenamento de Energia (Baterias)
    config_storage = {
        'unidades': [
            # Formato: (barra, potencia_mw, capacidade_mwh, nome)
            (12, 20.0, 80.0, 'Bateria_1'),
            (37, 15.0, 60.0, 'Bateria_2'),
            (100, 10.0, 40.0, 'Bateria_3'),
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
    
    # Retorna apenas um dicionário de configurações
    return configs

# ##############################################################################
# FASE 2: SIMULAÇÃO DA REDE ELÉTRICA (EM PYTHON)
# ##############################################################################
def simular_rede(configs):
    """
    Carrega um caso de estudo nativo, adiciona os ativos (DERs e baterias) e
    executa a simulação de fluxo de potência.
    """
    print("\nFASE 2: Iniciando a simulação da rede elétrica...")

    # 1. Carrega o caso de estudo diretamente da biblioteca pandapower
    try:
        print("   -> Carregando 'case118' da biblioteca nativa do pandapower...")
        net = nw.case118()
        print(f"   -> Sucesso! Rede '{net.name}' com {len(net.bus)} barras foi carregada.")
    except Exception as e:
        print(f"   -> ERRO ao carregar o caso de estudo nativo: {e}")
        return None

    # 2. Adiciona os DERs à rede
    print("   -> Adicionando DERs à rede...")
    for der_info in configs['ders']['unidades']:
        barra, capacidade_mw, nome, tipo = der_info
        
        # --- CORREÇÃO IMPORTANTE AQUI ---
        # Pandapower usa indexação base 0. Os nomes das barras são base 1.
        # Encontramos o índice interno da barra.
        bus_index = net.bus[net.bus.name == barra].index
        
        if bus_index.empty:
            print(f"      -> AVISO: Barra {barra} não encontrada. Pulando DER {nome}.")
            continue

        # Remove qualquer gerador existente nesta barra para evitar conflitos
        gens_na_barra = net.gen[net.gen.bus == bus_index[0]].index
        if not gens_na_barra.empty:
            print(f"      -> Removendo {len(gens_na_barra)} gerador(es) existente(s) na barra {barra}.")
            net.gen.drop(gens_na_barra, inplace=True)
            
        pp.create_gen(net, bus=bus_index[0], p_mw=capacidade_mw, name=nome, tags=tipo)

    # 3. Adiciona as Baterias à rede
    print("   -> Adicionando Baterias à rede...")
    for bat_info in configs['storage']['unidades']:
        barra, potencia_mw, capacidade_mwh, nome = bat_info
        bus_index = net.bus[net.bus.name == barra].index

        if bus_index.empty:
            print(f"      -> AVISO: Barra {barra} não encontrada. Pulando Bateria {nome}.")
            continue
            
        pp.create_storage(net, bus=bus_index[0], p_mw=potencia_mw, max_e_mwh=capacidade_mwh, name=nome)
        
    # 4. Executa a simulação de fluxo de potência
    print("   -> Executando a simulação de fluxo de potência (runpp)...")
    try:
        pp.runpp(net)
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

    # FASE 3
    indicadores = calcular_indicadores(net_simulada, configs)
    
    # FASE 4
    apresentar_resultados(indicadores)

if __name__ == "__main__":
    main()