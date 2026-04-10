import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QListWidget, QListWidgetItem, QListView, QTreeWidget, 
    QTreeWidgetItem, QTextEdit, QCheckBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon, QPixmap, QFontDatabase, QFont

class AssetManager(QWidget):
    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.resources_path = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.refresh_btn = QPushButton("Atualizar Galeria")
        self.refresh_btn.clicked.connect(self.refresh_assets)
        toolbar.addWidget(self.refresh_btn)
        
        self.path_label = QLabel("Nenhuma pasta @Resources carregada.")
        toolbar.addWidget(self.path_label)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Galeria
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListView.ViewMode.IconMode)
        self.list_widget.setIconSize(QSize(100, 100))
        self.list_widget.setResizeMode(QListWidget.ResizeMode.Adjust)
        self.list_widget.setMovement(QListWidget.Movement.Static)
        self.list_widget.setSpacing(10)
        self.list_widget.doubleClicked.connect(self.request_insertion)
        layout.addWidget(self.list_widget)

    def set_theme(self, dark_mode):
        if dark_mode:
            self.path_label.setStyleSheet("color: #888; font-style: italic;")
        else:
            self.path_label.setStyleSheet("color: #666; font-style: italic;")

    def set_resources_path(self, path):
        self.resources_path = path
        if path:
            self.path_label.setText(f"Pasta: {os.path.basename(os.path.dirname(path))}/@Resources")
            self.refresh_assets()
        else:
            self.path_label.setText("Pasta @Resources não encontrada.")
            self.list_widget.clear()

    def refresh_assets(self):
        if not self.resources_path or not os.path.isdir(self.resources_path):
            return
            
        self.list_widget.clear()
        extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.ico')
        
        for root, dirs, files in os.walk(self.resources_path):
            for file in files:
                if file.lower().endswith(extensions):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.resources_path)
                    
                    # Criar item com ícone/thumbnail
                    item = QListWidgetItem(file)
                    pixmap = QPixmap(full_path)
                    if not pixmap.isNull():
                        icon = QIcon(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                        item.setIcon(icon)
                    
                    # Salvar o caminho do Rainmeter (#@#Path\File.png)
                    rainmeter_path = f"#@#{rel_path}"
                    item.setData(Qt.ItemDataRole.UserRole, rainmeter_path)
                    item.setToolTip(rel_path)
                    
                    self.list_widget.addItem(item)

    def request_insertion(self):
        item = self.list_widget.currentItem()
        if item:
            path = item.data(Qt.ItemDataRole.UserRole)
            # Enviar sinal para o main inserir o texto
            if hasattr(self.parent(), 'insert_asset_path'):
                self.parent().insert_asset_path(path)
            elif hasattr(self.window(), 'insert_asset_path'):
                self.window().insert_asset_path(path)

class SnippetManager(QWidget):
    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.snippets = {
            "Meters": {
                "Texto Basico (String)": "[MeterText]\nMeter=String\nX=10\nY=10\nW=220\nH=32\nText=Ola Mundo\nFontFace=#FontFace#\nFontSize=#FontSize#\nFontColor=#FontColor#\nAntiAlias=1\nDynamicVariables=1\nStringAlign=LeftCenter\nClipString=1",
                "Texto com Medida + %": "[MeterCPU]\nMeter=String\nMeasureName=MeasureCPU\nX=0\nY=0\nW=180\nH=24\nText=CPU: %1%%\nFontColor=#FontColor#\nFontSize=#FontSize#\nFontFace=#FontFace#\nPercentual=1\nNumOfDecimals=1\nClipString=1\nAntiAlias=1\nDynamicVariables=1",
                "Texto com Inline": "[MeterInline]\nMeter=String\nX=10\nY=10\nW=260\nH=28\nText=Normal Destaque Normal\nFontColor=#FontColor#\nFontFace=#FontFace#\nFontSize=#FontSize#\nInlineSetting=Color | #AccentColor#\nInlinePattern=Destaque\nInlineSetting2=Bold\nInlinePattern2=Destaque\nAntiAlias=1\nDynamicVariables=1",
                "Texto Clip + Auto-Wrap": "[MeterLongText]\nMeter=String\nX=10\nY=10\nW=300\nH=80\nText=Texto muito longo que deve quebrar ou truncar de forma controlada.\nFontFace=#FontFace#\nFontSize=#FontSize#\nFontColor=#FontColor#\nClipString=2\nDynamicWindowSize=1\nAntiAlias=1",

                "Imagem Simples": "[MeterImage]\nMeter=Image\nImageName=#@#Icons\\app.png\nX=5\nY=5\nW=64\nH=64\nPreserveAspectRatio=1\nAntiAlias=1\nDynamicVariables=1",
                "Imagem com Mascara": "[MeterMasked]\nMeter=Image\nImageName=#@#Images\\photo.jpg\nMaskImageName=#@#Images\\circle-mask.png\nX=0\nY=0\nW=100\nH=100\nPreserveAspectRatio=1\nAntiAlias=1\nDynamicVariables=1",

                "Barra Horizontal Simples": "[MeterBar]\nMeter=Bar\nMeasureName=MeasureRAM\nX=10\nY=10\nW=180\nH=12\nBarColor=#AccentColor#\nSolidColor=50,50,50,180\nBarOrientation=Horizontal\nAntiAlias=1\nDynamicVariables=1",

                "Roundline Basico": "[MeterRoundline]\nMeter=Roundline\nMeasureName=MeasureCPU\nX=10\nY=10\nW=120\nH=120\nStartAngle=0\nRotationAngle=360\nLineStart=20\nLineLength=40\nLineWidth=8\nLineColor=#AccentColor#\nSolid=1\nAntiAlias=1\nDynamicVariables=1",
                "Roundline Gauge de Progresso": "[MeterRoundGauge]\nMeter=Roundline\nMeasureName=MeasureRAM\nX=0\nY=0\nW=140\nH=140\nStartAngle=225\nRotationAngle=270\nLineStart=30\nLineLength=45\nLineWidth=10\nLineColor=#AccentColor#\nSolid=1\nAntiAlias=1\nDynamicVariables=1",
                "Roundline Segmentado": "[MeterRoundSegments]\nMeter=Roundline\nMeasureName=MeasureDisk\nX=0\nY=0\nW=150\nH=150\nStartAngle=0\nRotationAngle=360\nLineStart=25\nLineLength=40\nLineWidth=6\nLineColor=255,170,0,255\nSolid=0\nAntiAlias=1\nDynamicVariables=1",
                "Roundline com Fundo": "[MeterRoundBg]\nMeter=Roundline\nX=0\nY=0\nW=140\nH=140\nStartAngle=225\nRotationAngle=270\nLineStart=28\nLineLength=44\nLineWidth=10\nLineColor=50,50,60,180\nSolid=1\nAntiAlias=1\n\n[MeterRoundValue]\nMeter=Roundline\nMeasureName=MeasureCPU\nX=r\nY=r\nW=140\nH=140\nStartAngle=225\nRotationAngle=270\nLineStart=28\nLineLength=44\nLineWidth=10\nLineColor=#AccentColor#\nSolid=1\nAntiAlias=1\nDynamicVariables=1",

                "Retangulo Arredondado (Background)": "[MeterBG]\nMeter=Shape\nShape=Rectangle 0,0,300,80,15 | Fill Color #BGColor# | StrokeWidth 2 | Stroke Color 80,80,100,150\nX=0\nY=0\nW=300\nH=80\nAntiAlias=1\nDynamicVariables=1",
                "Circulo (Icone/Botao)": "[MeterCircle]\nMeter=Shape\nShape=Ellipse 50,50,40 | Fill Color 0,120,255,220 | StrokeWidth 3 | Stroke Color 255,255,255,180\nX=0\nY=0\nW=100\nH=100\nAntiAlias=1",
                "Gauge Arco Circular": "[MeterArcGauge]\nMeter=Shape\nX=0\nY=0\nW=120\nH=120\nShape=Arc 60,60,60,60,0,0,0,0,0,1 | StrokeWidth 12 | Stroke Color 60,60,60,255\nShape2=Arc 60,60,60,60,[&StartAngle],[&SweepAngle],0,0,0,1 | StrokeWidth 12 | Stroke Color #AccentColor#\nDynamicVariables=1",
                "Botao com Gradiente": "[MeterButton]\nMeter=Shape\nShape=Rectangle 0,0,140,40,12 | Fill LinearGradient Grad | StrokeWidth 1 | Stroke Color 100,100,255,180\nGrad=90 | 50,100,255,255;0.0 | 100,200,255,255;1.0\nAntiAlias=1"
            },
            "Measures": {
                "CPU Uso Total": "[MeasureCPU]\nMeasure=CPU\nProcessor=0\nMinValue=0\nMaxValue=100\nUpdateDivider=1",
                "RAM Usada (%)": "[MeasureRAM]\nMeasure=PhysicalMemory\nMinValue=0\nMaxValue=100\nUpdateDivider=5",
                "Relogio Digital": "[MeasureTime]\nMeasure=Time\nFormat=%H:%M:%S\nTimeZone=Local",
                "Data Completa": "[MeasureDate]\nMeasure=Time\nFormat=%A, %d %B %Y",
                "Calculo Simples": "[MeasureCalc]\nMeasure=Calc\nFormula=Clamp([MeasureCPU] * 2, 0, 100)\nMinValue=0\nMaxValue=100\nDynamicVariables=1",
                "Espaco Livre Disco C:": "[MeasureDisk]\nMeasure=FreeDiskSpace\nDrive=C:\\\nUnit=GB\nMinValue=0\nMaxValue=Total",
                "Rede Download (NetIn)": "[MeasureNetIn]\nMeasure=NetIn\nInterface=Best\nCumulative=0",
                "Plugin Exemplo (Lua)": "[MeasureLua]\nMeasure=Plugin\nPlugin=LuaScript\nScriptFile=#@#Scripts\\main.lua",
                "WebParser - Titulo da Pagina": "[MeasureWebTitle]\nMeasure=WebParser\nURL=https://www.google.com\nRegExp=<title>(.*?)</title>",
                "Registry - Valor de Registro": "[MeasureRegistry]\nMeasure=Registry\nRegHKEY=HKEY_CURRENT_USER\nRegKey=\nRegPath=Software\\Rainmeter\nRegValue=AccentColor",
                "Process - Uso de CPU": "[MeasureProcess]\nMeasure=Process\nProcessName=chrome.exe\nUpdateDivider=1\nSubstitute=\"-1\":\"not running\",\"1\":\"running\""
            },
            "Templates": {
                "Estrutura Basica Completa": "[Rainmeter]\nUpdate=1000\nAccurateText=1\nDynamicWindowSize=1\nBackgroundMode=2\nSolidColor=0,0,0,1\n\n[Variables]\nFontColor=255,255,255,220\nAccentColor=0,180,255,255\nBGColor=30,30,40,200\nFontFace=Segoe UI\nFontSize=13\n\n[@Include]\n@Include=#@#Variables.inc\n\n[MeterBackground]\nMeter=Shape\nShape=Rectangle 0,0,280,180,20 | Fill Color #BGColor#\nW=280\nH=180\nAntiAlias=1\nDynamicVariables=1",
                "Gauge Roundline Animado": "[Rainmeter]\nUpdate=1000\nAccurateText=1\nDynamicWindowSize=1\n\n[Variables]\nAccentColor=0,180,255,255\nTrackColor=45,45,55,180\nFontColor=235,235,245,255\nFontFace=Segoe UI\nFontSize=14\nGaugeSize=160\nRingStart=34\nRingLength=48\nRingWidth=10\n\n[MeasureCPU]\nMeasure=CPU\nProcessor=0\nMinValue=0\nMaxValue=100\nUpdateDivider=1\n\n[MeasureSweep]\nMeasure=Calc\nFormula=([MeasureCPU] * 2.7)\nMinValue=0\nMaxValue=270\nDynamicVariables=1\n\n[MeterTrack]\nMeter=Roundline\nX=0\nY=0\nW=#GaugeSize#\nH=#GaugeSize#\nStartAngle=225\nRotationAngle=270\nLineStart=#RingStart#\nLineLength=#RingLength#\nLineWidth=#RingWidth#\nLineColor=#TrackColor#\nSolid=1\nAntiAlias=1\nDynamicVariables=1\n\n[MeterValue]\nMeter=Roundline\nMeasureName=MeasureCPU\nX=r\nY=r\nW=#GaugeSize#\nH=#GaugeSize#\nStartAngle=225\nRotationAngle=270\nLineStart=#RingStart#\nLineLength=#RingLength#\nLineWidth=#RingWidth#\nLineColor=#AccentColor#\nSolid=1\nAntiAlias=1\nDynamicVariables=1\n\n[MeterLabel]\nMeter=String\nMeasureName=MeasureCPU\nX=(#GaugeSize#/2)\nY=(#GaugeSize#/2)\nStringAlign=CenterCenter\nText=%1%%\nFontFace=#FontFace#\nFontSize=#FontSize#\nFontColor=#FontColor#\nAntiAlias=1\nDynamicVariables=1",
                "Tema Dark Moderno": "[Variables]\nFontColor=220,220,230,255\nAccent=100,180,255,255\nBG=25,25,35,220\nShadow=0,0,0,120\n\n[MeterShadow]\nMeter=Shape\nShape=Rectangle 5,5,270,170,18 | Fill Color #Shadow#\nBlur=1\nBlurRadius=8",
                "Container + Scroll": "[MeterContainer]\nMeter=Shape\nShape=Rectangle 0,0,250,400 | Fill Color 0,0,0,1\nW=250\nH=400\nAntiAlias=1\n\n[MeterContent]\nMeter=String\nContainer=MeterContainer\nY=r\nDynamicVariables=1"
            },
            "Acoes & Interatividade": {
                "Clique Simples (Abrir Site)": "LeftMouseUpAction=[\"https://www.google.com\"]",
                "Toggle Skin": "LeftMouseUpAction=[!ToggleConfig \"MinhaSuite\\Relogio\" \"Relogio.ini\"]",
                "Hover Highlight": "MouseOverAction=[!SetOption MeterText FontColor \"255,220,100,255\"][!UpdateMeter MeterText][!Redraw]\nMouseLeaveAction=[!SetOption MeterText FontColor \"#FontColor#\"][!UpdateMeter MeterText][!Redraw]",
                "Scroll Ajusta Variavel": "MouseScrollUpAction=[!SetVariable Scale \"(#Scale# + 0.1)\"][!Update]\nMouseScrollDownAction=[!SetVariable Scale \"(#Scale# - 0.1)\"][!Update]",
                "Atualizar Variavel Permanente": "LeftMouseUpAction=[!WriteKeyValue Variables AccentColor \"255,100,100\" \"#@#Variables.inc\"][!Refresh]"
            },
            "Variaveis Comuns": {
                "Bloco de Cores": "[Variables]\nFontColor=235,235,245,255\nAccent=80,200,255,255\nBG=18,18,28,220\nBorder=60,60,80,150",
                "Tamanhos Globais": "[Variables]\nScale=1.0\nFontSize=14\nIconSize=48\nPadding=12",
                "Caminhos": "[Variables]\n@=#@#\nImg=#@#Images\\\nFonts=#@#Fonts\\\nScripts=#@#Scripts\\"
            }
        }

        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Esquerda: Lista de Snippets
        left_panel = QVBoxLayout()
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Selecione um Modelo")
        self.tree.itemSelectionChanged.connect(self.show_preview)
        
        for category, items in self.snippets.items():
            cat_item = QTreeWidgetItem(self.tree)
            cat_item.setText(0, category)
            for name in items.keys():
                item = QTreeWidgetItem(cat_item)
                item.setText(0, name)
        
        self.tree.expandAll()
        left_panel.addWidget(self.tree)
        
        # Direita: Preview e Botão
        right_panel = QVBoxLayout()
        right_panel.addWidget(QLabel("<b>Pré-visualização:</b>"))
        
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        if self.dark_mode:
            self.preview.setStyleSheet("font-family: Consolas; background-color: #1e1e1e; color: #d4d4d4;")
        else:
            self.preview.setStyleSheet("font-family: Consolas; background-color: #ffffff; color: #000000;")
        right_panel.addWidget(self.preview)
        
        self.insert_btn = QPushButton("Inserir no Editor")
        self.insert_btn.setEnabled(False)
        self.insert_btn.clicked.connect(self.request_insertion)
        right_panel.addWidget(self.insert_btn)
        
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 2)

    def show_preview(self):
        item = self.tree.currentItem()
        if not item or not item.parent():
            self.preview.clear()
            self.insert_btn.setEnabled(False)
            return
            
        category = item.parent().text(0)
        name = item.text(0)
        code = self.snippets[category][name]
        self.preview.setPlainText(code)
        self.insert_btn.setEnabled(True)

    def request_insertion(self):
        code = self.preview.toPlainText()
        if code:
            # Enviar sinal para o main inserir o texto
            if hasattr(self.parent(), 'insert_snippet'):
                self.parent().insert_snippet(code)
            elif hasattr(self.window(), 'insert_snippet'):
                self.window().insert_snippet(code)

    def set_theme(self, dark_mode):
        self.dark_mode = dark_mode
        if self.dark_mode:
            self.preview.setStyleSheet("font-family: Consolas; background-color: #1e1e1e; color: #d4d4d4;")
        else:
            self.preview.setStyleSheet("font-family: Consolas; background-color: #ffffff; color: #000000;")

class FontManager(QWidget):
    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.resources_path = None
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        
        # Esquerda: Lista de Fontes
        left_panel = QVBoxLayout()
        self.font_list = QListWidget()
        
        families = QFontDatabase.families()
        valid_families = []
        for family in families:
            try:
                test_font = QFont(family, 10)
                if test_font.family() == family or test_font.exactMatch():
                    valid_families.append(family)
            except Exception as e:
                import utils
                utils.logger.debug(f"Aviso ao testar fonte '{family}': {e}")
        
        self.font_list.addItems(valid_families if valid_families else families)
        self.font_list.currentTextChanged.connect(self.show_preview)
        left_panel.addWidget(QLabel("Fontes do Sistema:"))
        left_panel.addWidget(self.font_list)
        
        # Direita: Preview
        right_panel = QVBoxLayout()
        self.preview_label = QLabel("ABCDEFGHIJKLMN\nabcdefghijklmn\n0123456789")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setWordWrap(True)
        if self.dark_mode:
            self.preview_label.setStyleSheet("background-color: #252526; border: 1px solid #3e3e3e; padding: 20px;")
        else:
            self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc; padding: 20px;")
        right_panel.addWidget(QLabel("Pré-visualização:"))
        right_panel.addWidget(self.preview_label)
        
        self.install_btn = QPushButton(r"Instalar na Skin (@Resources\Fonts)")
        self.install_btn.setEnabled(False)
        self.install_btn.clicked.connect(self.install_font)
        right_panel.addWidget(self.install_btn)
        
        layout.addLayout(left_panel, 1)
        layout.addLayout(right_panel, 1)

    def set_resources_path(self, path):
        self.resources_path = path

    def show_preview(self, family):
        if family:
            try:
                font = QFont(family, 24)
                self.preview_label.setFont(font)
                self.install_btn.setEnabled(True)
            except Exception as e:
                self.preview_label.setText(f"Erro ao carregar fonte: {family}")
                self.install_btn.setEnabled(False)

    def install_font(self):
        family = self.font_list.currentItem().text()
        if not self.resources_path:
            QMessageBox.warning(self, "Aviso", "A pasta @Resources não foi encontrada para esta skin.")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, f"Localizar arquivo para '{family}'", 
            "C:\\Windows\\Fonts", "Font Files (*.ttf *.otf *.woff)"
        )
        
        if file_path:
            fonts_dir = os.path.join(self.resources_path, "Fonts")
            if not os.path.exists(fonts_dir):
                os.makedirs(fonts_dir)
            
            target_name = os.path.basename(file_path)
            target_path = os.path.join(fonts_dir, target_name)
            
            try:
                import shutil
                shutil.copy2(file_path, target_path)
                
                reply = QMessageBox.question(
                    self, "Sucesso", 
                    f"Fonte '{target_name}' copiada para @Resources\\Fonts.\n\nDeseja inserir 'FontFace={family}' no editor?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    if hasattr(self.window(), 'insert_snippet'):
                        self.window().insert_snippet(f"FontFace={family}")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao copiar fonte: {str(e)}")

    def set_theme(self, dark_mode):
        self.dark_mode = dark_mode
        if self.dark_mode:
            self.preview_label.setStyleSheet("background-color: #252526; border: 1px solid #3e3e3e; padding: 20px;")
        else:
            self.preview_label.setStyleSheet("background-color: #f0f0f0; border: 1px solid #cccccc; padding: 20px;")
