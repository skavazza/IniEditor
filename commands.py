from PyQt6.QtGui import QUndoCommand
from PyQt6.QtCore import Qt
from PyQt6 import sip


class DeleteSectionCommand(QUndoCommand):
    def __init__(self, editor, section_name):
        super().__init__(f"Excluir seção {section_name}")
        self.editor = editor
        self.section_name = section_name
        self.section_data = dict(editor.config.items(section_name))

    def redo(self):
        self.editor.config.remove_section(self.section_name)
        self.editor.update_tree()

    def undo(self):
        self.editor.config.add_section(self.section_name)
        for key, value in self.section_data.items():
            self.editor.config.set(self.section_name, key, value)
        self.editor.update_tree()


class DeleteKeyCommand(QUndoCommand):
    def __init__(self, editor, section_name, key_name):
        super().__init__(f"Excluir chave {key_name}")
        self.editor = editor
        self.section_name = section_name
        self.key_name = key_name
        self.value = editor.config.get(section_name, key_name)

    def redo(self):
        self.editor.config.remove_option(self.section_name, self.key_name)
        self.editor.update_tree()

    def undo(self):
        self.editor.config.set(self.section_name, self.key_name, self.value)
        self.editor.update_tree()


class DuplicateSectionCommand(QUndoCommand):
    def __init__(self, editor, old_name, new_name):
        super().__init__(f"Duplicar seção {old_name}")
        self.editor = editor
        self.old_name = old_name
        self.new_name = new_name
        self.data = dict(editor.config.items(old_name))

    def redo(self):
        self.editor.config.add_section(self.new_name)
        for key, value in self.data.items():
            self.editor.config.set(self.new_name, key, value)
        self.editor.update_tree()

    def undo(self):
        self.editor.config.remove_section(self.new_name)
        self.editor.update_tree()


class DuplicateKeyCommand(QUndoCommand):
    def __init__(self, editor, section_name, old_key, new_key):
        super().__init__(f"Duplicar chave {old_key}")
        self.editor = editor
        self.section_name = section_name
        self.old_key = old_key
        self.new_key = new_key
        self.value = editor.config.get(section_name, old_key)

    def redo(self):
        self.editor.config.set(self.section_name, self.new_key, self.value)
        self.editor.update_tree()

    def undo(self):
        self.editor.config.remove_option(self.section_name, self.new_key)
        self.editor.update_tree()


class AddSectionCommand(QUndoCommand):
    def __init__(self, editor, section_name):
        super().__init__(f"Adicionar seção {section_name}")
        self.editor = editor
        self.section_name = section_name

    def redo(self):
        if not self.editor.config.has_section(self.section_name):
            self.editor.config.add_section(self.section_name)
            self.editor.update_tree()

    def undo(self):
        self.editor.config.remove_section(self.section_name)
        self.editor.update_tree()


class AddKeyCommand(QUndoCommand):
    def __init__(self, editor, section_name, key_name, value=''):
        super().__init__(f"Adicionar chave {key_name}")
        self.editor = editor
        self.section_name = section_name
        self.key_name = key_name
        self.value = value

    def redo(self):
        self.editor.config.set(self.section_name, self.key_name, self.value)
        self.editor.update_tree()

    def undo(self):
        self.editor.config.remove_option(self.section_name, self.key_name)
        self.editor.update_tree()


class ChangeValueCommand(QUndoCommand):
    def __init__(self, editor, section, key, old_value, new_value):
        super().__init__(f"Alterar valor de {key}")
        self.editor = editor
        self.section = section
        self.key = key
        self.old_value = old_value
        self.new_value = new_value

    def redo(self):
        if self.section == 'DEFAULT':
            self.editor.config.defaults()[self.key] = self.new_value
        else:
            self.editor.config.set(self.section, self.key, self.new_value)
        self.sync_ui(self.new_value)

    def undo(self):
        if self.section == 'DEFAULT':
            self.editor.config.defaults()[self.key] = self.old_value
        else:
            self.editor.config.set(self.section, self.key, self.old_value)
        self.sync_ui(self.old_value)

    def sync_ui(self, value):
        # Atualizar apenas o item modificado na árvore principal para evitar recriar tudo
        for i in range(self.editor.tree.topLevelItemCount()):
            section_item = self.editor.tree.topLevelItem(i)
            s_data = section_item.data(0, Qt.ItemDataRole.UserRole)
            if s_data and s_data[0] == 'section' and s_data[1] == self.section:
                for j in range(section_item.childCount()):
                    key_item = section_item.child(j)
                    k_data = key_item.data(0, Qt.ItemDataRole.UserRole)
                    if k_data and k_data[0] == 'key' and k_data[2] == self.key:
                        key_item.setText(0, f'{self.key} = {value}')
                        break
                break

        self.editor.synchronize_canvas()
        
        # se item atual for o mesmo, atualiza o editor
        if self.editor.current_item and not sip.isdeleted(self.editor.current_item):
            data = self.editor.current_item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == 'key' and data[1] == self.section and data[2] == self.key:
                # FIX: Apenas atualiza se o texto for diferente para evitar que o cursor pule
                if self.editor.value_editor.toPlainText() != value:
                    self.editor.value_editor.blockSignals(True)
                    self.editor.value_editor.setPlainText(value)
                    self.editor.value_editor.blockSignals(False)
                self.editor.last_saved_value = value


class MoveItemCommand(QUndoCommand):
    def __init__(self, editor, section, old_x, old_y, new_x, new_y):
        super().__init__(f"Mover {section}")
        self.editor = editor
        self.section = section
        self.old_x = old_x
        self.old_y = old_y
        self.new_x = new_x
        self.new_y = new_y

    def redo(self):
        self.apply_pos(self.new_x, self.new_y)

    def undo(self):
        self.apply_pos(self.old_x, self.old_y)

    def apply_pos(self, x, y):
        # Evitar loop de sinais
        already_updating = self.editor.is_updating_from_canvas
        self.editor.is_updating_from_canvas = True
        
        try:
            self.editor.config.set(self.section, 'X', str(x))
            self.editor.config.set(self.section, 'Y', str(y))
            
            # Sincronizar Árvore e Editor de Campo sem recarregar tudo
            self.sync_tree(x, y)
            
            # Atualizar painel de propriedades
            self.editor.update_prop_panel(self.section)
            
            # Só sincroniza o CANVAS durante UNDO/REDO (quando already_updating é True,
            # o movimento veio de fora — Undo/Redo — e o canvas precisa ser reposicionado).
            # Em drags diretos (already_updating=False), o item já está na posição certa
            # visualmente; reconstruir o canvas quebraria o drag em andamento.
            if already_updating:
                self.editor.synchronize_canvas()
        finally:
            self.editor.is_updating_from_canvas = already_updating

    def sync_tree(self, x, y):
        tree = self.editor.tree
        for i in range(tree.topLevelItemCount()):
            section_item = tree.topLevelItem(i)
            s_data = section_item.data(0, Qt.ItemDataRole.UserRole)
            if s_data and s_data[0] == 'section' and s_data[1] == self.section:
                for j in range(section_item.childCount()):
                    key_item = section_item.child(j)
                    k_data = key_item.data(0, Qt.ItemDataRole.UserRole)
                    if k_data and k_data[0] == 'key' and k_data[1] == self.section:
                        if k_data[2].upper() == 'X':
                            key_item.setText(0, f'X = {x}')
                            self.update_field_editor('X', x)
                        elif k_data[2].upper() == 'Y':
                            key_item.setText(0, f'Y = {y}')
                            self.update_field_editor('Y', y)
                break

    def update_field_editor(self, key, value):
        # Se o campo selecionado for o que mudou, atualiza o texto sem mover o cursor
        if self.editor.current_item and not sip.isdeleted(self.editor.current_item):
            data = self.editor.current_item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == 'key' and data[1] == self.section and data[2].upper() == key.upper():
                if self.editor.value_editor.toPlainText() != str(value):
                    self.editor.value_editor.blockSignals(True)
                    self.editor.value_editor.setPlainText(str(value))
                    self.editor.value_editor.blockSignals(False)


class RenameSectionCommand(QUndoCommand):
    def __init__(self, editor, old_name, new_name):
        super().__init__(f"Renomear seção {old_name} para {new_name}")
        self.editor = editor
        self.old_name = old_name
        self.new_name = new_name
        self.section_data = dict(editor.config.items(old_name))

    def redo(self):
        # Em configparser, renomear é: adicionar nova, copiar dados, remover antiga
        self.editor.config.add_section(self.new_name)
        for key, value in self.section_data.items():
            self.editor.config.set(self.new_name, key, value)
        self.editor.config.remove_section(self.old_name)
        self.editor.update_tree()

    def undo(self):
        # Inverter: adicionar antiga, copiar dados, remover nova
        self.editor.config.add_section(self.old_name)
        for key, value in self.section_data.items():
            self.editor.config.set(self.old_name, key, value)
        self.editor.config.remove_section(self.new_name)
        self.editor.update_tree()


class AddCommentCommand(QUndoCommand):
    """Insere uma linha de comentário em raw_lines na posição indicada."""
    def __init__(self, editor, line_index, comment_text):
        super().__init__("Adicionar comentário")
        self.editor = editor
        self.line_index = line_index
        # Garantir que a linha termina com \n e começa com ;
        text = comment_text.strip()
        if not text.startswith(';'):
            text = '; ' + text
        self.line = text + '\n'

    def redo(self):
        self.editor.raw_lines.insert(self.line_index, self.line)
        self.editor.update_tree()

    def undo(self):
        if self.line_index < len(self.editor.raw_lines):
            self.editor.raw_lines.pop(self.line_index)
        self.editor.update_tree()


class DeleteCommentCommand(QUndoCommand):
    """Remove uma linha de comentário de raw_lines na posição indicada."""
    def __init__(self, editor, line_index):
        super().__init__("Excluir comentário")
        self.editor = editor
        self.line_index = line_index
        self.saved_line = editor.raw_lines[line_index] if line_index < len(editor.raw_lines) else '\n'

    def redo(self):
        if self.line_index < len(self.editor.raw_lines):
            self.editor.raw_lines.pop(self.line_index)
        self.editor.update_tree()

    def undo(self):
        self.editor.raw_lines.insert(self.line_index, self.saved_line)
        self.editor.update_tree()
