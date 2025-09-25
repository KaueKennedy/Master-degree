import pandapower
import inspect
import pkgutil
import importlib

def encontrar_funcao(pacote, nome_funcao):
    """
    Procura recursivamente por uma função dentro de um pacote Python.
    """
    prefixo = pacote.__name__ + '.'
    for _, nome_modulo, is_pkg in pkgutil.walk_packages(pacote.__path__, prefixo):
        try:
            modulo = importlib.import_module(nome_modulo)
            if hasattr(modulo, nome_funcao):
                funcao_obj = getattr(modulo, nome_funcao)
                if inspect.isfunction(funcao_obj):
                    print(f"SUCESSO! Função '{nome_funcao}' encontrada.")
                    print(f"Para usá-la, escreva: from {modulo.__name__} import {nome_funcao}")
                    return True
        except Exception:
            # Ignora erros de importação de submódulos que possam ocorrer
            continue
    return False

print(f"Iniciando a busca pela função 'from_matpower' na biblioteca pandapower...")
print(f"Local da biblioteca: {pandapower.__path__}")

if not encontrar_funcao(pandapower, 'from_matpower'):
    print("\nERRO: A função 'from_matpower' não foi encontrada em nenhum submódulo padrão.")