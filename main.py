import matlab.engine
import scipy.io
import sys
import os
import numpy as np

# --- Configuracao do Mecanismo de Compensacao e Indicadores ---

# 1. Configuracoes dos Recursos Energeticos Distribuidos (DERs)
config_ders = {
    'tipos': ['solar', 'eolico'],  # Tipos de DERs a serem considerados
    # Onde os DERs estao e como serao espalhados na rede.
    # Cada entrada eh uma tupla: (numero_da_barra, capacidade_MW, tipo_der)
    'localizacao': [
        (10, 5, 'solar'),   # Ex: 5 MW de geracao solar na barra 10
        (25, 10, 'eolico'),  # Ex: 10 MW de geracao eolica na barra 25
        (50, 3, 'solar'),   # Ex: 3 MW de geracao solar na barra 50
    ],
    'investimento_por_kw': {     # Custo de investimento (CAPEX)
        'solar': 1200,  # Ex: $1200 por kW
        'eolico': 1500, # Ex: $1500 por kW
    },
    'custo_operacional_por_kwh': { # Custo operacional (OPEX)
        'solar': 0.01,  # Ex: $0.01 por kWh
        'eolico': 0.02, # Ex: $0.02 por kWh
    }
}

# 2. Configuracoes do Mecanismo de Compensacao
config_compensacao = {
    'remuneracao_por_kwh': 0.10,  # Ex: $0.10 por kWh injetado na rede
}

# 3. Configuracoes Economicas Gerais
config_economicas = {
    'custo_energia_consumidor_por_kwh': 0.15,  # Ex: $0.15 por kWh para o consumidor final
    'custo_geradores_convencionais_por_kwh': 0.05, # Custo medio de geracao convencional
}

def apresentar_resultados(dados_carregados):
    """Funcao para apresentar os resultados dos indicadores em formato de tabela."""
    if 'indicadores' not in dados_carregados:
        print("Indicadores nao encontrados no arquivo de resultados do MATLAB.")
        return

    indicadores = dados_carregados['indicadores'][0, 0]
    
    output_lines = []
    output_lines.append("--- Resultados dos Indicadores da Simulacao ---")
    output_lines.append("\n--- Indicadores Tecnicos ---")
    
    # Tensao nas barras (min, max, media)
    tensao_min = indicadores['tensao_min'][0][0]
    tensao_max = indicadores['tensao_max'][0][0]
    tensao_media = indicadores['tensao_media'][0][0]
    output_lines.append(f"Niveis de Tensao nas Barras (p.u.): Min={tensao_min:.4f}, Max={tensao_max:.4f}, Media={tensao_media:.4f}")

    # Congestionamento das linhas
    congestionamento = indicadores['congestionamento_percent'][0][0]
    output_lines.append(f"Congestionamento das Linhas de Transmissao: {congestionamento:.2f}% das linhas operando no limite.")

    # Perdas de potencia
    perdas_mw = indicadores['perdas_mw'][0][0]
    perdas_mvar = indicadores['perdas_mvar'][0][0]
    output_lines.append(f"Perdas de Potencia no Rede: {perdas_mw:.4f} MW (Ativa), {perdas_mvar:.4f} MVar (Reativa)")

    # Fator de utilizacao dos geradores convencionais
    fator_utilizacao = indicadores['fator_utilizacao_convencional'][0][0]
    output_lines.append(f"Fator de Utilizacao dos Geradores Convencionais: {fator_utilizacao:.2f}%")

    # Utilizacao de fontes renovaveis
    total_demanda = indicadores['total_demanda_mw'][0][0]
    total_gerado_renovavel = indicadores['total_gerado_renovavel_mw'][0][0]
    penetracao_renovavel = (total_gerado_renovavel / total_demanda) * 100 if total_demanda > 0 else 0
    output_lines.append(f"Utilizacao de Fontes Renovaveis: {penetracao_renovavel:.2f}% da demanda total.")
    
    output_lines.append("\n--- Indicadores Economicos ---")
    custo_total = indicadores['custo_total_sistema'][0][0]
    output_lines.append(f"Custo Total do Sistema: ${custo_total:,.2f}")
    
    rentabilidade_produtores = indicadores['rentabilidade_produtores'][0][0]
    output_lines.append(f"Rentabilidade para os Produtores Autonomos (Receita): ${rentabilidade_produtores:,.2f}")
    
    impacto_consumidores = indicadores['impacto_fatura_consumidores'][0][0]
    output_lines.append(f"Impacto na Fatura dos Consumidores (Custo Total): ${impacto_consumidores:,.2f}")

    output_lines.append("\n--- Indicadores Sociais e Ambientais (Exemplos) ---")
    output_lines.append("Distribuicao da Riqueza Energetica: (a ser implementado com base em dados socioeconomicos)")
    output_lines.append("Incentivo para Fontes de Energia Limpa: (a ser implementado com base em politicas)")
    output_lines.append("Resiliencia Local: (a ser implementado com base em topologia e cenarios de falha)")
    
    # Imprimir no console
    for line in output_lines:
        print(line)
        
    # Salvar em arquivo
    with open('resultados_indicadores.txt', 'w') as f:
        for line in output_lines:
            f.write(line + '\n')
    print("\nResultados dos indicadores salvos em 'resultados_indicadores.txt'")


print("Iniciando sessao MATLAB...")
try:
    eng = matlab.engine.start_matlab()
except Exception as e:
    print(f"Erro ao iniciar o MATLAB: {e}")
    sys.exit()

# Adiciona o Matpower ao path do MATLAB
try:
    matpower_path = eng.fullfile(r'C:\Users\KKCOD\OneDrive - Université Laval\Recherche\codes\matpower8.1', nargout=1)
    eng.addpath(eng.genpath(matpower_path), nargout=0)
except Exception as e:
    print(f"Erro ao adicionar o MATPOWER ao path do MATLAB: {e}")
    eng.quit()
    sys.exit()

# Passa as configuracoes do Python para o MATLAB
try:
    eng.workspace['config_ders'] = matlab.double([item for sublist in config_ders['localizacao'] for item in (sublist[0], sublist[1])])
    eng.workspace['config_compensacao_remuneracao'] = config_compensacao['remuneracao_por_kwh']
    eng.workspace['config_custo_consumidor'] = config_economicas['custo_energia_consumidor_por_kwh']
    eng.workspace['config_custo_convencional'] = config_economicas['custo_geradores_convencionais_por_kwh']
except Exception as e:
    print(f"Erro ao passar configuracoes para o MATLAB: {e}")
    eng.quit()
    sys.exit()

# Comando MATLAB para rodar o caso de estudo e salvar o resultado
comando_matlab = """
    mpc = pglib_opf_case73_ieee_rts();
    
    % Adicionar DERs ao caso de estudo
    num_ders = length(config_ders) / 2;
    for i = 1:num_ders
        bus_idx = config_ders(2*i-1);
        capacity_mw = config_ders(2*i);
        
        % Encontra o indice do gerador a ser adicionado
        new_gen_idx = size(mpc.gen, 1) + 1;
        
        % Adiciona nova linha em mpc.gen
        % [bus, Pg, Qg, Qmax, Qmin, Vg, mBase, status, Pmax, Pmin, ...]
        mpc.gen(new_gen_idx, :) = [bus_idx, capacity_mw, 0, 100, -100, 1.0, 100, 1, capacity_mw, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
        
        % Adiciona custo para o novo gerador (supondo custo quadratico simples)
        % [MODEL, STARTUP, SHUTDOWN, NCOST, COST]
        mpc.gencost(new_gen_idx, :) = [2, 0, 0, 3, 0, 0, 0]; % Custo zero para simplificar, a logica de remuneracao esta fora do OPF
    end
    
    resultados = runpf(mpc);
    
    % --- Calculo dos Indicadores ---
    indicadores = struct();
    
    % Indicadores Tecnicos
    indicadores.tensao_min = min(resultados.bus(:, 8)); % VM
    indicadores.tensao_max = max(resultados.bus(:, 8)); % VM
    indicadores.tensao_media = mean(resultados.bus(:, 8)); % VM
    
    flow_limit = resultados.branch(:, 6); % RATE_A
    flow_abs = max(abs(resultados.branch(:, 14)), abs(resultados.branch(:, 16))); % PF e PT
    congestionadas = flow_abs >= flow_limit & flow_limit > 0;
    indicadores.congestionamento_percent = (sum(congestionadas) / size(resultados.branch, 1)) * 100;
    
    [loss_mw, loss_mvar] = get_losses(resultados);
    indicadores.perdas_mw = sum(loss_mw);
    indicadores.perdas_mvar = sum(loss_mvar);
    
    conv_gens = mpc.gen(1:end-num_ders, :);
    total_cap_conv = sum(conv_gens(:, 9)); % Pmax
    total_gen_conv = sum(resultados.gen(1:end-num_ders, 2)); % Pg
    indicadores.fator_utilizacao_convencional = (total_gen_conv / total_cap_conv) * 100;
    
    indicadores.total_demanda_mw = sum(resultados.bus(:, 3)); % PD
    indicadores.total_gerado_renovavel_mw = sum(resultados.gen(end-num_ders+1:end, 2)); % Pg dos DERs
    
    % Indicadores Economicos
    custo_geracao_conv = total_gen_conv * 1000 * config_custo_convencional; % Convertendo MW para kW
    receita_ders = indicadores.total_gerado_renovavel_mw * 1000 * config_compensacao_remuneracao;
    indicadores.custo_total_sistema = custo_geracao_conv - receita_ders;
    indicadores.rentabilidade_produtores = receita_ders;
    indicadores.impacto_fatura_consumidores = indicadores.total_demanda_mw * 1000 * config_custo_consumidor;

    save('resultados.mat', 'resultados', 'indicadores');
"""

print("Executando simulação no MATLAB...")
try:
    eng.eval(comando_matlab, nargout=0)
    print("Simulacao concluida no MATLAB. Arquivo 'resultados.mat' gerado com indicadores.")
except Exception as e:
    print(f"Erro durante a execucao do comando MATLAB: {e}")
    eng.quit()
    sys.exit()

print("Tentando carregar os resultados no Python...")
try:
    dados_carregados = scipy.io.loadmat('resultados.mat')
    
    if 'resultados' in dados_carregados:
        print("Sucesso! A estrutura 'resultados' foi encontrada no arquivo.")
        
        resultados_data = dados_carregados['resultados']
        bus_matrix = resultados_data['bus'][0,0]
        num_buses = bus_matrix.shape[0]
        
        print(f"O caso de estudo contém {num_buses} barras.")
        
        # Apresentar os resultados dos indicadores
        apresentar_resultados(dados_carregados)
        
        print("O Python agora pode trabalhar com os dados sem problemas.")
    else:
        print("Falha: A estrutura 'resultados' nao foi encontrada no arquivo.")

except FileNotFoundError:
    print("Falha: O arquivo 'resultados.mat' nao foi encontrado.")
except Exception as e:
    print(f"Falha: Erro ao carregar o arquivo .mat. Detalhes: {e}")

finally:
    eng.quit()
    print("\nSessao MATLAB encerrada.")