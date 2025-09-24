import matlab.engine
import scipy.io
import sys
import os

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

# Comando MATLAB para rodar o caso de estudo e salvar o resultado
comando_matlab = """
    mpc = pglib_opf_case73_ieee_rts();
    resultados = runpf(mpc);
    save('resultados.mat', 'resultados');
"""

print("Executando simulação no MATLAB...")
try:
    eng.eval(comando_matlab, nargout=0)
    print("Simulacao concluida no MATLAB. Arquivo 'resultados.mat' gerado.")
except Exception as e:
    print(f"Erro durante a execucao do comando MATLAB: {e}")
    eng.quit()
    sys.exit()

print("Tentando carregar os resultados no Python...")
try:
    # Carrega o arquivo .mat no Python
    dados_carregados = scipy.io.loadmat('resultados.mat')
    
    # --- Passo de validacao adicional ---
    # Verifica se a chave 'resultados' existe no dicionario
    if 'resultados' in dados_carregados:
        print("Sucesso! A estrutura 'resultados' foi encontrada no arquivo.")
        
        # Acessa a matriz de barras e imprime o numero total de barras
        resultados_data = dados_carregados['resultados']
        
        # O MATLAB retorna a matriz aninhada dentro de um array numpy, entao precisamos
        # acessar o indice [0,0] para obter a matriz real.
        bus_matrix = resultados_data['bus'][0,0]
        num_buses = bus_matrix.shape[0]
        
        print(f"O caso de estudo contém {num_buses} barras.")
        
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
    print("\nSessao MATLAB encerrada.")
    #teste