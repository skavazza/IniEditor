import os
import json
from PyQt6.QtWidgets import QFileDialog, QMessageBox, QMenu, QInputDialog
from PyQt6.QtCore import Qt, QSettings
from PyQt6.QtGui import QAction

from i18n import _, T
from ui import LogViewer

class ProjectOperationsMixin:
    """Mixin para gestão de projetos (.rmproject), snippets e integração com o LogViewer."""

    def open_project(self, file_path=None):
        if not file_path:
            if not self.check_unsaved_changes():
                return
            file_path, _filter = QFileDialog.getOpenFileName(
                self, _('Abrir Projeto'), '', _('Projetos Rainmeter (*.rmproject)')
            )
        
        if file_path and os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                main_ini = data.get('main_ini')
                if main_ini:
                    # Se o caminho for relativo, resolver em relação ao .rmproject
                    if not os.path.isabs(main_ini):
                        main_ini = os.path.join(os.path.dirname(file_path), main_ini)
                    
                    if os.path.exists(main_ini):
                        self.load_ini_file(main_ini)
                        self.add_to_recent_projects(file_path)
                    else:
                        QMessageBox.warning(self, _("Erro"), _("Arquivo .ini principal não encontrado."))
            except Exception as e:
                QMessageBox.critical(self, _("Erro"), f"Erro ao abrir projeto: {str(e)}")

    def save_project(self):
        if not self.ini_file:
            QMessageBox.warning(self, _("Aviso"), _("Abra uma skin primeiro."))
            return
            
        file_path, _filter = QFileDialog.getSaveFileName(
            self, _('Salvar Projeto'), '', _('Projetos Rainmeter (*.rmproject)')
        )
        if file_path:
            try:
                # Salvar caminho relativo do INI se possível
                try:
                    main_ini = os.path.relpath(self.ini_file, os.path.dirname(file_path))
                except ValueError:
                    main_ini = self.ini_file
                    
                data = {
                    'main_ini': main_ini,
                    'version': '1.0'
                }
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4)
                
                self.add_to_recent_projects(file_path)
                QMessageBox.information(self, _("Sucesso"), _("Projeto salvo com sucesso!"))
            except Exception as e:
                QMessageBox.critical(self, _("Erro"), f"Erro ao salvar projeto: {str(e)}")

    def update_recent_menu(self):
        self.recent_menu.clear()
        if not self.recent_projects:
            self.recent_menu.addAction(_("Nenhum projeto recente")).setEnabled(False)
            return

        for path in self.recent_projects:
            action = QAction(os.path.basename(path), self)
            action.setData(path)
            action.triggered.connect(lambda checked, p=path: self.open_project(p))
            self.recent_menu.addAction(action)
        
        self.recent_menu.addSeparator()
        clear_action = QAction(_("Limpar Histórico"), self)
        clear_action.triggered.connect(self.clear_recent_projects)
        self.recent_menu.addAction(clear_action)

    def add_to_recent_projects(self, file_path):
        if file_path in self.recent_projects:
            self.recent_projects.remove(file_path)
        self.recent_projects.insert(0, file_path)
        self.recent_projects = self.recent_projects[:10]  # Limite de 10
        self.settings.setValue('recent_projects', self.recent_projects)
        self.update_recent_menu()

    def clear_recent_projects(self):
        self.recent_projects = []
        self.settings.setValue('recent_projects', [])
        self.update_recent_menu()

    def show_log_viewer(self):
        if not self.log_window:
            self.log_window = LogViewer(dark_mode=self.dark_mode)
            self.log_window.setWindowTitle("Rainmeter Log")
            self.log_window.resize(600, 400)
            self.log_window.setStyleSheet(self.styleSheet())
        
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()

    def _set_last_active(self, editor):
        self.last_active_editor = editor

    def insert_asset_path(self, path):
        editor = self.last_active_editor if self.last_active_editor else self.value_editor
        if editor == self.value_editor:
            self.tabs.setCurrentIndex(0)
        elif editor == self.var_editor:
            self.tabs.setCurrentIndex(2)
        editor.insertPlainText(path)

    def insert_snippet(self, code):
        from PyQt6.QtCore import Qt
        import re
        import configparser
        from commands import AddSectionCommand, AddKeyCommand
        
        has_sections = bool(re.search(r'^\[.*\]', code, re.MULTILINE))
        
        if has_sections:
            if not self.ini_file:
                self._insert_snippet_raw(code)
                return

            snippet_config = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                snippet_config.read_string(code)
            except Exception:
                self._insert_snippet_raw(code)
                return
            
            self.undo_stack.beginMacro(_("Inserir Snippet (Estruturado)"))
            for section in snippet_config.sections():
                new_name = section
                counter = 1
                while self.config.has_section(new_name):
                    new_name = f"{section}_{counter}"
                    counter += 1
                
                self.undo_stack.push(AddSectionCommand(self, new_name))
                for key, value in snippet_config.items(section):
                    self.undo_stack.push(AddKeyCommand(self, new_name, key, value))
            
            self.undo_stack.endMacro()
            self.tabs.setCurrentIndex(0)
            QMessageBox.information(self, _("Sucesso"), _("Snippet adicionado com sucesso!"))
        else:
            selected_items = self.tree.selectedItems()
            target_section = None
            if selected_items:
                item = selected_items[0]
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data:
                    target_section = data[1] if data[0] in ('section', 'key') else None
            
            if target_section and self.tabs.currentIndex() == 0:
                self.undo_stack.beginMacro(_("Inserir Snippet na Seção"))
                added = 0
                for line in code.splitlines():
                    line = line.strip()
                    if not line or line.startswith(';'): continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        self.undo_stack.push(AddKeyCommand(self, target_section, k.strip(), v.strip()))
                        added += 1
                self.undo_stack.endMacro()
                if added > 0: return
            
            self._insert_snippet_raw(code)

    def _insert_snippet_raw(self, code):
        editor = self.last_active_editor if self.last_active_editor else self.value_editor
        if editor == self.value_editor:
            self.tabs.setCurrentIndex(0)
        elif editor == self.var_editor:
            self.tabs.setCurrentIndex(2)
        editor.insertPlainText(code)
