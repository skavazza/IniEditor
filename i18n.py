class Translator:
    def __init__(self):
        self.current_lang = "pt_BR"
        
        self.translations = {
            "en_US": {
                "Arquivo": "File",
                "Novo": "New",
                "Abrir": "Open",
                "Salvar": "Save",
                "Salvar Como": "Save As",
                "Exportar skin (.rmskin)": "Export skin (.rmskin)",
                "Abrir Projeto (.rmproject)": "Open Project (.rmproject)",
                "Salvar Projeto (.rmproject)": "Save Project (.rmproject)",
                "Projetos Recentes": "Recent Projects",
                "Adicionar Skin ao Projeto": "Add Skin to Project",
                
                "Editar": "Edit",
                "Desfazer": "Undo",
                "Refazer": "Redo",
                "Duplicar Item": "Duplicate Item",
                "Excluir Item": "Delete Item",
                "Preferências": "Preferences",
                
                "Exibir": "View",
                "Modo Escuro": "Dark Mode",
                "Exibir Limites da Skin": "Show Skin Boundary",
                "Exibir Grade": "Show Grid",
                "Encaixe Automático": "Snap to Grid",
                "Visualizador de Log": "Log Viewer",
                
                "Adicionar Seçã": "Add Section",
                "Adicionar Seção": "Add Section",
                "Renomear Seção": "Rename Section",
                "Adicionar Chave": "Add Key",
                "Atualizar Skin": "Refresh Skin",
                "Gerador de Bangs": "Bang Generator",
                
                "Nenhum projeto recente": "No recent projects",
                "Limpar Histórico": "Clear History",
                
                "Editor de Skin": "Skin Editor",
                "Canvas Visual": "Visual Canvas",
                "Variáveis Globais (@Resources)": "Global Variables (@Resources)",
                "Ativos (@Resources)": "Assets (@Resources)",
                "Snippets (Modelos)": "Snippets (Templates)",
                
                "Pesquisar seções ou chaves...": "Search sections or keys...",
                "Seções e Chaves": "Sections and Keys",
                "Selecione uma chave para editar seu valor": "Select a key to edit its value"
            }
            # O texto base no código já é Português (pt_BR), 
            # não precisamos mapear pt_BR para pt_BR a menos que precise de refatorações futuras.
        }

    def set_language(self, lang_code):
        if lang_code in ["pt_BR", "en_US"]:
            self.current_lang = lang_code

    def get(self, text):
        if self.current_lang == "pt_BR":
            return text
            
        dict_lang = self.translations.get(self.current_lang, {})
        return dict_lang.get(text, text) # Retorna original se não achar tradução

# Singleton instanciado
T = Translator()
def _(text):
    return T.get(text)
