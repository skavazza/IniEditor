from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import QRegularExpression

class IniHighlighter(QSyntaxHighlighter):
    def __init__(self, parent, dark_mode=True):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self._apply_rules()

    def set_theme(self, dark_mode):
        self.dark_mode = dark_mode
        self._apply_rules()
        self.rehighlight()

    def _apply_rules(self):
        self.highlighting_rules = []

        if self.dark_mode:
            color_var = QColor("#4ec9b0")     # Aquamarine
            color_section = QColor("#da70d6") # Orchid
            color_num = QColor("#b5cea8")     # Light Green
            color_comment = QColor("#6a9955") # Green (Visual Studio style)
            color_key = QColor("#9cdcfe")     # Light Blue
        else:
            color_var = QColor("#008080")     # Teal
            color_section = QColor("#800080") # Purple
            color_num = QColor("#008000")     # Green
            color_comment = QColor("#008000") # Dark Green
            color_key = QColor("#0000ff")     # Blue

        # Comentários (; ou # no início da linha)
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(color_comment)
        comment_fmt.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"^[;#].*"), comment_fmt))

        # Seções [Section]
        section_fmt = QTextCharFormat()
        section_fmt.setForeground(color_section)
        section_fmt.setFontWeight(700) # Bold
        self.highlighting_rules.append((QRegularExpression(r"\[[^\]]+\]"), section_fmt))

        # Chaves (Key antes de =)
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(color_key)
        self.highlighting_rules.append((QRegularExpression(r"^[^\s=]+(?=\s*=)"), key_fmt))

        # Variáveis #Variavel#
        variable_fmt = QTextCharFormat()
        variable_fmt.setForeground(color_var)
        self.highlighting_rules.append((QRegularExpression(r"#[^#]+#"), variable_fmt))

        # Números
        number_fmt = QTextCharFormat()
        number_fmt.setForeground(color_num)
        self.highlighting_rules.append((QRegularExpression(r"\b\d+\b"), number_fmt))

    def highlightBlock(self, text):
        for expression, fmt in self.highlighting_rules:
            iterator = expression.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
