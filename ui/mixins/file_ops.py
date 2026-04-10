import os
import configparser
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QInputDialog
from PyQt6.QtCore import Qt

from core.constants import SUPPORTED_ENCODINGS, DEFAULT_ENCODING
from utils import (
    find_variables_file, find_inc_files, 
    create_new_skin, add_skin_to_project, refresh_skin
)
from i18n import _, T
from ui import NewSkinDialog, AddSkinDialog, RmskinExportDialog

class FileOperationsMixin:
    """Mixin para operações de carregamento, salvamento e exportação de arquivos INI."""

    def check_unsaved_changes(self):
        if not self.undo_stack.isClean():
            reply = QMessageBox.question(
                self, _('Salvar alterações?'),
                _('Você tem alterações não salvas. Deseja salvá-las antes de prosseguir?'),
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self.save_file()
                return True
            elif reply == QMessageBox.StandardButton.Discard:
                return True
            else: # Cancel
                return False
        return True

    def close_file(self):
        if not self.check_unsaved_changes():
            return

        self.ini_file = None
        self.var_file = None
        self.config = configparser.ConfigParser(interpolation=None, strict=False)
        self.undo_stack.clear()
        self.raw_lines = []
        self.resolved_vars = {}
        
        self.tree.clear()
        self.value_editor.clear()
        self.var_editor.clear()
        self.canvas_widget.clear_canvas()
        self.layer_panel.set_meters([])
        self.prop_panel.clear_properties()
        self.asset_tab.set_resources_path(None)
        
        self.var_file_combo.blockSignals(True)
        self.var_file_combo.clear()
        self.var_file_combo.blockSignals(False)
        
        self.add_skin_action.setEnabled(False)
        self.btn_save_vars.setEnabled(False)
        self.setWindowTitle('Editor de Arquivos .ini - Rainmeter Skins')
        
        var_idx = self.tabs.indexOf(self.var_widget)
        if var_idx != -1:
            self.tabs.setTabText(var_idx, _("Variáveis Globais"))

    def open_file(self):
        if not self.check_unsaved_changes():
            return
        file_path, _filter = QFileDialog.getOpenFileName(
            self, _('Abrir arquivo .ini'), '', 'Arquivos INI (*.ini);;Todos os arquivos (*)'
        )
        if file_path:
            self.load_ini_file(file_path)

    def new_skin(self):
        if not self.check_unsaved_changes():
            return
        dialog = NewSkinDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            data = dialog.get_data()
            success, result = create_new_skin(
                data['base_path'], 
                data['name'],
                author=data.get('author', ''),
                version=data.get('version', '1.0'),
                description=data.get('description', '')
            )
            if success:
                QMessageBox.information(self, _("Sucesso"), f"Skin '{data['name']}' criada com sucesso!")
                self.load_ini_file(result)
            else:
                QMessageBox.critical(self, _("Erro"), f"Erro ao criar skin: {result}")

    def add_skin_to_project_action(self):
        if not self.var_file:
            QMessageBox.warning(self, _("Aviso"), _("Não há um projeto com a pasta @Resources aberto."))
            return
        resources_dir = os.path.dirname(self.var_file)
        project_path = os.path.dirname(resources_dir)
        dialog = AddSkinDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            skin_name = dialog.get_skin_name()
            success, result = add_skin_to_project(project_path, skin_name)
            if success:
                reply = QMessageBox.question(
                    self, _('Skin Adicionada'),
                    f"Skin '{skin_name}' adicionada com sucesso ao projeto!\nDeseja abrir esta skin agora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.load_ini_file(result)
            else:
                QMessageBox.critical(self, _("Erro"), f"Erro ao adicionar skin: {result}")

    def load_ini_file(self, file_path):
        self.config = configparser.ConfigParser(interpolation=None, strict=False)
        self.undo_stack.clear()
        self.raw_lines = []
        success = False
        last_error = ""
        used_enc = self.current_encoding

        for enc, _label in SUPPORTED_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                self.config.read_string(content)
                self.raw_lines = content.splitlines(keepends=True)
                if self.raw_lines and not self.raw_lines[-1].endswith('\n'):
                    self.raw_lines[-1] += '\n'
                used_enc = enc
                success = True
                break
            except Exception as e:
                last_error = str(e)
                self.config = configparser.ConfigParser(interpolation=None, strict=False)
                continue
        
        if not success:
            QMessageBox.critical(self, _('Erro'), f'Não foi possível decodificar o arquivo: {last_error}')
            return

        self.ini_file = file_path
        self.current_encoding = used_enc
        self.update_encoding_menu()
        self.var_file = find_variables_file(file_path)
        self._build_resolved_vars()
        self.update_tree()
        self.setWindowTitle(f'Editor de Arquivos .ini - {os.path.basename(file_path)}')
        
        if self.var_file:
            self.asset_tab.set_resources_path(os.path.dirname(self.var_file))
        else:
            self.asset_tab.set_resources_path(None)

        inc_files = find_inc_files(file_path)
        self.var_file_combo.blockSignals(True)
        self.var_file_combo.clear()
        for inc_path in inc_files:
            self.var_file_combo.addItem(os.path.basename(inc_path), inc_path)
        self.var_file_combo.blockSignals(False)

        if inc_files:
            self.add_skin_action.setEnabled(True)
            default_idx = 0
            if self.var_file:
                for i in range(self.var_file_combo.count()):
                    if self.var_file_combo.itemData(i) == self.var_file:
                        default_idx = i
                        break
            self.var_file_combo.setCurrentIndex(default_idx)
            self._on_var_file_selected(default_idx)
        else:
            self.var_editor.setPlainText(_("Nenhum arquivo .inc encontrado em @Resources."))
            self.btn_save_vars.setEnabled(False)
            self.add_skin_action.setEnabled(False if not self.var_file else True)
            var_idx = self.tabs.indexOf(self.var_widget)
            if var_idx != -1:
                self.tabs.setTabText(var_idx, _("Variáveis Globais"))

    def save_file(self, silent=False):
        if not self.ini_file:
            self.save_file_as()
            return

        try:
            from utils import merge_config_with_raw
            # Usar a função utilitária para manter comentários
            output = merge_config_with_raw(self.raw_lines, self.config)
            
            with open(self.ini_file, 'w', encoding=self.current_encoding) as f:
                f.write(output)
            
            # Só marca como "limpo" se não estivermos no meio de uma macro de undo
            # (QUndoStack não permite setClean dentro de macro)
            if not self.undo_stack.isActive():
                self.undo_stack.setClean()

            if not silent:
                self.statusBar().showMessage(_("Arquivo salvo com sucesso."), 3000)
        except Exception as e:
            if not silent:
                QMessageBox.critical(self, _("Erro"), f"Erro ao salvar arquivo: {str(e)}")

    def save_file_as(self):
        file_path, _filter = QFileDialog.getSaveFileName(
            self, _('Salvar arquivo .ini como'), '', 'Arquivos INI (*.ini);;Todos os arquivos (*)'
        )
        if file_path:
            self.ini_file = file_path
            self.save_file()
            self.setWindowTitle(f'Editor de Arquivos .ini - {os.path.basename(file_path)}')

    def save_variables_file(self):
        if not self.var_file: return
        try:
            content = self.var_editor.toPlainText()
            with open(self.var_file, 'w', encoding=self.var_file_encoding) as f:
                f.write(content)
            self.statusBar().showMessage(_("Variáveis globais salvas."), 3000)
            self._build_resolved_vars()
            self.synchronize_canvas()
        except Exception as e:
            QMessageBox.critical(self, _("Erro"), f"Erro ao salvar variáveis: {str(e)}")

    def _on_var_file_selected(self, index):
        file_path = self.var_file_combo.itemData(index)
        if not file_path or not os.path.exists(file_path):
            return
        
        self.var_file = file_path
        var_idx = self.tabs.indexOf(self.var_widget)
        if var_idx != -1:
            self.tabs.setTabText(var_idx, f"VAR: {os.path.basename(file_path)}")
            
        try:
            # Tentar carregar com diferentes encodings
            content = ""
            for enc in ['utf-8-sig', 'utf-16', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        content = f.read()
                    self.var_file_encoding = enc
                    break
                except (UnicodeDecodeError, OSError):
                    continue
            self.var_editor.setPlainText(content)
            self.btn_save_vars.setEnabled(True)
        except Exception as e:
            self.var_editor.setPlainText(f"Erro ao carregar arquivo: {str(e)}")
            self.btn_save_vars.setEnabled(False)

    def set_file_encoding(self, encoding):
        self.current_encoding = encoding
        self.update_encoding_menu()
        self.statusBar().showMessage(f"Codificação alterada para {encoding}", 3000)

    def update_encoding_menu(self):
        if hasattr(self, 'encoding_actions'):
            for enc, action in self.encoding_actions.items():
                action.setChecked(enc == self.current_encoding)

    def auto_save_file(self):
        if self.ini_file:
            self.save_file(silent=True)

    def export_rmskin(self):
        if not self.ini_file:
            QMessageBox.warning(self, "Aviso", "Abra uma skin primeiro.")
            return
        dialog = RmskinExportDialog(self, skin_path=os.path.dirname(self.ini_file))
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()

    def refresh_skin(self):
        success, message = refresh_skin(self.ini_file)
        if not success:
            QMessageBox.warning(self, _('Aviso'), message)
