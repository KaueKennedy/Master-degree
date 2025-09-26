import pandapower.networks as nw

def verificar_estrutura_do_bus():
    """
    Carrega a rede e imprime a estrutura da tabela de barras para entendermos
    como identificar e acessar cada uma.
    """
    print("--- Iniciando Teste de Identificação de Barras ---")
    
    try:
        # Carrega a rede de 1354 barras da biblioteca nativa
        net = nw.case1354pegase()
        print("Rede 'case1354pegase' carregada com sucesso.")
        
        # A tabela 'net.bus' contém todas as informações das barras
        # O 'head()' nos mostra as 5 primeiras linhas para vermos as colunas e o índice
        print("\n1. Visualização das 5 primeiras barras (cabeçalho da tabela):")
        print("   (Observe a primeira coluna sem nome - esse é o ÍNDICE)")
        print(net.bus.head().to_string())
        
        # Agora, vamos tentar acessar as barras específicas que nos interessam (3, 4, 10)
        
        print("\n2. Acessando as barras de interesse pela coluna 'name':")
        # Esta é a forma mais comum de encontrar uma barra pelo seu número original.
        barras_alvo = [3, 4, 10]
        # O método .isin() procura por qualquer um desses valores na coluna 'name'
        buses_encontrados = net.bus[net.bus.name.isin(barras_alvo)]
        
        if not buses_encontrados.empty:
            print("   -> SUCESSO! As barras foram encontradas pela coluna 'name'.")
            print("      Isto significa que o 'nome' da barra é o seu número original.")
            print("      A forma correta de encontrar o índice é: net.bus[net.bus.name == NUMERO_DA_BARRA].index[0]")
            print("\n   Dados das barras encontradas:")
            print(buses_encontrados.to_string())
        else:
            print("   -> FALHA! As barras 3, 4 e 10 não foram encontradas na coluna 'name'.")
            print("      Isso é inesperado. Por favor, verifique a saída acima para entender a estrutura.")

    except Exception as e:
        print(f"\nOcorreu um erro geral: {e}")

if __name__ == "__main__":
    verificar_estrutura_do_bus()