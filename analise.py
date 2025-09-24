# analise.py
import numpy as np

def analisar_resultados_comparacao(resultados_base, resultados_otimizados):
    """
    Funcao para analisar e imprimir a comparacao entre dois cenarios.
    """
    print('===============================================================')
    print('                 Resultados da Otimizacao NEM                ')
    print('===============================================================')

    # --- Analise de Impactos Financeiros ---
    # Para o modelo de Despacho Economico, o custo e a propria funcao objetivo
    # Acessar a funcao objetivo requer que o valor seja salvo no Pyomo.
    # Vamos usar a geracao total como uma proxy de custo por enquanto.
    geracao_base = np.sum(resultados_base['gen'][:, 1])
    geracao_otimizada = np.sum(resultados_otimizados['gen'][:, 1])

    print("\n--- Impacto Financeiro ---")
    print(f"Geracao total (MW):")
    print(f"  Cenario Base:    {geracao_base:.2f}")
    print(f"  Cenario Otimizado: {geracao_otimizada:.2f}")

    # --- Analise de Impactos Tecnicos ---
    # Perdas de potencia ativa
    perdas_base = np.sum(resultados_base['branch'][:, 13] + resultados_base['branch'][:, 15])
    perdas_otimizadas = np.sum(resultados_otimizados['branch'][:, 13] + resultados_otimizados['branch'][:, 15])

    print("\n--- Impacto Tecnico ---")
    print(f"Perdas totais na rede (MW):")
    print(f"  Cenario Base:      {perdas_base:.2f}")
    print(f"  Cenario Otimizado: {perdas_otimizadas:.2f}")

    # Niveis de tensao
    tensao_min_base = np.min(resultados_base['bus'][:, 7])
    tensao_max_base = np.max(resultados_base['bus'][:, 7])
    tensao_min_otimizada = np.min(resultados_otimizados['bus'][:, 7])
    tensao_max_otimizada = np.max(resultados_otimizados['bus'][:, 7])

    print(f"Niveis de tensao (Min/Max em p.u.):")
    print(f"  Cenario Base:    Min={tensao_min_base:.3f}, Max={tensao_max_base:.3f}")
    print(f"  Cenario Otimizado: Min={tensao_min_otimizada:.3f}, Max={tensao_max_otimizada:.3f}")

    print('===============================================================')