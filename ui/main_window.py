import configparser
from PyQt6.QtWidgets import QMainWindow, QApplication
from PyQt6.QtCore import QTimer, QSettings
from PyQt6.QtGui import QUndoStack

from i18n import _, T
from core.constants import DEFAULT_ENCODING, VAR_FILE_ENCODING, AUTOCOMPLETE_KEYS
from ui.mixins.uisetup_mixin import UISetupMixin
from ui.mixins.file_ops import FileOperationsMixin
from ui.mixins.project_ops import ProjectOperationsMixin
from ui.mixins.edit_ops import EditOperationsMixin
from ui.mixins.canvas_ops import CanvasIntegrationMixin

class IniEditor(QMainWindow, UISetupMixin, FileOperationsMixin, 
                ProjectOperationsMixin, EditOperationsMixin, CanvasIntegrationMixin):
    """
    Janela principal do Editor de Skins Rainmeter.
    Esta classe atua como o hub central, herdando funcionalidades modulares via Mixins.
    """
    
    # Constantes agora centralizadas em core/constants.py, mas mantidas aqui para retrocompatibilidade se necessário
    AUTOCOMPLETE_KEYS = AUTOCOMPLETE_KEYS

    def __init__(self):
        super().__init__()
        
        # 1. Atributos de Estado e Configuração
        self.ini_file = None
        self.var_file = None
        self.current_encoding = DEFAULT_ENCODING
        self.var_file_encoding = VAR_FILE_ENCODING
        self.raw_lines = []  # Linhas brutas para preservar comentários e formatação
        self.dark_mode = True
        self.config = configparser.ConfigParser(interpolation=None, strict=False)
        self.resolved_vars = {}
        
        # 2. Preferências e histórico
        self.settings = QSettings('RainmeterEditor', 'RainmeterEditorAppSettings')
        self.recent_projects = self.settings.value('recent_projects', [])
        
        # 3. Inicializar Idioma (i18n)
        current_lang = self.settings.value("language", "pt_BR")
        T.set_language(current_lang)
        
        # 4. Sistema de Desfazer/Refazer (Undo/Redo)
        self.undo_stack = QUndoStack(self)
        
        # 5. Flags de Controle e Timers
        self.is_updating_from_canvas = False
        self.last_saved_value = None
        
        self.value_timer = QTimer(self)
        self.value_timer.setSingleShot(True)
        self.value_timer.timeout.connect(self.push_value_command)
        
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_file)
        
        # 6. Outros auxílios
        self.last_active_editor = None
        self.log_window = None # Janela de log (LogViewer)
        
        # 7. Inicializar Interface (herdado de UISetupMixin)
        self.init_ui()
        
        # 8. Configurações Finais
        self.configure_auto_save()
        self.apply_theme() # herdado de UISetupMixin

    def closeEvent(self, event):
        """Sobrescreve o evento de fechar para verificar alterações não salvas."""
        if self.check_unsaved_changes():
            event.accept()
        else:
            event.ignore()
