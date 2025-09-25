import pandapower as pp
# --- CORREÇÃO AQUI: A importação da função mudou de lugar em versões recentes ---
from pandapower.from_matpower import from_matpower
import os
import numpy as np # Importando para uso futuro

# ##############################################################################
# FASE 1: CONFIGURAÇÃO DO CENÁRIO
# Descrição: Defina aqui todos os parâmetros de entrada da simulação.
# ##############################################################################
def configurar_cenario():
    """
    Configura e retorna todos os parâmetros para um cenário de simulação.
    """
    print("FASE 1: Configurando o cenário...")
    
    # Caminho para o arquivo do caso de estudo no formato MATPOWER (.m)
    # Garanta que este caminho está correto em relação a onde você executa o script.
    caminho_arquivo_caso = 'matpower8.1/data/case2746wop_TAMU_Updated.m'

    # 1. Configuracoes das fontes renováveis (DERs)
    config_ders = {
        'unidades': [
            # Formato: (id_da_barra, capacidade_mw, nome, tipo_der)
            (500, 200, 'Solar_Farm_1', 'solar'),
            (120, 150, 'Wind_Turbine_1', 'eolico'),
            (2105, 50, 'Solar_Farm_2', 'solar'),
        ]
    }

    # 2. Configurações do Armazenamento de Energia (Baterias)
    config_storage = {
        'unidades': [
            # Formato: (barra, potencia_mw, capacidade_mwh, nome)
            (100, 100.0, 400.0, 'Bateria_1'),
            (88,  50.0, 200.0, 'Bateria_2'),
            (1542, 75.0, 300.0, 'Bateria_3'),
        ]
    }
    
    # 3. Configuracoes do Mecanismo de Compensacao (Net Metering)
    #    Nesta fase inicial, apenas definimos a tarifa para o cálculo do impacto.
    config_compensacao = {
        'modelo': 'Net Metering',
        'remuneracao_credito_mwh': 75.0,  # Ex: $75 por MWh de energia injetada
    }

    # Agrupa todas as configurações em um único dicionário para facilitar o uso
    configs = {
        "ders": config_ders,
        "storage": config_storage,
        "compensacao": config_compensacao
    }
    
    return caminho_arquivo_caso, configs

# ##############################################################################
# FASE 2: SIMULAÇÃO DA REDE ELÉTRICA (EM PYTHON)
# Descrição: Carrega a rede, adiciona os novos ativos e roda a simulação.
# ##############################################################################
def simular_rede(caminho_arquivo, configs):
    """
    Carrega o caso de estudo, adiciona os ativos (DERs e baterias) e
    executa a simulação de fluxo de potência.
    """
    print("\nFASE 2: Iniciando a simulação da rede elétrica...")

    # 1. Carrega o caso de estudo diretamente do arquivo .m
    try:
        print(f"   -> Lendo o arquivo: {caminho_arquivo}")
        if not os.path.exists(caminho_arquivo):
            print(f"   -> ERRO: Arquivo não encontrado em '{caminho_arquivo}'")
            print(f"   -> Diretório de trabalho atual: {os.getcwd()}")
            return None
        
        # --- CORREÇÃO AQUI: A chamada da função é a mesma, mas a importação mudou ---
        net = from_matpower(caminho_arquivo)
        print(f"   -> Sucesso! Rede '{net.name}' com {len(net.bus)} barras foi carregada.")
    except Exception as e:
        print(f"   -> ERRO ao ler o arquivo do caso de estudo: {e}")
        return None

    # 2. Adiciona os DERs à rede (como geradores estáticos)
    print("   -> Adicionando DERs à rede...")
    for id_der, der_info in enumerate(configs['ders']['unidades']):
        barra, capacidade_mw, nome, tipo = der_info
        pp.create_gen(net, bus=barra, p_mw=capacidade_mw, name=nome, tags=tipo)

    # 3. Adiciona as Baterias à rede
    print("   -> Adicionando Baterias à rede...")
    for id_bat, bat_info in enumerate(configs['storage']['unidades']):
        barra, potencia_mw, capacidade_mwh, nome = bat_info
        pp.create_storage(net, bus=barra, p_mw=potencia_mw, max_e_mwh=capacidade_mwh, name=nome)
        
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
# Descrição: Calcula os indicadores a partir dos resultados da simulação.
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
    # A diferença entre a geração total e a carga total.
    geracao_total_mw = net.res_gen.p_mw.sum() + net.res_ext_grid.p_mw.sum()
    carga_total_mw = net.res_load.p_mw.sum()
    perdas_totais_mw = geracao_total_mw - carga_total_mw
    
    indicadores['perdas_totais_mw'] = perdas_totais_mw
    
    print(f"   -> Indicador calculado: Perdas Totais = {perdas_totais_mw:.2f} MW")
    
    return indicadores

# ##############################################################################
# FASE 4: APRESENTAÇÃO DOS RESULTADOS
# Descrição: Formata e exibe os indicadores calculados.
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
    # Futuramente, outros indicadores serão adicionados aqui

# ##############################################################################
# FASE 5: ORQUESTRADOR PRINCIPAL
# Descrição: Bloco principal que executa todas as fases em ordem.
# ##############################################################################
def main():
    """Função principal para executar a simulação completa."""
    
    # FASE 1: Obter configurações do cenário
    caminho_caso, configs = configurar_cenario()

    # FASE 2: Simular a rede elétrica
    net_simulada = simular_rede(caminho_caso, configs)

    # FASE 3: Calcular indicadores com base nos resultados
    indicadores = calcular_indicadores(net_simulada, configs)
    
    # FASE 4: Apresentar os resultados finais
    apresentar_resultados(indicadores)

if __name__ == "__main__":
    main()