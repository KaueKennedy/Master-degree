import matlab.engine
import scipy.io
import sys
import os
import numpy as np
import pyomo.environ as pyo
from pyomo.opt import SolverFactory

# ##############################################################################
# FASE 1: CONFIGURAÇÃO DO CENÁRIO E OTIMIZAÇÃO DO MECANISMO DE COMPENSAÇÃO
# Descrição: Define os parâmetros, otimiza o mecanismo de compensação (NEM)
#            usando Pyomo/CPLEX e cria o arquivo de entrada para o MATLAB.
# ##############################################################################
def preparar_cenario_e_criar_arquivo():
    """
    Configura os parâmetros, executa a otimização do mecanismo de compensação
    e cria o arquivo 'cenario.mat' para a simulação principal.
    """
    print("FASE 1: Configurando o cenário e o mecanismo de compensação...")

    # --------------------------------------------------------------------------
    # 1.A. DEFINIÇÃO DOS ATIVOS E PARÂMETROS
    # --------------------------------------------------------------------------
    
    # Nome da FUNÇÃO do caso de estudo que o MATLAB irá chamar
    nome_caso_matlab = 'case2746wop_TAMU_Updated'

    # Configuracoes das fontes renováveis (DERs)
    config_ders = {
        'unidades': [
            # Formato: (numero_da_barra, capacidade_MW, 'tipo_der')
            (500, 200, 'solar'),
            (120, 150, 'eolico'),
            (2105, 50, 'solar'),
        ]
    }

    # Configurações do Armazenamento de Energia (Baterias)
    config_storage = {
        'unidades': [
            # Formato: (barra, Potencia_MW, Capacidade_MWh, eff_carga, eff_descarga, soc_inicial)
            (500, 100.0, 400.0, 0.95, 0.95, 0.5),
            (120,  50.0, 200.0, 0.92, 0.92, 0.5),
            (2105, 75.0, 300.0, 0.94, 0.94, 0.5),
        ]
    }

    # Configuracoes Economicas e Perfis de Operação (para a otimização)
    # (Dados de exemplo para um dia, divididos em 24 horas)
    config_economicas = {
        'preco_compra_energia_grid_mwh': np.array( # Preço varia ao longo do dia
            [60, 58, 55, 54, 55, 62, 70, 85, 95, 100, 105, 100,
             98, 95, 96, 102, 110, 120, 115, 105, 95, 85, 75, 65]
        ),
        'custo_operacional_ders_mwh': {'solar': 2.0, 'eolico': 5.0 },
        'perfil_carga_mw': np.array([
            15000, 14500, 14000, 13800, 13900, 14200, 15000, 16500, 17500, 18000, 18200, 18300,
            18100, 18000, 17800, 17900, 18500, 19500, 20000, 19800, 19000, 18000, 17000, 16000
        ]),
        'perfil_solar_fator': np.array([
            0, 0, 0, 0, 0, 0.1, 0.3, 0.5, 0.7, 0.85, 0.95, 1.0,
            1.0, 0.95, 0.85, 0.7, 0.5, 0.2, 0, 0, 0, 0, 0, 0
        ]),
        'perfil_eolico_fator': np.array([
            0.4, 0.45, 0.5, 0.55, 0.6, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3,
            0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.55, 0.5, 0.45, 0.4, 0.4
        ])
    }
    
    # Parametros do Mecanismo de Compensação (Net Energy Metering - NEM)
    config_compensacao = {
        # No NEM, a remuneração é o próprio preço da energia que se evita comprar.
        'remuneracao_credito_mwh': config_economicas['preco_compra_energia_grid_mwh']
    }

    # --------------------------------------------------------------------------
    # 1.B. MODELO DE OTIMIZAÇÃO DO MECANISMO (Pyomo + CPLEX)
    # --------------------------------------------------------------------------
    print("   -> Construindo o modelo de otimização do mecanismo de compensação...")
    model = pyo.ConcreteModel(name="Mecanismo_NEM")

    # Sets
    model.T = pyo.Set(initialize=range(24))
    model.DERS = pyo.Set(initialize=range(len(config_ders['unidades'])))
    model.BESS = pyo.Set(initialize=range(len(config_storage['unidades'])))

    # Variáveis de Decisão
    model.p_grid = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.p_ders = pyo.Var(model.DERS, model.T, domain=pyo.NonNegativeReals)
    model.p_charge = pyo.Var(model.BESS, model.T, domain=pyo.NonNegativeReals)
    model.p_discharge = pyo.Var(model.BESS, model.T, domain=pyo.NonNegativeReals)
    model.soc = pyo.Var(model.BESS, model.T, bounds=(0, None))

    # Função Objetivo: Minimizar o custo total de operação
    def objective_rule(m):
        custo_grid = sum(m.p_grid[t] * config_economicas['preco_compra_energia_grid_mwh'][t] for t in m.T)
        custo_ders_op = sum(m.p_ders[d, t] * config_economicas['custo_operacional_ders_mwh'][config_ders['unidades'][d][2]] for d in m.DERS for t in m.T)
        return custo_grid + custo_ders_op
    model.objective = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    # Restrições
    def power_balance_rule(m, t):
        geracao = m.p_grid[t] + sum(m.p_ders[d, t] for d in m.DERS) + sum(m.p_discharge[b, t] for b in m.BESS)
        carga = config_economicas['perfil_carga_mw'][t] + sum(m.p_charge[b, t] for b in m.BESS)
        return geracao == carga
    model.power_balance = pyo.Constraint(model.T, rule=power_balance_rule)

    def der_capacity_rule(m, d, t):
        tipo_der = config_ders['unidades'][d][2]
        fator = config_economicas[f'perfil_{tipo_der}_fator'][t]
        return m.p_ders[d, t] <= config_ders['unidades'][d][1] * fator
    model.der_capacity = pyo.Constraint(model.DERS, model.T, rule=der_capacity_rule)
    
    def storage_soc_rule(m, b, t):
        unidade = config_storage['unidades'][b]
        if t == 0: soc_anterior = unidade[5] * unidade[2]
        else:      soc_anterior = m.soc[b, t-1]
        return m.soc[b, t] == soc_anterior + m.p_charge[b, t] * unidade[3] - m.p_discharge[b, t] / unidade[4]
    model.storage_soc = pyo.Constraint(model.BESS, model.T, rule=storage_soc_rule)
    
    def storage_soc_max_rule(m, b, t): return m.soc[b, t] <= config_storage['unidades'][b][2]
    model.storage_soc_max = pyo.Constraint(model.BESS, model.T, rule=storage_soc_max_rule)
    
    def storage_power_charge_rule(m, b, t): return m.p_charge[b, t] <= config_storage['unidades'][b][1]
    model.storage_power_charge = pyo.Constraint(model.BESS, model.T, rule=storage_power_charge_rule)

    def storage_power_discharge_rule(m, b, t): return m.p_discharge[b, t] <= config_storage['unidades'][b][1]
    model.storage_power_discharge = pyo.Constraint(model.BESS, model.T, rule=storage_power_discharge_rule)

    # --- Resolução do Modelo ---
    print("   -> Resolvendo o modelo de otimização com CPLEX...")
    try:
        solver = SolverFactory('cplex')
        results = solver.solve(model, tee=False)
        if results.solver.termination_condition == pyo.TerminationCondition.optimal:
            print("   -> Otimização concluída com sucesso!")
            custo_total_otimizado = pyo.value(model.objective)
            print(f"   -> Custo diário total da rede (otimizado pelo NEM): ${custo_total_otimizado:,.2f}")
            config_compensacao['custo_total_otimizado'] = custo_total_otimizado
        else:
            print(f"   -> ERRO: Otimização falhou. Condição: {results.solver.termination_condition}")
            return None # Retorna None em caso de falha na otimização
    except Exception as e:
        print(f"   -> ERRO CRÍTICO ao tentar resolver com Pyomo/CPLEX: {e}")
        print("   -> Verifique se o Pyomo e o CPLEX estão instalados e configurados corretamente.")
        return None

    # --------------------------------------------------------------------------
    # 1.C. CRIAÇÃO DO ARQUIVO DE ENTRADA PARA O MATLAB
    # --------------------------------------------------------------------------
    
    # Prepara os dados que o MATLAB precisa para a simulação física
    ders_para_matlab = np.array([item[:-1] for item in config_ders['unidades']])
    
    # A função addstorage do MOST precisa de duas matrizes: st_data e stor_data
    storage_units = config_storage.get('unidades', [])
    st_data = np.array([[s[0], 0, 0, -1000, 1000, 0, 0.1, 1, s[1], -s[1]] + [0]*12 for s in storage_units])
    stor_data = np.array([[s[5], s[3], s[4], 0.05, 1, 0, s[2]] + [0]*14 for s in storage_units])
    
    cenario_para_matlab = {
        'nome_caso': nome_caso_matlab,
        'ders_a_adicionar': ders_para_matlab,
        'storage_st_data': st_data,
        'storage_stor_data': stor_data
    }

    try:
        scipy.io.savemat('cenario.mat', cenario_para_matlab)
        print("   -> Arquivo 'cenario.mat' criado com sucesso para o MATLAB.")
    except Exception as e:
        print(f"   -> Erro ao criar 'cenario.mat': {e}")
        return None

    # Agrupa todas as configurações para retornar
    configs = {
        "ders": config_ders, "storage": config_storage,
        "compensacao": config_compensacao, "economicas": config_economicas
    }
    
    return nome_caso_matlab, configs

# ##############################################################################
# FASE 2: SIMULAÇÃO NO MATLAB
# Descrição: Contém o script que será executado pelo MATLAB, com base nos
#            arquivos gerados pela FASE 1.
# ##############################################################################
def get_comando_matlab():
    """
    Retorna a string com o script MATLAB. Este script carrega o 'cenario.mat',
    modifica o caso de estudo e executa a simulação.
    """
    print("FASE 2: Montando o comando de simulação do MATLAB...")
    
    comando_matlab = f"""
        try
            % --- 1. Carregamento e Preparação ---
            define_constants;
            
            % Carrega os dados do cenário preparados pelo Python
            load('cenario.mat', 'nome_caso', 'ders_a_adicionar', 'storage_st_data', 'storage_stor_data');
            
            fprintf('   -> MATLAB leu ''cenario.mat'' com sucesso.\\n');

            % Carrega o caso de estudo base dinamicamente
            mpc = eval(nome_caso);
            mpc_original = mpc; % Salva uma cópia para referência futura

            % --- 2. Adição de Recursos Distribuídos (DERs) ---
            fprintf('   -> Adicionando %d DERs ao caso de estudo...\\n', size(ders_a_adicionar, 1));
            for i = 1:size(ders_a_adicionar, 1)
                bus_idx = ders_a_adicionar(i, 1);
                capacity_mw = ders_a_adicionar(i, 2);
                
                % Define a linha do novo gerador
                new_gen_row = [bus_idx, capacity_mw, 0, 1000, -1000, 1.0, 100, 1, capacity_mw, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0];
                
                % Adiciona o gerador e seu custo ao mpc
                mpc.gen = [mpc.gen; new_gen_row];
                mpc.gencost = [mpc.gencost; [2, 0, 0, 3, 0, 0, 0, 0]]; % Custo com 8 colunas
            end
            
            % --- 3. Adição de Sistemas de Armazenamento (Baterias) ---
            if exist('storage_st_data', 'var') && ~isempty(storage_st_data)
                fprintf('   -> Adicionando %d unidades de armazenamento...\\n', size(storage_st_data, 1));
                % A função 'addstorage' é parte do MOST (MATPOWER Optimal Scheduling Tool)
                mpc = addstorage(mpc, storage_st_data, storage_stor_data);
            end

            % --- 4. Execução da Simulação ---
            fprintf('   -> Executando o Fluxo de Potência Ótimo (runopf)...\\n');
            % Define opções para o OPF para evitar saídas detalhadas no console
            mpopt = mpoption('verbose', 0, 'out.all', 0);
            resultados = runopf(mpc, mpopt);
            
            % --- 5. Salvando os Resultados ---
            if resultados.success
                fprintf('   -> Simulação bem-sucedida! Salvando resultados...\\n');
                save('resultados.mat', 'resultados', 'mpc_original');
            else
                fprintf('   -> ERRO: A simulação OPF não convergiu.\\n');
            end

        catch ME
            % Captura e exibe qualquer erro que ocorra no script MATLAB
            fprintf('ERRO NO SCRIPT MATLAB:\\n  Arquivo: %s\\n  Linha: %d\\n  Mensagem: %s\\n', ME.stack(1).file, ME.stack(1).line, ME.message);
        end
    """
    return comando_matlab

# ##############################################################################
# FASE 3: PROCESSAMENTO DOS RESULTADOS (EM PYTHON)
# Descrição: Python carrega o arquivo de resultados e verifica sua integridade.
# ##############################################################################
def processar_resultados():
    """
    Carrega o arquivo 'resultados.mat' criado pelo MATLAB e verifica seu conteúdo.
    """
    print("\nFASE 3: Lendo o arquivo de resultados no Python...")
    
    try:
        dados_do_matlab = scipy.io.loadmat('resultados.mat')
        print("   -> Arquivo 'resultados.mat' lido com sucesso pelo Python.")
        
        # Verifica se a estrutura de resultados esperada está presente
        if 'resultados_simulacao' in dados_do_matlab:
            print("   -> Estrutura 'resultados_simulacao' encontrada no arquivo.")
            
            # Acessa os dados (lembrando da estrutura aninhada do scipy.io)
            mensagem = dados_do_matlab['resultados_simulacao'][0, 0]['mensagem'][0]
            print(f"   -> Mensagem do MATLAB: '{mensagem}'")
            return True
        else:
            print("   -> ERRO: Estrutura 'resultados_simulacao' não encontrada.")
            return False
            
    except FileNotFoundError:
        print("   -> ERRO: O arquivo 'resultados.mat' não foi encontrado. A simulação no MATLAB pode ter falhado.")
        return False
    except Exception as e:
        print(f"   -> ERRO ao ler 'resultados.mat' no Python: {e}")
        return False

# ##############################################################################
# FASE 4: ORQUESTRADOR PRINCIPAL
# ##############################################################################
def main():
    """Função principal para executar o fluxo completo."""
    
    # FASE 1
    if not preparar_cenario_e_criar_arquivo():
        return # Para a execução se a criação do arquivo falhar

    # FASE 2
    print("\nIniciando comunicação com o MATLAB...")
    try:
        eng = matlab.engine.start_matlab()
        eng.addpath(os.getcwd(), nargout=0)
        matpower_path = r'C:\\Users\\KKCOD\\OneDrive - Université Laval\\Recherche\\codes\\matpower8.1'
        eng.addpath(eng.genpath(matpower_path), nargout=0)

        comando_matlab = get_comando_matlab()
        print("Executando script no MATLAB...")
        eng.eval(comando_matlab, nargout=0)

    except Exception as e:
        print(f"Ocorreu um erro na comunicação com o MATLAB: {e}")
    finally:
        if 'eng' in locals():
            eng.quit()
            print("Sessão MATLAB encerrada.")
            
    # FASE 3
    if processar_resultados():
        print("\nFLUXO DE ARQUIVOS VALIDADO: Python criou -> MATLAB leu -> MATLAB criou -> Python leu.")
    else:
        print("\nFALHA NO FLUXO DE ARQUIVOS. Verifique as mensagens de erro acima.")

if __name__ == "__main__":
    main()