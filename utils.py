import os
import sys
import logging
import re
import configparser
from PyQt6.QtGui import QColor

# Imports de outros módulos para manter a interface unificada
from logic import (
    find_variables_file, find_resources_dir, find_inc_files,
    refresh_skin, create_backup, package_rmskin,
    create_new_skin, add_skin_to_project
)
from project_manager import save_project_json, load_project_json

# Configuração básica de logging
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('IniEditor')

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def safe_int(value, default=0):
    try:
        return int(float(value))
    except (ValueError, TypeError):
        if value:
            logger.warning(f"Falha ao converter '{value}' para int. Usando padrão: {default}")
        return default

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (ValueError, TypeError):
        if value:
            logger.warning(f"Falha ao converter '{value}' para float. Usando padrão: {default}")
        return default

def parse_color(color_str, default=None):
    """Converte 'R,G,B,A' para QColor."""
    if not color_str or not isinstance(color_str, str):
        return default
    
    parts = [p.strip() for p in color_str.split(',')]
    if len(parts) >= 3:
        try:
            r = int(parts[0])
            g = int(parts[1])
            b = int(parts[2])
            a = int(parts[3]) if len(parts) >= 4 else 255
            return QColor(r, g, b, a)
        except (ValueError, IndexError) as e:
            logger.warning(f"Erro ao parsear cor '{color_str}': {e}")
    
    return default

def merge_config_with_raw(raw_lines, config):
    """
    Reconstrói o conteúdo do .ini a partir de raw_lines,
    substituindo valores conforme config (edições do usuário),
    preservando comentários e linhas em branco.
    """
    result = []
    current_section = None           # seção em processamento nas raw_lines
    sections_written = set()         # seções cujo header já foi escrito
    keys_written = {}                # section -> set de chaves já escritas
    
    # Conjunto de seções que existem no config atual
    existing_sections = set(config.sections())
    if config.defaults():
        existing_sections.add('DEFAULT')

    # Rastrear se estamos dentro de uma seção deletada (para pular suas chaves)
    in_deleted_section = False

    for line in raw_lines:
        stripped = line.strip()

        # ----- Linha de comentário ou em branco -----
        if not stripped or stripped.startswith(';') or stripped.startswith('#'):
            if not in_deleted_section:
                result.append(line)
            continue

        # ----- Cabeçalho de seção -----
        if stripped.startswith('[') and ']' in stripped:
            # Antes de mudar de seção, escrever chaves novas da seção anterior
            if current_section and current_section in existing_sections:
                for key, val in config.items(current_section):
                    if key not in keys_written.get(current_section, set()):
                        result.append(f'{key}={val}\n')
                        keys_written.setdefault(current_section, set()).add(key)

            section_name = stripped[1:stripped.index(']')]
            current_section = section_name

            if section_name in existing_sections:
                result.append(line)
                sections_written.add(section_name)
                keys_written.setdefault(section_name, set())
                in_deleted_section = False
            else:
                # Seção foi deletada — pular até próxima seção
                in_deleted_section = True
            continue

        # ----- Linha key=value -----
        if in_deleted_section:
            continue

        if '=' in stripped and current_section:
            key_raw = stripped.split('=', 1)[0].rstrip()
            key_lower = key_raw.lower()

            if current_section in existing_sections:
                if config.has_option(current_section, key_lower):
                    # Pegar valor atualizado do config
                    val = config.get(current_section, key_lower)
                    # Preservar espaçamento original em torno do =
                    eq_idx = line.index('=')
                    lhs = line[:eq_idx]  # inclui espaços/tabs antes do =
                    result.append(f'{lhs}= {val}\n')
                    keys_written.setdefault(current_section, set()).add(key_lower)
                else:
                    # Chave deletada — ignorar
                    pass
                continue

        # ----- Qualquer outra linha -----
        result.append(line)

    # Escrever chaves novas da última seção processada
    if current_section and current_section in existing_sections:
        for key, val in config.items(current_section):
            if key not in keys_written.get(current_section, set()):
                result.append(f'{key}={val}\n')

    # Escrever seções completamente novas (não presentes em raw_lines)
    for section in existing_sections:
        if section not in sections_written:
            result.append(f'\n[{section}]\n')
            for key, val in config.items(section):
                result.append(f'{key}={val}\n')

    return ''.join(result)

def resolve_rainmeter_variables(props, resolved_vars, resources_dir=""):
    """
    Substitui variáveis #VarName# nos valores das propriedades e resolve #@#.
    """
    res = {}
    rd = resources_dir
    
    def _sub_val(val, depth=0):
        if depth > 5 or not isinstance(val, str):
            return val
        
        # Substituir #@#
        if rd:
            val = val.replace("#@#", rd + os.sep)
        
        # Substituir #VarName# (case-insensitive)
        def _var_replace(match):
            var_name = match.group(1).lower()
            return resolved_vars.get(var_name, match.group(0))
            
        new_val = re.sub(r'#([^#]+)#', _var_replace, val)
        
        if new_val != val and "#" in new_val:
            return _sub_val(new_val, depth + 1)
        return new_val

    for k, v in props.items():
        res[k] = _sub_val(v)
    return res

def parse_variables_from_config(config):
    """Extrai variáveis da seção [Variables] de um ConfigParser."""
    variables = {}
    if config.has_section('Variables'):
        for k, v in config.items('Variables'):
            variables[k.lower()] = v
    return variables

def resolve_variable_references(variables):
    """Resolve referências cruzadas entre variáveis (#A# resolvendo para valor de A)."""
    resolved = variables.copy()
    for _ in range(5):
        changed = False
        for k, v in resolved.items():
            if '#' in v:
                new_v = re.sub(r'#([^#]+)#', lambda m: resolved.get(m.group(1).lower(), m.group(0)), v)
                if new_v != v:
                    resolved[k] = new_v
                    changed = True
        if not changed:
            break
    return resolved
