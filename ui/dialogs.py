import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, 
    QComboBox, QLabel, QTextEdit, QDialogButtonBox, QFileDialog, QMessageBox,
    QCompleter
)
from PyQt6.QtCore import Qt

class BangGeneratorDialog(QDialog):
    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.setWindowTitle("Gerador de Bangs Rainmeter")
        self.setMinimumWidth(500)
        
        # Definição dos Bangs e seus parâmetros
        self.bangs_meta = {
            "!SetClip": ["String"],
            "!SetWallpaper": ["File", "Position"],
            "!About": ["Tabname"],
            "!Delay": ["Milliseconds"],
            "!SetOption": ["Config", "Meter", "Option", "Value"],
            "!SetVariable": ["Variable", "Value", "Config"],
            "!UpdateMeter": ["Meter", "Config"],
            "!UpdateMeasure": ["Measure", "Config"],
            "!WriteKeyValue": ["Section", "Key", "Value", "File"],
            "!Refresh": ["Config"],
            "!ActivateConfig": ["Config", "File"],
            "!DeactivateConfig": ["Config"],
            "!ToggleConfig": ["Config", "File"],
            "!ShowMeter": ["Meter", "Config"],
            "!HideMeter": ["Meter", "Config"],
            "!ToggleMeter": ["Meter", "Config"],
            "!SetWallpaper": ["FilePath", "Style"],
            "!Play": ["FilePath"],
            "!AddBlur": ["Region", "Config"],
            "!RemoveBlur": ["Region", "Config"],
            "!Show": ["Config"],
            "!Hide": ["Config"],
            "!Toggle": ["Config"],
            "!ShowBlur": ["Config"],
            "!HideBlur": ["Config"],
            "!ToggleBlur": ["Config"],
            "!SkinMenu": ["Config"],
            "!SkinCustomMenu": ["Config"],
            "!DisableMouseAction": ["Meter", "MouseAction", "Config"],
            "!ClearMouseAction": ["Meter", "MouseAction", "Config"],
            "!EnableMouseAction": ["Meter", "MouseAction", "Config"],
            "!ToggleMouseAction": ["Meter", "MouseAction", "Config"]
        }
        
        self.param_inputs = {}
        self.init_ui()

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Seleção do Bang
        self.form_layout = QFormLayout()
        self.bang_selector = QComboBox()
        self.bang_selector.addItems(sorted(self.bangs_meta.keys()))
        self.bang_selector.currentTextChanged.connect(self.update_params)
        self.form_layout.addRow("Comando (Bang):", self.bang_selector)
        
        # Container para parâmetros dinâmicos
        self.params_container = QWidget()
        self.params_layout = QFormLayout(self.params_container)
        self.form_layout.addRow(self.params_container)
        
        self.main_layout.addLayout(self.form_layout)
        
        # Pré-visualização
        self.preview_label = QLabel("<b>Pré-visualização:</b>")
        self.main_layout.addWidget(self.preview_label)
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(60)
        if self.dark_mode:
            self.preview_text.setStyleSheet("font-family: Consolas; background-color: #2d2d2d; color: #9cdcfe;")
        else:
            self.preview_text.setStyleSheet("font-family: Consolas; background-color: #ffffff; color: #000000;")
        self.main_layout.addWidget(self.preview_text)
        
        # Botões
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Inserir no Editor")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)
        
        # Inicializar parâmetros
        self.update_params(self.bang_selector.currentText())

    def update_params(self, bang_name):
        # Limpar parâmetros antigos
        for i in reversed(range(self.params_layout.count())):
            self.params_layout.itemAt(i).widget().setParent(None)
            
        self.param_inputs = {}
        params = self.bangs_meta.get(bang_name, [])
        
        for param in params:
            edit = QLineEdit()
            edit.setPlaceholderText(f"Opcional: {param}")
            edit.textChanged.connect(self.update_preview)
            self.params_layout.addRow(f"{param}:", edit)
            self.param_inputs[param] = edit
            
        self.update_preview()

    def update_preview(self):
        bang = self.bang_selector.currentText()
        params = []
        
        for param_name in self.bangs_meta[bang]:
            val = self.param_inputs[param_name].text().strip()
            if val:
                # Envolver em aspas se tiver espaços e não tiver aspas
                if ' ' in val and not (val.startswith('"') and val.endswith('"')):
                    val = f'"{val}"'
                params.append(val)
        
        result = f"[{bang} " + " ".join(params) + "]"
        self.preview_text.setPlainText(result)

    def get_result(self):
        return self.preview_text.toPlainText()

# We need to import QWidget for BangGeneratorDialog container
from PyQt6.QtWidgets import QWidget

class RmskinExportDialog(QDialog):
    def __init__(self, parent=None, default_name=""):
        super().__init__(parent)
        self.setWindowTitle("Exportar para .rmskin")
        self.setMinimumWidth(400)
        self.init_ui(default_name)

    def init_ui(self, default_name):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit(default_name)
        self.name_edit.setPlaceholderText("Ex: MyAmazingSkin")
        form.addRow("Nome da Skin:", self.name_edit)
        
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Seu Nome / apelido")
        form.addRow("Autor:", self.author_edit)
        
        self.version_edit = QLineEdit("1.0")
        form.addRow("Versão:", self.version_edit)
        
        self.save_path_edit = QLineEdit()
        self.save_path_edit.setPlaceholderText("Pasta onde salvar o .rmskin")
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.save_path_edit)
        self.browse_btn = QPushButton("...")
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self.browse_save_path)
        path_layout.addWidget(self.browse_btn)
        form.addRow("Salvar em:", path_layout)
        
        layout.addLayout(form)
        
        # Botões
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Exportar Agora")
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def browse_save_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar pasta de destino")
        if directory:
            self.save_path_edit.setText(directory)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Aviso", "O nome da skin é obrigatório.")
            return
        if not self.save_path_edit.text().strip():
            QMessageBox.warning(self, "Aviso", "Selecione a pasta de destino.")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "author": self.author_edit.text().strip(),
            "version": self.version_edit.text().strip(),
            "destination": self.save_path_edit.text().strip()
        }
        
# Import QPushButton for RmskinExportDialog
from PyQt6.QtWidgets import QPushButton

class NewSkinDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Criar Nova Skin")
        self.setMinimumWidth(400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex: MinhaNovaSkin")
        form.addRow("Nome da Skin:", self.name_edit)
        
        self.path_edit = QLineEdit()
        self.path_edit.setText(os.path.expanduser("~/Documents/Rainmeter/Skins"))
        
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        self.browse_btn = QPushButton("...")
        self.browse_btn.setFixedWidth(30)
        self.browse_btn.clicked.connect(self.browse_path)
        path_layout.addWidget(self.browse_btn)
        form.addRow("Criar em (Pasta):", path_layout)
        
        self.author_edit = QLineEdit()
        self.author_edit.setPlaceholderText("Seu Nome")
        form.addRow("Autor:", self.author_edit)
        
        self.version_edit = QLineEdit("1.0")
        form.addRow("Versão:", self.version_edit)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Uma breve descrição da skin")
        form.addRow("Descrição:", self.description_edit)
        
        layout.addLayout(form)
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Criar Skin")
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def browse_path(self):
        directory = QFileDialog.getExistingDirectory(self, "Selecionar pasta onde criar a skin")
        if directory:
            self.path_edit.setText(directory)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Aviso", "O nome da skin é obrigatório.")
            return
        if not self.path_edit.text().strip():
            QMessageBox.warning(self, "Aviso", "Selecione a pasta de destino.")
            return
        self.accept()

    def get_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "base_path": self.path_edit.text().strip(),
            "author": self.author_edit.text().strip(),
            "version": self.version_edit.text().strip(),
            "description": self.description_edit.text().strip()
        }

class AddSkinDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Adicionar Skin ao Projeto")
        self.setMinimumWidth(350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Ex: Clock, SystemView, etc.")
        form.addRow("Nome da Nova Skin:", self.name_edit)
        
        layout.addLayout(form)
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Adicionar")
        self.buttons.accepted.connect(self.validate_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def validate_and_accept(self):
        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Aviso", "O nome da skin é obrigatório.")
            return
        self.accept()

    def get_skin_name(self):
        return self.name_edit.text().strip()

from PyQt6.QtCore import QSettings

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferências")
        self.setMinimumWidth(350)
        self.settings = QSettings('RainmeterEditor', 'RainmeterEditorAppSettings')
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Idioma
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Português", "pt_BR")
        self.lang_combo.addItem("English", "en_US")
        
        current_lang = self.settings.value("language", "pt_BR")
        index = self.lang_combo.findData(current_lang)
        if index >= 0:
            self.lang_combo.setCurrentIndex(index)
            
        form.addRow("Idioma / Language:", self.lang_combo)
        
        # Auto Save
        from PyQt6.QtWidgets import QCheckBox
        self.auto_save_cb = QCheckBox("Habilitar")
        self.auto_save_cb.setChecked(self.settings.value("auto_save_enabled", False, type=bool))
        form.addRow("Auto-Save:", self.auto_save_cb)
        
        # Intervalo
        self.interval_combo = QComboBox()
        self.interval_combo.addItem("1 Minuto", 60000)
        self.interval_combo.addItem("5 Minutos", 300000)
        self.interval_combo.addItem("10 Minutos", 600000)
        
        current_interval = self.settings.value("auto_save_interval", 300000, type=int)
        index = self.interval_combo.findData(current_interval)
        if index >= 0:
            self.interval_combo.setCurrentIndex(index)
            
        self.auto_save_cb.stateChanged.connect(lambda: self.interval_combo.setEnabled(self.auto_save_cb.isChecked()))
        self.interval_combo.setEnabled(self.auto_save_cb.isChecked())
        
        form.addRow("Intervalo de Auto-Save:", self.interval_combo)
        
        layout.addLayout(form)
        
        # AVISO
        layout.addWidget(QLabel("<i>Nota: A alteração de idioma pode exigir\num reinício para ter efeito completo.</i>"))
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save_and_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def save_and_accept(self):
        self.settings.setValue("language", self.lang_combo.currentData())
        self.settings.setValue("auto_save_enabled", self.auto_save_cb.isChecked())
        self.settings.setValue("auto_save_interval", self.interval_combo.currentData())
        self.accept()



class AutocompleteInputDialog(QDialog):
    def __init__(self, parent=None, title="", label="", text="", keywords=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.input_edit = QLineEdit(text)
        if keywords:
            self.completer = QCompleter(keywords, self)
            self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            self.completer.setFilterMode(Qt.MatchFlag.MatchContains)
            self.input_edit.setCompleter(self.completer)
            
        form.addRow(label, self.input_edit)
        layout.addLayout(form)
        
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        
        # Focar no input e selecionar texto se houver
        self.input_edit.setFocus()
        if text:
            self.input_edit.selectAll()

    def get_text(self):
        return self.input_edit.text().strip()

from PyQt6.QtWidgets import QTabWidget, QScrollArea, QFrame

class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ajuda, Atalhos e Documentação")
        self.setMinimumSize(500, 450)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Aba 1: Atalhos (Shortcuts)
        shortcuts_tab = QWidget()
        s_layout = QVBoxLayout(shortcuts_tab)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        s_layout.addWidget(scroll)
        
        content = QWidget()
        scroll.setWidget(content)
        c_layout = QFormLayout(content)
        
        # Lista de atalhos
        c_layout.addRow(QLabel("<b>Gerais:</b>"), QLabel(""))
        c_layout.addRow("Ctrl + N", QLabel("Nova Skin"))
        c_layout.addRow("Ctrl + S", QLabel("Salvar Arquivo Aberto"))
        c_layout.addRow("Ctrl + P", QLabel("Preferências"))
        c_layout.addRow(QLabel("<b>Editor de Código:</b>"), QLabel(""))
        c_layout.addRow("Ctrl + Z", QLabel("Desfazer (Editor e Canvas)"))
        c_layout.addRow("Ctrl + Y", QLabel("Refazer (Editor e Canvas)"))
        c_layout.addRow("Ctrl + F", QLabel("Localizar (se implementado)"))
        c_layout.addRow(QLabel("<b>Canvas Visual:</b>"), QLabel(""))
        c_layout.addRow("Scroll do Mouse", QLabel("Zoom In / Zoom Out"))
        c_layout.addRow("Arrastar", QLabel("Mover item livremente"))
        c_layout.addRow("Ctrl + Seleção", QLabel("Múltipla Seleção (em breve)"))
        c_layout.addRow("Arrastar Bordas", QLabel("Redimensionar item (W / H)"))
        c_layout.addRow("Del", QLabel("Excluir Item Selecionado"))
        c_layout.addRow("Ctrl + D", QLabel("Duplicar Item Selecionado"))
        
        tabs.addTab(shortcuts_tab, "Atalhos de Teclado")
        
        # Aba 2: Documentação Rainmeter
        docs_tab = QWidget()
        d_layout = QVBoxLayout(docs_tab)
        
        desc = QLabel(
            "<h3>Rainmeter Oficial</h3>"
            "<p>O Rainmeter tem uma extensa e detalhada documentação online sobre como criar Skins "
            "e configurar os Meters e Measures.</p>"
            "<ul>"
            "<li><a href='https://docs.rainmeter.net/manual/'>Manual Principal do Rainmeter</a></li>"
            "<li><a href='https://docs.rainmeter.net/manual/meters/'>Apostila de Meters (Visuais)</a></li>"
            "<li><a href='https://docs.rainmeter.net/manual/measures/'>Apostila de Measures (Dados)</a></li>"
            "<li><a href='https://docs.rainmeter.net/manual/variables/'>Variáveis Dinâmicas e Nativas</a></li>"
            "</ul>"
            "<p><i>Dica de Desenvolvimento:</i> Utilize a aba <b>Modelos (Snippets)</b> para criar os blocos "
            "principais rapidamente e o botão <b>!Bangs</b> para visualizar ações interativas.</p>"
        )
        desc.setOpenExternalLinks(True)
        desc.setWordWrap(True)
        d_layout.addWidget(desc)
        d_layout.addStretch()
        
        tabs.addTab(docs_tab, "Documentação e Links")
        
        # Botões
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox

class ShapeEditorDialog(QDialog):
    def __init__(self, parent=None, initial_string="", dark_mode=True):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.setWindowTitle("Editor de Formas (Shape)")
        self.setMinimumWidth(450)
        self.initial_string = initial_string
        
        self.params_inputs = {}
        self.fill_color = "255,255,255,150"
        self.stroke_color = "255,255,255,255"
        self.stroke_width = 1
        
        self.init_ui()
        self.parse_string(initial_string)

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        # Tipo de Forma
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Rectangle", "Ellipse", "Line"])
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        form.addRow("Tipo de Forma:", self.type_combo)
        
        # Container para parâmetros dinâmicos
        self.params_container = QWidget()
        self.params_layout = QFormLayout(self.params_container)
        self.params_layout.setContentsMargins(0, 0, 0, 0)
        form.addRow(self.params_container)
        
        # Divisor
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        form.addRow(line)
        
        # Estilo
        # Cor de Preenchimento
        self.fill_edit = QLineEdit(self.fill_color)
        self.fill_btn = QPushButton()
        self.fill_btn.setFixedWidth(30)
        self.fill_btn.clicked.connect(self.pick_fill_color)
        
        fill_layout = QHBoxLayout()
        fill_layout.addWidget(self.fill_edit)
        fill_layout.addWidget(self.fill_btn)
        form.addRow("Cor de Preenchimento:", fill_layout)
        
        # Cor da Borda
        self.stroke_edit = QLineEdit(self.stroke_color)
        self.stroke_btn = QPushButton()
        self.stroke_btn.setFixedWidth(30)
        self.stroke_btn.clicked.connect(self.pick_stroke_color)
        
        stroke_layout = QHBoxLayout()
        stroke_layout.addWidget(self.stroke_edit)
        stroke_layout.addWidget(self.stroke_btn)
        form.addRow("Cor da Borda:", stroke_layout)
        
        # Espessura da Borda
        self.width_spin = QDoubleSpinBox()
        self.width_spin.setRange(0, 100)
        self.width_spin.setValue(self.stroke_width)
        form.addRow("Espessura da Borda:", self.width_spin)
        
        self.main_layout.addLayout(form)
        
        # Preview
        self.main_layout.addWidget(QLabel("<b>Resultado:</b>"))
        self.result_edit = QLineEdit()
        self.result_edit.setReadOnly(True)
        self.main_layout.addWidget(self.result_edit)
        
        # Sinais para atualizar preview
        self.fill_edit.textChanged.connect(self.update_preview)
        self.stroke_edit.textChanged.connect(self.update_preview)
        self.width_spin.valueChanged.connect(self.update_preview)
        
        # Botões
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.main_layout.addWidget(self.buttons)
        
        self.on_type_changed(self.type_combo.currentText())

    def on_type_changed(self, shape_type):
        # Limpar parâmetros anteriores
        while self.params_layout.count():
            child = self.params_layout.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        self.params_inputs = {}
        
        specs = {
            "Rectangle": ["X", "Y", "W", "H", "Radius"],
            "Ellipse": ["CenterX", "CenterY", "RadiusX", "RadiusY"],
            "Line": ["StartX", "StartY", "EndX", "EndY"]
        }
        
        for param in specs.get(shape_type, []):
            edit = QLineEdit("0")
            edit.textChanged.connect(self.update_preview)
            self.params_layout.addRow(f"{param}:", edit)
            self.params_inputs[param] = edit
            
        self.update_preview()

    def parse_string(self, s):
        if not s: return
        
        parts = [p.strip() for p in s.split('|')]
        if not parts: return
        
        # Parte 1: Forma e Coordenadas
        main_part = parts[0]
        main_words = main_part.split(' ', 1)
        if len(main_words) < 2: return
        
        shape_type = main_words[0]
        args_str = main_words[1]
        args = [a.strip() for a in args_str.split(',')]
        
        index = self.type_combo.findText(shape_type, Qt.MatchFlag.MatchExactly)
        if index >= 0:
            self.type_combo.setCurrentIndex(index)
            # Preencher inputs
            keys = list(self.params_inputs.keys())
            for i, val in enumerate(args):
                if i < len(keys):
                    self.params_inputs[keys[i]].setText(val)
                    
        # Modificadores
        for mod in parts[1:]:
            lmod = mod.lower()
            if lmod.startswith("fill color"):
                self.fill_color = mod[10:].strip()
                self.fill_edit.setText(self.fill_color)
            elif lmod.startswith("stroke color"):
                self.stroke_color = mod[12:].strip()
                self.stroke_edit.setText(self.stroke_color)
            elif lmod.startswith("strokewidth"):
                try: 
                    self.stroke_width = float(mod[11:].strip())
                    self.width_spin.setValue(self.stroke_width)
                except: pass
        
        self.update_preview()

    def update_preview(self):
        shape_type = self.type_combo.currentText()
        args = []
        for key in self.params_inputs:
            args.append(self.params_inputs[key].text() or "0")
            
        res = f"{shape_type} {','.join(args)}"
        
        # Modificadores
        res += f" | Fill Color {self.fill_edit.text()}"
        res += f" | Stroke Color {self.stroke_edit.text()}"
        if self.width_spin.value() != 1:
            res += f" | StrokeWidth {self.width_spin.value():.1f}".replace('.0', '')
            
        self.result_edit.setText(res)
        self.update_color_buttons()

    def update_color_buttons(self):
        def set_btn_color(btn, color_str):
            parts = [p.strip() for p in color_str.split(',')]
            bg = "white"
            if len(parts) >= 3:
                try: bg = f"rgb({parts[0]},{parts[1]},{parts[2]})"
                except: pass
            btn.setStyleSheet(f"background-color: {bg}; border: 1px solid #888; border-radius: 2px;")
            
        set_btn_color(self.fill_btn, self.fill_edit.text())
        set_btn_color(self.stroke_btn, self.stroke_edit.text())

    def pick_fill_color(self):
        color = self._open_picker(self.fill_edit.text())
        if color: self.fill_edit.setText(color)

    def pick_stroke_color(self):
        color = self._open_picker(self.stroke_edit.text())
        if color: self.stroke_edit.setText(color)

    def _open_picker(self, current):
        initial = QColor(255, 255, 255)
        parts = [p.strip() for p in current.split(',')]
        if len(parts) >= 3:
            try: 
                a = int(parts[3]) if len(parts) == 4 else 255
                initial = QColor(int(parts[0]), int(parts[1]), int(parts[2]), a)
            except: pass
            
        color = QColorDialog.getColor(initial, self, "Selecionar Cor", QColorDialog.ColorDialogOption.ShowAlphaChannel)
        if color.isValid():
            r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()
            return f"{r},{g},{b}" if a == 255 else f"{r},{g},{b},{a}"
        return None

    def get_result(self):
        return self.result_edit.text()
