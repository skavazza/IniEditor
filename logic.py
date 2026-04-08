import os
import subprocess
import shutil
import zipfile

def find_variables_file(skin_file):
    # Tenta encontrar @Resources\Variables.inc
    path = os.path.dirname(skin_file)
    while path and len(os.path.split(path)[1]) > 0:
        resources_path = os.path.join(path, '@Resources')
        if os.path.isdir(resources_path):
            var_file = os.path.join(resources_path, 'Variables.inc')
            if os.path.exists(var_file):
                return var_file
        
        # Se chegarmos no nível da pasta 'Skins', paramos
        if os.path.split(path)[1].lower() == 'skins':
            break
        
        new_path = os.path.dirname(path)
        if new_path == path: break
        path = new_path
    return None

def refresh_skin(skin_file):
    if not skin_file:
        return False, "Abra uma skin primeiro!"
    
    path_parts = os.path.normpath(skin_file).split(os.sep)
    try:
        skins_index = -1
        for i, part in enumerate(path_parts):
            if part.lower() == 'skins':
                skins_index = i
                break
        
        if skins_index != -1:
            skin_name_parts = path_parts[skins_index + 1 : -1]
            skin_name = "\\".join(skin_name_parts)
            command = f'!Refresh "{skin_name}"'
        else:
            command = '!RefreshApp'
        
        subprocess.run(['Rainmeter.exe', command], shell=True)
        return True, "Skin atualizada!"
    except Exception as e:
        return False, str(e)

def create_backup(file_path):
    if os.path.exists(file_path):
        try:
            shutil.copy2(file_path, file_path + '.bak')
            return True
        except Exception:
            return False
    return False

def package_rmskin(skin_dir, export_data):
    """
    Cria um arquivo .rmskin compactando a pasta da skin.
    RMSKIN é basicamente um ZIP.
    """
    zip_name = f"{export_data['name']}_{export_data['version']}.rmskin"
    target_path = os.path.join(export_data['destination'], zip_name)
    
    try:
        # Pega a pasta pai para manter a estrutura relativa (ex: illustro/Clock/Clock.ini)
        # Se estivermos editando 'Clock.ini' dentro de 'illustro\Clock', 
        # o skin_dir deve ser 'illustro' ou a pasta pai correta.
        
        with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as rmskin:
            for root, dirs, files in os.walk(skin_dir):
                # Ignorar backups e arquivos de projeto do editor se existirem
                for file in files:
                    if file.endswith('.bak') or file == 'ROADMAP.md':
                        continue
                    
                    full_path = os.path.join(root, file)
                    # Caminho relativo a partir do pai da skin_dir para que a pasta da skin esteja no zip
                    rel_path = os.path.relpath(full_path, os.path.dirname(skin_dir))
                    rmskin.write(full_path, rel_path)
                    
        return True, target_path
    except Exception as e:
        return False, str(e)

def create_new_skin(base_path, skin_name, author="", version="1.0", description=""):
    """
    Cria a estrutura de pastas e arquivo inicial para uma nova skin.
    """
    skin_dir = os.path.join(base_path, skin_name)
    if os.path.exists(skin_dir):
        return False, f"A pasta '{skin_name}' já existe em {base_path}."
        
    try:
        # Criar pastas
        os.makedirs(skin_dir)
        resources_dir = os.path.join(skin_dir, "@Resources")
        os.makedirs(resources_dir)
        os.makedirs(os.path.join(resources_dir, "Fonts"))
        os.makedirs(os.path.join(resources_dir, "Images"))
        
        # Criar arquivo Variables.inc
        with open(os.path.join(resources_dir, "Variables.inc"), "w", encoding='utf-8') as f:
            f.write("; Variáveis Globais\n[Variables]\n")
            
        # Criar arquivo .ini inicial
        ini_path = os.path.join(skin_dir, f"{skin_name}.ini")
        template = f"""[Rainmeter]
Update=1000
AccurateText=1
DynamicWindowSize=1

[Metadata]
Name={skin_name}
Author={author}
Information={description}
Version={version}
License=Creative Commons BY-NC-SA 4.0

[Variables]
@Include=#@#Variables.inc

[MeterBackground]
Meter=Shape
Shape=Rectangle 0,0,200,100 | Fill Color 0,0,0,150 | StrokeWidth 0
X=0
Y=0

[MeterHello]
Meter=String
Text=Nova Skin: {skin_name}
FontSize=12
FontColor=255,255,255,255
X=10
Y=10
AntiAlias=1
"""
        with open(ini_path, "w", encoding='utf-8') as f:
            f.write(template)
            
        return True, ini_path
    except Exception as e:
        return False, str(e)

def add_skin_to_project(project_path, skin_name):
    """
    Cria uma nova pasta e um novo arquivo .ini para uma nova skin
    dentro de um projeto já existente (que já possui a pasta @Resources).
    """
    skin_dir = os.path.join(project_path, skin_name)
    if os.path.exists(skin_dir):
        return False, f"A pasta '{skin_name}' já existe no projeto."
        
    try:
        # Criar pasta da skin
        os.makedirs(skin_dir)
        
        # Criar arquivo .ini inicial
        ini_path = os.path.join(skin_dir, f"{skin_name}.ini")
        template = f"""[Rainmeter]
Update=1000
AccurateText=1
DynamicWindowSize=1

[Metadata]
Name={skin_name}
Author={author}
Information=Nova skin adicionada ao projeto.
Version=1.0
License=Creative Commons BY-NC-SA 4.0

[Variables]
@Include=#@#Variables.inc

[MeterBackground]
Meter=Shape
Shape=Rectangle 0,0,200,100 | Fill Color 0,0,0,150 | StrokeWidth 0
X=0
Y=0

[MeterHello]
Meter=String
Text=Skin: {skin_name}
FontSize=12
FontColor=255,255,255,255
X=10
Y=10
AntiAlias=1
"""
        with open(ini_path, "w", encoding='utf-8') as f:
            f.write(template)
            
        return True, ini_path
    except Exception as e:
        return False, str(e)
