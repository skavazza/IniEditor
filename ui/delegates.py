from PyQt6.QtWidgets import QStyledItemDelegate, QApplication, QStyle, QStyleOptionViewItem
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

class KeyValueDelegate(QStyledItemDelegate):
    """Renderiza itens de chave da árvore com cores separadas para nome e valor,
    igual ao IniHighlighter do editor de código."""

    def __init__(self, editor):
        super().__init__(editor)
        self.editor = editor

    def _colors(self):
        dark = self.editor.dark_mode
        if dark:
            return {
                'key':     QColor("#9cdcfe"),
                'var':     QColor("#4ec9b0"),
                'num':     QColor("#b5cea8"),
                'default': QColor("#cccccc"),
            }
        return {
            'key':     QColor("#0000ff"),
            'var':     QColor("#008080"),
            'num':     QColor("#008000"),
            'default': QColor("#000000"),
        }

    def _val_color(self, colors, value):
        if '#' in value:
            return colors['var']
        stripped = value.strip()
        if stripped.isdigit() or (',' in stripped and all(x.strip().isdigit() for x in stripped.split(','))):
            return colors['num']
        return colors['default']

    def paint(self, painter, option, index):
        data = index.data(Qt.ItemDataRole.UserRole)
        if not data or data[0] != 'key':
            super().paint(painter, option, index)
            return

        # Cópia segura do option para não corromper o objeto C++ original
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        widget = opt.widget
        style = widget.style() if widget else QApplication.style()

        painter.save()

        # Desenha fundo (seleção, hover) sem o texto
        opt.text = ''
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, widget)

        text_rect = style.subElementRect(QStyle.SubElement.SE_ItemViewItemText, opt, widget)
        text = index.data(Qt.ItemDataRole.DisplayRole) or ''
        is_selected = bool(opt.state & QStyle.StateFlag.State_Selected)

        colors = self._colors()

        if '=' in text:
            eq_pos = text.index('=')
            key_part = text[:eq_pos].rstrip() + ' '
            eq_part = '= '
            val_part = text[eq_pos + 1:].strip()
        else:
            key_part = text
            eq_part = ''
            val_part = ''

        painter.setFont(opt.font)
        fm = painter.fontMetrics()
        x = text_rect.x() + 2
        y = text_rect.y() + (text_rect.height() - fm.height()) // 2 + fm.ascent()

        def draw(txt, color):
            nonlocal x
            c = QColor("#ffffff") if is_selected else color
            painter.setPen(c)
            painter.drawText(x, y, txt)
            x += fm.horizontalAdvance(txt)

        draw(key_part, colors['key'])
        draw(eq_part, colors['default'])
        draw(val_part, self._val_color(colors, val_part))

        painter.restore()
