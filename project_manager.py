import json
import os

def save_project_json(file_path, state_dict):
    """
    Salva o dicionário de estado em um arquivo JSON.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=4, ensure_ascii=False)
        return True, "Projeto salvo com sucesso."
    except Exception as e:
        return False, f"Erro ao salvar o projeto: {str(e)}"

def load_project_json(file_path):
    """
    Lê o arquivo JSON e retorna o dicionário de estado.
    """
    if not os.path.exists(file_path):
        return False, "Arquivo não encontrado."
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            state_dict = json.load(f)
        return True, state_dict
    except Exception as e:
        return False, f"Erro ao ler o projeto: {str(e)}"
