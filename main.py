import matlab.engine
import scipy.io
import sys
import os
import numpy as np

# ##############################################################################
# FASE 1: PREPARAÇÃO DO CENÁRIO E CRIAÇÃO DO ARQUIVO DE ENTRADA
# Descrição: Python cria um arquivo .mat com os dados para o MATLAB.
# ##############################################################################
def preparar_cenario_e_criar_arquivo():
    """
    Prepara um dicionário com os dados do cenário e o salva em um arquivo .mat
    para o MATLAB consumir.
    """
    print("FASE 1: Preparando dados do cenário no Python...")

    # Nome do caso de estudo que o MATLAB deve carregar
    nome_caso_matlab = 'case2746wop_TAMU_Updated'

    # Dados de exemplo para novos geradores (formato numérico puro)
    ders_para_adicionar = np.array([
        [500, 200.0],  # [barra, capacidade_MW]
        [600, 150.0]
    ])

    # Cria um dicionário que será salvo no arquivo .mat
    cenario_para_matlab = {
        'nome_caso': nome_caso_matlab,
        'ders_a_adicionar': ders_para_adicionar
    }

    # Salva o dicionário no arquivo 'cenario.mat'
    try:
        scipy.io.savemat('cenario.mat', cenario_para_matlab)
        print("   -> Arquivo 'cenario.mat' criado com sucesso.")
    except Exception as e:
        print(f"   -> Erro ao criar 'cenario.mat': {e}")
        return False

    return True

# ##############################################################################
# FASE 2: COMANDO DE SIMULAÇÃO (EM MATLAB)
# Descrição: Script MATLAB que lê o arquivo de cenário e cria um arquivo de resultados.
# ##############################################################################
def get_comando_matlab():
    """
    Retorna a string com o script MATLAB. Este script agora carrega o 'cenario.mat'.
    """
    print("FASE 2: Montando o comando de simulação do MATLAB...")
    
    comando_matlab = """
        try
            % 1. Limpa o ambiente e carrega os dados do cenário
            clear;
            load('cenario.mat', 'nome_caso', 'ders_a_adicionar');
            
            fprintf('   -> MATLAB leu ''cenario.mat'' com sucesso.\\n');

            % 2. Carrega o caso de estudo base
            mpc = eval(nome_caso);
            fprintf('   -> MATLAB carregou o caso ''%s'' com %d barras.\\n', nome_caso, size(mpc.bus, 1));
            
            % 3. (Lógica de simulação será adicionada aqui no futuro)
            % Por enquanto, apenas criamos um resultado de exemplo
            
            resultados_simulacao = struct('sucesso', 1, 'mensagem', 'Simulacao de teste bem-sucedida');
            
            % 4. Salva os resultados para o Python
            save('resultados.mat', 'resultados_simulacao');
            fprintf('   -> MATLAB salvou ''resultados.mat'' com sucesso.\\n');

        catch ME
            fprintf('ERRO NO SCRIPT MATLAB:\\n%s\\n', ME.message);
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