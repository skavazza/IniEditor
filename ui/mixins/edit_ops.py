from PyQt6.QtWidgets import (
    QInputDialog, QMessageBox, QMenu, QTreeWidgetItem
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6 import sip

from i18n import _, T
from ui import BangGeneratorDialog
from commands import (
    AddSectionCommand, AddKeyCommand, RenameSectionCommand,
    DeleteSectionCommand, DeleteKeyCommand, DuplicateSectionCommand, 
    DuplicateKeyCommand, ChangeValueCommand, AddCommentCommand, DeleteCommentCommand
)

class EditOperationsMixin:
    """Mixin para operações de edição da estrutura do arquivo INI (seções, chaves, comentários)."""

    def add_section(self):
        name, ok = QInputDialog.getText(self, _('Adicionar Seção'), _('Nome da nova seção:'))
        if ok and name:
            if self.config.has_section(name):
                QMessageBox.warning(self, _('Aviso'), _('Uma seção com este nome já existe.'))
                return
            command = AddSectionCommand(self, name)
            self.undo_stack.push(command)

    def add_key(self):
        selected = self.tree.selectedItems()
        if not selected:
            QMessageBox.warning(self, _('Aviso'), _('Selecione uma seção primeiro.'))
            return
            
        item = selected[0]
        data = item.data(0, Qt.ItemDataRole.UserRole)
        section_name = data[1] if data else None
        
        if not section_name:
            return

        from ui import AutocompleteInputDialog
        dialog = AutocompleteInputDialog(self, _('Adicionar Chave'), _('Nome da chave:'), keywords=self.AUTOCOMPLETE_KEYS)
        dialog.setStyleSheet(self.styleSheet())
        
        if dialog.exec():
            key_name = dialog.get_text()
            if key_name:
                if '=' in key_name:
                    key_name = key_name.split('=')[0]
                
                if not self.config.has_option(section_name, key_name):
                    command = AddKeyCommand(self, section_name, key_name)
                    self.undo_stack.push(command)
                else:
                    QMessageBox.warning(self, _('Aviso'), _('Chave já existe nesta seção!'))

    def rename_section(self, section_name=None):
        if section_name is None:
            item = self.tree.currentItem()
            if not item: return
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data or data[0] != 'section': return
            old_name = data[1]
        else:
            old_name = section_name

        if old_name == 'DEFAULT': return
            
        new_name, ok = QInputDialog.getText(self, _('Renomear Seção'), _('Novo nome:'), text=old_name)
        if ok and new_name and new_name != old_name:
            if self.config.has_section(new_name):
                QMessageBox.warning(self, _('Aviso'), _('Seção já existe.'))
                return
            self.undo_stack.push(RenameSectionCommand(self, old_name, new_name))

    def delete_current_item(self):
        item = self.tree.currentItem()
        if item: self.delete_item(item)

    def delete_item(self, item_to_delete=None, section_name=None):
        if section_name:
            target_name = section_name
            is_section = True
        elif item_to_delete:
            data = item_to_delete.data(0, Qt.ItemDataRole.UserRole)
            if not data: return
            if data[0] == 'section':
                target_name = data[1]
                is_section = True
            else:
                target_name = data[2] # key name
                section_name = data[1]
                is_section = False
        else: return

        if is_section:
            if target_name == 'DEFAULT': return
            reply = QMessageBox.question(self, _('Confirmar Exclusão'), f'Excluir seção "{target_name}"?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.undo_stack.push(DeleteSectionCommand(self, target_name))
        else:
            reply = QMessageBox.question(self, _('Confirmar Exclusão'), f'Excluir chave "{target_name}"?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.undo_stack.push(DeleteKeyCommand(self, section_name, target_name))

    def duplicate_item(self, section_name=None):
        if section_name:
            old_name = section_name
            dup_type = 'section'
        else:
            item = self.tree.currentItem()
            if not item: return None
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data: return None
            dup_type = data[0]
            if dup_type == 'section': old_name = data[1]
            else: target_section, key_name = data[1], data[2]

        if dup_type == 'section':
            new_name, ok = QInputDialog.getText(self, _('Duplicar Seção'), _('Novo nome:'), text=f"{old_name}_Copy")
            if ok and new_name:
                if not self.config.has_section(new_name):
                    self.undo_stack.push(DuplicateSectionCommand(self, old_name, new_name))
                    return new_name
                else: QMessageBox.warning(self, _("Aviso"), _("Seção já existe."))
        elif dup_type == 'key':
            new_key, ok = QInputDialog.getText(self, _('Duplicar Chave'), _('Novo nome:'), text=f"{key_name}_Copy")
            if ok and new_key:
                if not self.config.has_option(target_section, new_key):
                    self.undo_stack.push(DuplicateKeyCommand(self, target_section, key_name, new_key))
                else: QMessageBox.warning(self, _("Aviso"), _("Chave já existe."))
        return None

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item: return
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data: return

        menu = QMenu()
        if data[0] == 'section':
            section_name = data[1]
            actions = {
                menu.addAction(_('Adicionar Chave')): self.add_key,
                menu.addAction(_('Adicionar Seção')): self.add_section,
                menu.addAction(_('Renomear Seção')): self.rename_section,
                menu.addAction(_('Duplicar Item')): self.duplicate_item,
                menu.addAction(_('Excluir Item')): lambda: self.delete_item(item_to_delete=item),
                menu.addAction(_('Adicionar Comentário')): lambda: self._prompt_add_comment(section_name)
            }
            action = menu.exec(self.tree.mapToGlobal(position))
            if action in actions: actions[action]()
        elif data[0] == 'key':
            actions = {
                menu.addAction(_('Adicionar Chave')): self.add_key,
                menu.addAction(_('Duplicar Item')): self.duplicate_item,
                menu.addAction(_('Excluir Item')): lambda: self.delete_item(item_to_delete=item),
                menu.addAction(_('Adicionar Comentário Acima')): lambda: self._prompt_add_comment(data[1])
            }
            action = menu.exec(self.tree.mapToGlobal(position))
            if action in actions: actions[action]()
        elif data[0] == 'comment':
            _type, section, line_idx = data
            del_action = menu.addAction(_('Excluir Comentário'))
            action = menu.exec(self.tree.mapToGlobal(position))
            if action == del_action:
                self.undo_stack.push(DeleteCommentCommand(self, line_idx))

    def _prompt_add_comment(self, section_name, insert_at=None):
        text, ok = QInputDialog.getText(self, _('Adicionar Comentário'), _('Texto:'), text='; ')
        if ok and text.strip():
            if insert_at is None:
                idx = len(self.raw_lines)
                in_sec = False
                for i, raw in enumerate(self.raw_lines):
                    s = raw.strip()
                    if s.startswith('[') and ']' in s:
                        if s[1:s.index(']')] == section_name: in_sec = True
                        elif in_sec: idx = i; break
            else: idx = insert_at
            self.undo_stack.push(AddCommentCommand(self, idx, text))

    def on_item_clicked(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == 'key':
            _, section, key = data
            val = self.config.defaults().get(key, '') if section == 'DEFAULT' else self.config.get(section, key, fallback='')
            self.value_editor.blockSignals(True)
            self.value_editor.setPlainText(val)
            self.value_editor.blockSignals(False)
            self.current_item = item
            self.last_saved_value = val
        else:
            self.value_editor.blockSignals(True)
            self.value_editor.clear()
            self.value_editor.blockSignals(False)
            self.current_item = None
            self.last_saved_value = None

    def on_value_changed(self):
        if hasattr(self, 'current_item') and self.current_item and not sip.isdeleted(self.current_item):
            self.value_timer.start(1000)
            data = self.current_item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == 'key':
                _, section, key = data
                new_val = self.value_editor.toPlainText()
                if section == 'DEFAULT': self.config.defaults()[key] = new_val
                else: self.config.set(section, key, new_val)
                self.current_item.setText(0, f'{key} = {new_val}')

    def push_value_command(self):
        if not self.current_item or sip.isdeleted(self.current_item): return
        data = self.current_item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data[0] != 'key': return
        _, section, key = data
        new_val = self.value_editor.toPlainText()
        if new_val != self.last_saved_value:
            self.undo_stack.push(ChangeValueCommand(self, section, key, self.last_saved_value, new_val))
            self.last_saved_value = new_val

    def filter_tree(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            sec_item = self.tree.topLevelItem(i)
            sec_vis = text in sec_item.text(0).lower()
            any_k_vis = False
            for j in range(sec_item.childCount()):
                k_item = sec_item.child(j)
                k_vis = text in k_item.text(0).lower()
                k_item.setHidden(not k_vis)
                if k_vis: any_k_vis = True
            sec_item.setHidden(not (sec_vis or any_k_vis))
            if any_k_vis: sec_item.setExpanded(True)

    def open_bang_generator(self):
        dialog = BangGeneratorDialog(self, self.dark_mode)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            res = dialog.get_result()
            editor = self.last_active_editor if self.last_active_editor else self.value_editor
            if editor == self.value_editor: self.tabs.setCurrentIndex(0)
            elif editor == self.var_editor:            self.tabs.setCurrentIndex(2)
            editor.insertPlainText(res)

    def update_tree(self):
        self.tree.clear()
        self.current_item = None
        
        # Cores para o "Highlighter" da Árvore
        if self.dark_mode:
            color_section = QColor("#da70d6") # Orchid
            color_key = QColor("#9cdcfe")     # Light Blue
            default_text_color = QColor("#cccccc")
            color_comment = QColor("#6a9955") # Verde escuro
        else:
            color_section = QColor("#800080") # Purple
            color_key = QColor("#0000ff")     # Blue
            default_text_color = QColor("#000000")
            color_comment = QColor("#607d3a") # Verde escuro claro

        # Pré-processar raw_lines para mapear comentários por seção
        comments_by_section = {}
        _current_sec = '__pre__'
        _pending_comments = []
        for idx, raw in enumerate(self.raw_lines):
            stripped = raw.strip()
            if stripped.startswith('[') and ']' in stripped:
                section_name = stripped[1:stripped.index(']')]
                if _pending_comments:
                    comments_by_section.setdefault(_current_sec, []).extend(_pending_comments)
                    _pending_comments = []
                _current_sec = section_name
            elif stripped.startswith(';') or stripped.startswith('#'):
                _pending_comments.append((idx, stripped))
            elif stripped:
                if _pending_comments:
                    comments_by_section.setdefault(_current_sec, []).extend(_pending_comments)
                    _pending_comments = []
        if _pending_comments:
            comments_by_section.setdefault(_current_sec, []).extend(_pending_comments)

        def _add_comment_items(parent_item, section_name):
            for line_idx, text in comments_by_section.get(section_name, []):
                c_item = QTreeWidgetItem([text])
                c_item.setData(0, Qt.ItemDataRole.UserRole, ('comment', section_name, line_idx))
                c_item.setForeground(0, color_comment)
                font = c_item.font(0)
                font.setItalic(True)
                c_item.setFont(0, font)
                c_item.setFlags(c_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                parent_item.addChild(c_item)

        for section_name in self.config.sections():
            section_item = QTreeWidgetItem([section_name])
            section_item.setData(0, Qt.ItemDataRole.UserRole, ('section', section_name))
            section_item.setForeground(0, color_section)
            self.tree.addTopLevelItem(section_item)
            _add_comment_items(section_item, section_name)

            for key, value in self.config.items(section_name):
                display_text = f'{key} = {value}'
                key_item = QTreeWidgetItem([display_text])
                key_item.setData(0, Qt.ItemDataRole.UserRole, ('key', section_name, key))
                section_item.addChild(key_item)

        if self.config.defaults():
            default_item = QTreeWidgetItem(['DEFAULT'])
            default_item.setData(0, Qt.ItemDataRole.UserRole, ('section', 'DEFAULT'))
            default_item.setForeground(0, color_section)
            self.tree.addTopLevelItem(default_item)
            for key, value in self.config.defaults().items():
                display_text = f'{key} = {value}'
                key_item = QTreeWidgetItem([display_text])
                key_item.setData(0, Qt.ItemDataRole.UserRole, ('key', 'DEFAULT', key))
                default_item.addChild(key_item)

        self.tree.expandAll()
        self._build_resolved_vars()
        if not self.is_updating_from_canvas:
            self.synchronize_canvas()
