import os
import configparser
from PyQt6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QTreeWidget, QTreeWidgetItem, QPushButton, QFileDialog,
    QMessageBox, QSplitter, QInputDialog, QMenu, QColorDialog, QLineEdit,
    QTabWidget, QLabel, QStyledItemDelegate, QApplication, QStyle,
    QStyleOptionViewItem, QComboBox
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QAction, QActionGroup, QColor, QKeySequence, QShortcut, QUndoStack
from PyQt6 import sip

# Importações locais
from ui import (
    RainmeterEdit, IniHighlighter, LogViewer, BangGeneratorDialog, 
    AssetManager, SnippetManager, RmskinExportDialog, FontManager, 
    VisualCanvas, LayerPanel, PropertyPanel, NewSkinDialog, 
    AddSkinDialog, PreferencesDialog, AutocompleteInputDialog, HelpDialog
)
from logic import find_variables_file, find_inc_files, refresh_skin, create_backup, package_rmskin, create_new_skin, add_skin_to_project
from project_manager import save_project_json, load_project_json
from i18n import _, T
from PyQt6.QtCore import QSettings
from commands import (
    DeleteSectionCommand, DeleteKeyCommand, DuplicateSectionCommand,
    DuplicateKeyCommand, AddSectionCommand, AddKeyCommand,
    ChangeValueCommand, MoveItemCommand, RenameSectionCommand,
    AddCommentCommand, DeleteCommentCommand
)


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


class IniEditor(QMainWindow):
    SUPPORTED_ENCODINGS = [
        ('utf-8-sig', 'UTF-8 com BOM'),
        ('utf-8', 'UTF-8'),
        ('utf-16', 'UTF-16'),
        ('utf-16-le', 'UTF-16 Little Endian'),
        ('utf-16-be', 'UTF-16 Big Endian'),
        ('cp1252', 'ANSI (Windows-1252)'),
        ('latin-1', 'Latin-1'),
    ]

    def __init__(self):
        super().__init__()
        self.ini_file = None
        self.var_file = None
        self.current_encoding = 'utf-8-sig'
        self.var_file_encoding = 'utf-8'
        self.raw_lines = []  # Linhas brutas do arquivo (preserva comentários)
        self.dark_mode = True
        self.config = configparser.ConfigParser(interpolation=None, strict=False)
        self.resolved_vars = {}  # Variáveis Rainmeter resolvidas para uso no canvas
        
        # Sistema de Undo/Redo
        self.undo_stack = QUndoStack(self)
        
        # Bandeira para evitar loops recursivos entre Tree/Editor e Canvas
        self.is_updating_from_canvas = False
        # Controle de salvamento de valores para Undo
        self.last_saved_value = None
        self.value_timer = QTimer(self)
        self.value_timer.setSingleShot(True)
        self.value_timer.timeout.connect(self.push_value_command)
        
        # Gerenciamento de projetos recentes e preferências
        self.settings = QSettings('RainmeterEditor', 'RainmeterEditorAppSettings')
        self.recent_projects = self.settings.value('recent_projects', [])
        
        # Inicializar Idioma
        current_lang = self.settings.value("language", "pt_BR")
        T.set_language(current_lang)

        # Timer de Auto-Save
        self.auto_save_timer = QTimer(self)
        self.auto_save_timer.timeout.connect(self.auto_save_file)
        self.configure_auto_save()
        
        # Rastrear qual editor foi usado por último para inserção de snippets/ativos
        self.last_active_editor = None

        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        self.setWindowTitle('Editor de Arquivos .ini - Rainmeter Skins')
        self.setGeometry(100, 100, 800, 600)

        # Menu
        menubar = self.menuBar()
        
        # Arquivo
        file_menu = menubar.addMenu(_('Arquivo'))

        new_action = QAction(_('Novo'), self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_skin)
        file_menu.addAction(new_action)
        self.add_skin_action = QAction(_('Adicionar Skin ao Projeto'), self)
        self.add_skin_action.triggered.connect(self.add_skin_to_project_action)
        self.add_skin_action.setEnabled(False) # Habilitado apenas se um projeto estiver aberto
        file_menu.addAction(self.add_skin_action)

        file_menu.addSeparator()

        open_action = QAction(_('Abrir'), self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        save_action = QAction(_('Salvar'), self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction(_('Salvar Como'), self)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()

        open_proj_action = QAction(_('Abrir Projeto (.rmproject)'), self)
        open_proj_action.triggered.connect(self.open_project)
        file_menu.addAction(open_proj_action)

        save_proj_action = QAction(_('Salvar Projeto (.rmproject)'), self)
        save_proj_action.triggered.connect(self.save_project)
        file_menu.addAction(save_proj_action)
        
        self.recent_menu = QMenu(_('Projetos Recentes'), self)
        file_menu.addMenu(self.recent_menu)
        self.update_recent_menu()
        
        file_menu.addSeparator()
        
        export_action = QAction(_('Exportar skin (.rmskin)'), self)
        export_action.triggered.connect(self.export_rmskin)
        file_menu.addAction(export_action)

        # Formatação
        format_menu = menubar.addMenu(_('Formatação'))
        encoding_menu = format_menu.addMenu(_('Codificação'))
        self.encoding_action_group = QActionGroup(self)
        self.encoding_action_group.setExclusive(True)
        self.encoding_actions = {}
        for encoding, label in self.SUPPORTED_ENCODINGS:
            action = QAction(f'Codificação em {label}', self)
            action.setCheckable(True)
            action.triggered.connect(lambda checked, enc=encoding: self.set_file_encoding(enc))
            self.encoding_action_group.addAction(action)
            self.encoding_actions[encoding] = action
            encoding_menu.addAction(action)
        self.update_encoding_menu()

        # Editar
        edit_menu = menubar.addMenu(_('Editar'))

        undo_action = self.undo_stack.createUndoAction(self, _('Desfazer'))
        undo_action.setShortcut('Ctrl+Z')
        edit_menu.addAction(undo_action)

        redo_action = self.undo_stack.createRedoAction(self, _('Refazer'))
        redo_action.setShortcut('Ctrl+Y')
        edit_menu.addAction(redo_action)
        
        edit_menu.addSeparator()
        
        duplicate_action = QAction(_('Duplicar Item'), self)
        duplicate_action.setShortcut(QKeySequence("Ctrl+D"))
        duplicate_action.triggered.connect(self.duplicate_item)
        edit_menu.addAction(duplicate_action)
        
        delete_action = QAction(_('Excluir Item'), self)
        delete_action.setShortcut(QKeySequence("Del"))
        delete_action.triggered.connect(self.delete_current_item)
        edit_menu.addAction(delete_action)
        
        edit_menu.addSeparator()
        
        pref_action = QAction(_('Preferências'), self)
        pref_action.setShortcut('Ctrl+P')
        pref_action.triggered.connect(self.open_preferences)
        edit_menu.addAction(pref_action)

        # Exibir
        view_menu = menubar.addMenu(_('Exibir'))
        
        # Modo Escuro
        self.dark_mode_action = QAction(_('Modo Escuro'), self, checkable=True)
        self.dark_mode_action.setChecked(self.dark_mode)
        self.dark_mode_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.dark_mode_action)
        
        # Visualizador de Log
        log_action = QAction(_('Visualizador de Log'), self)
        log_action.triggered.connect(self.show_log_viewer)
        view_menu.addAction(log_action)

        view_menu.addSeparator()

        self.show_boundary_action = QAction(_('Exibir Limites da Skin'), self, checkable=True)
        self.show_boundary_action.setChecked(True)
        self.show_boundary_action.triggered.connect(self.toggle_boundary)
        view_menu.addAction(self.show_boundary_action)

        self.show_grid_action = QAction(_('Exibir Grade'), self, checkable=True)
        self.show_grid_action.setChecked(False)
        self.show_grid_action.triggered.connect(self.toggle_grid)
        view_menu.addAction(self.show_grid_action)

        self.snap_to_grid_action = QAction(_('Encaixe Automático'), self, checkable=True)
        self.snap_to_grid_action.setChecked(False)
        self.snap_to_grid_action.triggered.connect(self.toggle_snap)
        view_menu.addAction(self.snap_to_grid_action)

        # Ajuda
        help_menu = menubar.addMenu(_('Ajuda'))
        
        doc_action = QAction(_('Documentação e Atalhos'), self)
        doc_action.triggered.connect(self.show_help_dialog)
        help_menu.addAction(doc_action)

        # Janela central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Tabs principais
        self.tabs = QTabWidget()
        
        # Aba do Editor e Visualizador
        editor_tab = QWidget()
        editor_layout = QHBoxLayout(editor_tab)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Painel Esquerdo: Árvore + Editor
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(_('Pesquisar seções ou chaves...'))
        self.search_bar.textChanged.connect(self.filter_tree)
        left_layout.addWidget(self.search_bar)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel(_('Seções e Chaves'))
        self.tree.itemClicked.connect(self.on_item_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.tree.setItemDelegate(KeyValueDelegate(self))
        left_layout.addWidget(self.tree)
        
        self.splitter.addWidget(left_panel)

        # Editor de texto para valores
        self.value_editor = RainmeterEdit()
        self.value_editor.setPlaceholderText(_('Selecione uma chave para editar seu valor'))
        self.value_editor.textChanged.connect(self.on_value_changed)
        self.value_editor.focused.connect(lambda: self._set_last_active(self.value_editor))
        self.last_active_editor = self.value_editor # Default
        self.highlighter = IniHighlighter(self.value_editor.document(), dark_mode=self.dark_mode)
        self.splitter.addWidget(self.value_editor)

        editor_layout.addWidget(self.splitter)
        
        # Aba 2: Canvas Visual (WYSIWYG) - Agora com painéis laterais
        self.canvas_panel = QSplitter(Qt.Orientation.Horizontal)
        
        self.layer_panel = LayerPanel()
        self.layer_panel.selection_changed = self.on_layer_selected
        self.layer_panel.visibility_changed = self.on_layer_visibility_changed
        self.layer_panel.lock_changed = self.on_layer_lock_changed
        self.layer_panel.order_changed = self.on_layer_order_changed
        self.layer_panel.add_requested = self.on_layer_add_requested
        self.layer_panel.remove_requested = self.on_layer_remove_requested
        self.layer_panel.rename_requested = self.on_layer_rename_requested
        self.layer_panel.duplicate_requested = self.on_layer_duplicate_requested
        self.layer_panel.set_theme(self.dark_mode)
        
        self.canvas_widget = VisualCanvas(dark_mode=self.dark_mode)
        self.canvas_widget.item_moved_signal = self.canvas_item_moved
        self.canvas_widget.item_selected_signal = self.on_canvas_item_selected
        self.canvas_widget.add_requested_signal = self.on_canvas_add_requested
        self.canvas_widget.remove_requested_signal = self.on_canvas_remove_requested
        self.canvas_widget.duplicate_requested_signal = self.on_canvas_duplicate_requested
        self.canvas_widget.multi_move_signal = self.on_canvas_multi_moved
        self.canvas_widget.remove_multiple_signal = self.on_canvas_remove_multiple
        
        self.prop_panel = PropertyPanel()
        self.prop_panel.property_changed = self.on_property_edited
        self.prop_panel.set_theme(self.dark_mode)
        
        self.canvas_container = QWidget()
        canvas_cont_layout = QVBoxLayout(self.canvas_container)
        canvas_cont_layout.setContentsMargins(0, 0, 0, 0)
        canvas_cont_layout.setSpacing(0)
        
        # Mini barra de ferramentas do Canvas
        canvas_toolbar = QHBoxLayout()
        canvas_toolbar.setContentsMargins(5, 5, 5, 5)
        
        self.btn_fit = QPushButton(_("Ajustar"))
        self.btn_fit.setToolTip(_("Ajustar à Tela"))
        self.btn_fit.clicked.connect(self.canvas_widget.fit_to_view)
        
        self.chk_snap = QPushButton(_("Encaixe"))
        self.chk_snap.setCheckable(True)
        self.chk_snap.setChecked(False)
        self.chk_snap.setFixedWidth(80)
        self.chk_snap.clicked.connect(self.toggle_snap)
        
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setFixedWidth(30)
        self.btn_zoom_in.clicked.connect(self.canvas_widget.zoom_in)
        
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_out.setFixedWidth(30)
        self.btn_zoom_out.clicked.connect(self.canvas_widget.zoom_out)
        
        canvas_toolbar.addWidget(self.btn_fit)
        canvas_toolbar.addWidget(self.chk_snap)
        canvas_toolbar.addSpacing(10)
        canvas_toolbar.addWidget(self.btn_zoom_in)
        canvas_toolbar.addWidget(self.btn_zoom_out)
        canvas_toolbar.addStretch()
        
        canvas_cont_layout.addLayout(canvas_toolbar)
        canvas_cont_layout.addWidget(self.canvas_widget)
        
        self.canvas_panel.addWidget(self.layer_panel)
        self.canvas_panel.addWidget(self.canvas_container)
        self.canvas_panel.addWidget(self.prop_panel)
        
        self.canvas_panel.setSizes([200, 600, 250])
        self.canvas_panel.setStretchFactor(0, 0)
        self.canvas_panel.setStretchFactor(1, 1)
        self.canvas_panel.setStretchFactor(2, 0)

        # Aba 3: Variáveis Globais (@Resources)
        self.var_widget = QWidget()
        var_layout = QVBoxLayout(self.var_widget)

        # Seletor de arquivo .inc
        var_file_row = QHBoxLayout()
        var_file_row.addWidget(QLabel(_("Arquivo:")))
        self.var_file_combo = QComboBox()
        self.var_file_combo.setMinimumWidth(220)
        self.var_file_combo.currentIndexChanged.connect(self._on_var_file_selected)
        var_file_row.addWidget(self.var_file_combo, 1)
        var_layout.addLayout(var_file_row)

        self.var_editor = RainmeterEdit()
        self.var_editor.setPlaceholderText(_('Selecione um arquivo .inc acima...'))
        self.var_editor.focused.connect(lambda: self._set_last_active(self.var_editor))
        self.var_highlighter = IniHighlighter(self.var_editor.document(), dark_mode=self.dark_mode)
        var_layout.addWidget(self.var_editor)

        self.btn_save_vars = QPushButton(_("Salvar Variáveis Globais"))
        self.btn_save_vars.clicked.connect(self.save_variables_file)
        var_layout.addWidget(self.btn_save_vars)

        # Aba 4: Gerenciador de Ativos (@Resources)
        self.asset_tab = AssetManager(dark_mode=self.dark_mode)

        # Aba 5: Snippets (Modelos)
        self.snippet_tab = SnippetManager(dark_mode=self.dark_mode)

        # Adicionar todas as abas ao TabWidget
        self.tabs.addTab(editor_tab, _('Editor de Skin'))
        self.tabs.addTab(self.canvas_panel, _('Canvas Visual'))
        self.tabs.addTab(self.var_widget, _('Variáveis Globais (@Resources)'))
        self.tabs.addTab(self.asset_tab, _('Ativos (@Resources)'))
        self.tabs.addTab(self.snippet_tab, _('Snippets (Modelos)'))

        main_layout.addWidget(self.tabs)



        # Instância persistente do Log Viewer (janela independente)
        self.log_window = None

        # Botões da skin (no rodapé)
        button_layout = QHBoxLayout()
        save_button = QPushButton('Salvar')
        save_button.clicked.connect(self.save_file)
        button_layout.addWidget(save_button)

        add_section_button = QPushButton('Adicionar Seção')
        add_section_button.clicked.connect(self.add_section)
        button_layout.addWidget(add_section_button)

        add_key_button = QPushButton('Adicionar Chave')
        add_key_button.clicked.connect(self.add_key)
        button_layout.addWidget(add_key_button)



        refresh_button = QPushButton('Atualizar Skin')
        refresh_button.clicked.connect(self.refresh_skin)
        button_layout.addWidget(refresh_button)

        bang_btn = QPushButton('Gerador de Bangs')
        bang_btn.clicked.connect(self.open_bang_generator)
        button_layout.addWidget(bang_btn)

        main_layout.addLayout(button_layout)

    def toggle_theme(self):
        self.dark_mode = self.dark_mode_action.isChecked()
        self.apply_theme()
        if self.ini_file:
            self.update_tree()
        
        # Aplicar tema na janela de log se estiver aberta
        if self.log_window:
            self.log_window.setStyleSheet(self.styleSheet())

    def toggle_boundary(self):
        show = self.show_boundary_action.isChecked()
        self.canvas_widget.set_show_boundary(show)

    def toggle_grid(self):
        show = self.show_grid_action.isChecked()
        self.canvas_widget.set_show_grid(show)

    def toggle_snap(self):
        # Sincronizar os dois controles (menu e botão)
        sender = self.sender()
        is_checked = sender.isChecked()
        
        self.snap_to_grid_action.setChecked(is_checked)
        self.chk_snap.setChecked(is_checked)
        self.canvas_widget.set_snap_to_grid(is_checked)

    def open_preferences(self):
        dialog = PreferencesDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            # Apply immediate settings if OK was clicked
            self.configure_auto_save()
            QMessageBox.information(
                self, "Preferências salvas",
                "Suas preferências foram salvas.\nAlgumas alterações de idioma requerem a reinicialização do aplicativo para ter o efeito total."
            )

    def show_help_dialog(self):
        dialog = HelpDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()

    def configure_auto_save(self):
        is_enabled = self.settings.value("auto_save_enabled", False, type=bool)
        interval = self.settings.value("auto_save_interval", 300000, type=int)
        
        if is_enabled:
            self.auto_save_timer.start(interval)
        else:
            self.auto_save_timer.stop()

    def auto_save_file(self):
        if self.ini_file:
            print(f"Auto-saving file: {self.ini_file}")
            self.save_file(silent=True)

    def apply_theme(self):
        if self.dark_mode:
            qss = """
                QMainWindow, QWidget {
                    background-color: #1e1e1e;
                    color: #e0e0e0;
                }
                QTreeWidget, QTextEdit {
                    background-color: #252526;
                    border: 1px solid #3e3e3e;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 10pt;
                }
                QPushButton {
                    background-color: #333333;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #007acc;
                    border: 1px solid #0098ff;
                }
                QMenuBar {
                    background-color: #2d2d2d;
                    color: #ffffff;
                }
                QMenuBar::item:selected {
                    background-color: #3e3e3e;
                }
                QMenu {
                    background-color: #2d2d2d;
                    color: #ffffff;
                    border: 1px solid #454545;
                }
                QMenu::item:selected {
                    background-color: #007acc;
                }
                QHeaderView::section {
                    background-color: #333333;
                    color: #ffffff;
                    padding: 4px;
                    border: 1px solid #1e1e1e;
                }
                QSplitter::handle {
                    background-color: #3e3e3e;
                }
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #ffffff;
                    border: 1px solid #555555;
                    padding: 4px;
                    border-radius: 2px;
                    margin-bottom: 2px;
                }
                QCheckBox {
                    color: #e0e0e0;
                    spacing: 5px;
                }
                QCheckBox::indicator {
                    width: 15px;
                    height: 15px;
                    background-color: #3c3c3c;
                    border: 1px solid #555555;
                    border-radius: 3px;
                }
                QCheckBox::indicator:checked {
                    background-color: #007acc;
                }
                QTabWidget::pane { border: 1px solid #3e3e3e; }
                QTabBar::tab {
                    background: #2d2d2d;
                    color: #bbbbbb;
                    padding: 8px;
                }
                QTabBar::tab:selected {
                    background: #1e1e1e;
                    color: #ffffff;
                }
            """
        else:
            qss = """
                QMainWindow, QWidget {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QTreeWidget, QTextEdit {
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
                    font-family: 'Consolas', 'Courier New', monospace;
                    font-size: 10pt;
                }
                QPushButton {
                    background-color: #e1e1e1;
                    color: #000000;
                    border: 1px solid #adadad;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #cfe5ff;
                    border: 1px solid #007acc;
                }
                QMenuBar {
                    background-color: #f0f0f0;
                    color: #000000;
                }
                QMenu {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                }
                QLineEdit {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #cccccc;
                    padding: 4px;
                }
                QCheckBox {
                    color: #000000;
                }
                QTabWidget::pane { border: 1px solid #cccccc; }
                QTabBar::tab {
                    background: #e1e1e1;
                    color: #000000;
                    padding: 8px;
                }
                QTabBar::tab:selected {
                    background: #ffffff;
                }
            """
        self.setStyleSheet(qss)
        
        # Aplicar tema aos widgets filhos
        self.layer_panel.set_theme(self.dark_mode)
        self.prop_panel.set_theme(self.dark_mode)
        self.asset_tab.set_theme(self.dark_mode)
        self.canvas_widget.set_theme(self.dark_mode)
        self.snippet_tab.set_theme(self.dark_mode)
        
        # Atualizar highlighters
        if hasattr(self, 'highlighter'):
            self.highlighter.set_theme(self.dark_mode)
        if hasattr(self, 'var_highlighter'):
            self.var_highlighter.set_theme(self.dark_mode)


    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Abrir arquivo .ini', '', 'Arquivos INI (*.ini);;Todos os arquivos (*)'
        )
        if file_path:
            self.load_ini_file(file_path)

    def new_skin(self):
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
                QMessageBox.information(self, "Sucesso", f"Skin '{data['name']}' criada com sucesso!")
                self.load_ini_file(result)
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao criar skin: {result}")

    def add_skin_to_project_action(self):
        if not self.var_file:
            QMessageBox.warning(self, "Aviso", "Não há um projeto com a pasta @Resources aberto.")
            return
            
        # O project_path é o pai da pasta atual ou do @Resources
        resources_dir = os.path.dirname(self.var_file)
        project_path = os.path.dirname(resources_dir)
        
        dialog = AddSkinDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            skin_name = dialog.get_skin_name()
            success, result = add_skin_to_project(project_path, skin_name)
            if success:
                reply = QMessageBox.question(
                    self, 'Skin Adicionada',
                    f"Skin '{skin_name}' adicionada com sucesso ao projeto!\nDeseja abrir esta skin agora?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.load_ini_file(result)
            else:
                QMessageBox.critical(self, "Erro", f"Erro ao adicionar skin: {result}")

    def load_ini_file(self, file_path):
        # Resetar configuração e histórico de undo para evitar mesclagem e confusão
        self.config = configparser.ConfigParser(interpolation=None, strict=False)
        self.undo_stack.clear()
        self.raw_lines = []
        
        success = False
        last_error = ""
        used_enc = self.current_encoding

        for enc, _label in self.SUPPORTED_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                # Alimentar o configparser com o conteúdo lido
                self.config.read_string(content)
                # Armazenar linhas brutas para preservação de comentários
                self.raw_lines = content.splitlines(keepends=True)
                # Garantir que a última linha tem \n
                if self.raw_lines and not self.raw_lines[-1].endswith('\n'):
                    self.raw_lines[-1] += '\n'
                used_enc = enc
                success = True
                break
            except (UnicodeDecodeError, Exception) as e:
                last_error = str(e)
                # Limpar config parcial antes de tentar próximo encoding
                self.config = configparser.ConfigParser(interpolation=None, strict=False)
                continue
        
        if not success:
            QMessageBox.critical(self, 'Erro', f'Não foi possível decodificar o arquivo: {last_error}')
            return

        self.ini_file = file_path
        self.current_encoding = used_enc
        self.update_encoding_menu()
        
        # Tentar carregar variáveis globais e ativos ANTES do update_tree
        # para que o synchronize_canvas tenha os caminhos resolvidos
        self.var_file = find_variables_file(file_path)
        
        # Construir dicionário de variáveis resolvidas para o canvas
        self._build_resolved_vars()
        
        self.update_tree()
        self.setWindowTitle(f'Editor de Arquivos .ini - {os.path.basename(file_path)}')
        
        # Atualizar gerenciador de ativos
        if self.var_file:
            resources_dir = os.path.dirname(self.var_file)
            self.asset_tab.set_resources_path(resources_dir)

        else:
            self.asset_tab.set_resources_path(None)


        # Preencher combobox com todos os .inc em @Resources
        inc_files = find_inc_files(file_path)
        self.var_file_combo.blockSignals(True)
        self.var_file_combo.clear()
        for inc_path in inc_files:
            self.var_file_combo.addItem(os.path.basename(inc_path), inc_path)
        self.var_file_combo.blockSignals(False)

        if inc_files:
            self.add_skin_action.setEnabled(True)
            # Selecionar Variables.inc por padrão, se existir
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

    def update_tree(self):
        self.tree.clear()
        self.current_item = None
        
        # Cores para o "Highlighter" da Árvore
        if self.dark_mode:
            color_section = QColor("#da70d6") # Orchid
            color_key = QColor("#9cdcfe")     # Light Blue
            color_var = QColor("#4ec9b0")     # Aquamarine
            color_num = QColor("#b5cea8")     # Light Green
            color_comment = QColor("#6a9955") # Verde escuro (estilo comentario)
            default_text_color = QColor("#cccccc")
        else:
            color_section = QColor("#800080") # Purple
            color_key = QColor("#0000ff")     # Blue
            color_var = QColor("#008080")     # Teal
            color_num = QColor("#008000")     # Green
            color_comment = QColor("#607d3a") # Verde escuro claro
            default_text_color = QColor("#000000")

        # Pré-processar raw_lines para mapear comentários por seção
        # Estrutura: {section_name: [(line_index, comment_text), ...], '__pre__': [...], '__post_section__': []}
        # '__pre__' = comentários antes de qualquer seção
        # chave de seção = comentários dentro daquela seção
        comments_by_section = {}  # section -> lista de (line_index, text)
        _current_sec = '__pre__'
        _pending_comments = []  # acumula até achar a seção real
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
            elif stripped:  # linha de chave — "commit" os pending to current section
                if _pending_comments:
                    comments_by_section.setdefault(_current_sec, []).extend(_pending_comments)
                    _pending_comments = []
        # Sobras no final
        if _pending_comments:
            comments_by_section.setdefault(_current_sec, []).extend(_pending_comments)

        def _add_comment_items(parent_item, section_name):
            """Adiciona filhos de comentário do raw_lines para a seção dada."""
            for line_idx, text in comments_by_section.get(section_name, []):
                c_item = QTreeWidgetItem([text])
                c_item.setData(0, Qt.ItemDataRole.UserRole, ('comment', section_name, line_idx))
                c_item.setForeground(0, color_comment)
                font = c_item.font(0)
                font.setItalic(True)
                c_item.setFont(0, font)
                # Não é selecionável para edição de valor
                c_item.setFlags(c_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                parent_item.addChild(c_item)

        for section_name in self.config.sections():
            section_item = QTreeWidgetItem([section_name])
            section_item.setData(0, Qt.ItemDataRole.UserRole, ('section', section_name))
            section_item.setForeground(0, color_section)
            self.tree.addTopLevelItem(section_item)

            # Mostrar comentários da seção antes das chaves
            _add_comment_items(section_item, section_name)

            for key, value in self.config.items(section_name):
                display_text = f'{key} = {value}'
                key_item = QTreeWidgetItem([display_text])
                key_item.setData(0, Qt.ItemDataRole.UserRole, ('key', section_name, key))
                section_item.addChild(key_item)

        # Adicionar seção DEFAULT se existir
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
        # Atualizar vars resolvidas sempre que a árvore for atualizada (por ex. após edição de chave)
        self._build_resolved_vars()
        if not self.is_updating_from_canvas:
            self.synchronize_canvas()

    def _build_resolved_vars(self):
        """Constrói um dicionário de variáveis Rainmeter resolvidas a partir do [Variables] do INI
        e de arquivos incluídos via @Include (ex: Variables.inc)."""
        self.resolved_vars = {}
        encodings = ['utf-8-sig', 'utf-16', 'cp1252']
        
        def _read_vars_from_content(content):
            """Extrai chave=valor da seção [Variables] de um conteúdo INI."""
            temp = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                temp.read_string(content)
                if temp.has_section('Variables'):
                    for k, v in temp.items('Variables'):
                        self.resolved_vars[k.lower()] = v
            except Exception:
                pass
        
        def _read_file_content(path):
            for enc in encodings:
                try:
                    with open(path, 'r', encoding=enc) as f:
                        return f.read()
                except (UnicodeDecodeError, OSError):
                    continue
            return ''
        
        # 1. Ler seção [Variables] do próprio INI
        if self.config.has_section('Variables'):
            for k, v in self.config.items('Variables'):
                self.resolved_vars[k.lower()] = v
        
        # 2. Processar @Include do INI principal para ler arquivos externos
        if self.ini_file:
            ini_dir = os.path.dirname(self.ini_file)
            # Tentar ler @Include, @Include2, @Include3... do próprio config
            for section in self.config.sections():
                for key_candidate in ['@include', '@include2', '@include3', '@include4', '@include5']:
                    # configparser normaliza keys para lowercase
                    inc_path_raw = self.config.get(section, key_candidate, fallback=None)
                    if inc_path_raw:
                        # Resolver #@# (resources dir)
                        if self.var_file:
                            res_dir = os.path.dirname(self.var_file)
                            inc_path_raw = inc_path_raw.replace('#@#', res_dir + os.sep)
                        else:
                            inc_path_raw = inc_path_raw.replace('#@#', ini_dir + os.sep + '@Resources' + os.sep)
                        if os.path.exists(inc_path_raw):
                            _read_vars_from_content(_read_file_content(inc_path_raw))
        
        # 3. Se temos var_file explícito, ler também
        if self.var_file and os.path.exists(self.var_file):
            _read_vars_from_content(_read_file_content(self.var_file))
        
        # 4. Resolver referências cruzadas entre variáveis (ex: size=#SizeValue#, sizevalue=0.60)
        # Fazemos múltiplas passagens até o dicionário convergir (sem mais mudanças)
        import re
        for _pass in range(6):
            changed = False
            for k, v in self.resolved_vars.items():
                if '#' in v:
                    def _sub(m):
                        return self.resolved_vars.get(m.group(1).lower(), m.group(0))
                    new_v = re.sub(r'#([^#]+)#', _sub, v)
                    if new_v != v:
                        self.resolved_vars[k] = new_v
                        changed = True
            if not changed:
                break

    def _resolve_props(self, props):
        """Substitui variáveis #VarName# nos valores das propriedades e resolve #@#."""
        import re
        resolved = {}
        res_dir = ''
        if self.var_file:
            res_dir = os.path.dirname(self.var_file)
        elif self.ini_file:
            res_dir = os.path.join(os.path.dirname(self.ini_file), '@Resources')
        
        def _replace_vars(val, depth=0):
            if depth > 5 or not isinstance(val, str):
                return val
            # Substituir #@# pelo caminho de recursos
            val = val.replace('#@#', res_dir + os.sep if res_dir else '')
            # Substituir cada #VarName# pelo valor da variável (case-insensitive)
            def _sub(match):
                var_name = match.group(1).lower()
                return self.resolved_vars.get(var_name, match.group(0))
            new_val = re.sub(r'#([^#]+)#', _sub, val)
            # Se ainda há variáveis não resolvidas e o valor mudou, tentar de novo
            if new_val != val and '#' in new_val:
                return _replace_vars(new_val, depth + 1)
            return new_val
        
        for k, v in props.items():
            resolved[k] = _replace_vars(v)
        return resolved

    def synchronize_canvas(self):
        self.canvas_widget.clear_canvas()
        if not self.ini_file:
            return

        # Background da seção [Rainmeter]
        if self.config.has_section('Rainmeter'):
            raw_bg = self.config.get('Rainmeter', 'Background', fallback='')
            bg_mode_str = self.config.get('Rainmeter', 'BackgroundMode', fallback='2')
            solid_color = self.config.get('Rainmeter', 'SolidColor', fallback=None)
            try:
                bg_mode = int(bg_mode_str)
            except ValueError:
                bg_mode = 2

            # Resolver #@# e variáveis no caminho
            resolved_bg = self._resolve_props({'bg': raw_bg}).get('bg', raw_bg)
            bg_path = ''
            if resolved_bg:
                if not os.path.isabs(resolved_bg):
                    bg_path = os.path.join(os.path.dirname(self.ini_file), resolved_bg)
                else:
                    bg_path = resolved_bg

            self.canvas_widget.set_skin_background(bg_path, bg_mode, solid_color)

        meters_data = []
        prev_item = None
        # Percorrer todas as seções em busca de Meters
        for section in self.config.sections():
            if self.config.has_option(section, 'Meter'):
                is_hidden = self.config.get(section, 'Hidden', fallback='0') != '1'
                # Usar is_locked como meta ou por comentário depois, por hora apenas inicializa False
                meters_data.append({'section': section, 'visible': is_hidden, 'locked': False})
                
                # Se estiver oculto, não adiciona no canvas
                if not is_hidden:
                    continue
                    
                meter_type = self.config.get(section, 'Meter')
                # Coletar propriedades brutas
                raw_props = {}
                for key, val in self.config.items(section):
                    raw_props[key.lower()] = val
                
                # Resolver variáveis (#VarName#, #@#, etc)
                props = self._resolve_props(raw_props)
                
                item = self.canvas_widget.add_meter(section, meter_type, props, prev_item=prev_item)
                if item:
                    prev_item = item
        
        self.layer_panel.set_meters(meters_data)

    def on_layer_selected(self, section):
        # Selecionar item no canvas (precisamos implementar esse método no VisualCanvas)
        self.canvas_widget.select_item_by_section(section)
        # Atualizar painel de propriedades
        self.update_prop_panel(section)

    def on_layer_visibility_changed(self, section, is_visible):
        val = '0' if is_visible else '1'
        old_val = self.config.get(section, 'Hidden', fallback='0')
        if old_val != val:
            command = ChangeValueCommand(self, section, 'Hidden', old_val, val)
            self.undo_stack.push(command)
            # A sinalização cuidará de atualizar a UI e sincronizar o canvas
            
    def on_layer_lock_changed(self, section, is_locked):
        self.canvas_widget.set_item_locked(section, is_locked)
        
    def on_layer_order_changed(self, new_order):
        # Mover as seções do config para refletir a nova ordem
        # Aqui, idealmente, criariamos um ReorderSectionsCommand. Por hora, apenas realocando.
        from collections import OrderedDict
        new_sections = OrderedDict()
        
        # 1. Manter seções que NÃO são meters no início ou na ordem original
        for sec in self.config.sections():
            if not self.config.has_option(sec, 'Meter'):
                new_sections[sec] = self.config._sections[sec]
                
        # 2. Adicionar as seções reordenadas dos meters
        for sec in new_order:
            if sec in self.config._sections:
                new_sections[sec] = self.config._sections[sec]
                
        # 3. Adicionar possíveis meters que não estavam no painel (fallback de segurança)
        for sec in self.config.sections():
            if sec not in new_sections:
                new_sections[sec] = self.config._sections[sec]
                
        self.config._sections = new_sections
        self.update_tree()
        self.synchronize_canvas()
        
    def on_layer_add_requested(self):
        # Usa a mesma lógica do context menu de adicionar (neste caso, pergunta coordenadas ou define padrão)
        # Por padrão: 0, 0, e pede o tipo. Para simplificar, chamar on_canvas_add_requested padronizado.
        # Mas não sabemos o tipo. Vamos apenas invocar o menu na tela ou simular adicao
        self.on_canvas_add_requested(0, 0, 'String')
        
    def on_layer_remove_requested(self, section):
        self.on_canvas_remove_requested(section)

    def on_layer_rename_requested(self, section):
        self.rename_section(section_name=section)
        
    def on_layer_duplicate_requested(self, section):
        self.duplicate_item(section_name=section)

    def on_canvas_item_selected(self, section):
        # Selecionar na lista de camadas
        self.layer_panel.select_meter(section)
        # Atualizar painel de propriedades
        self.update_prop_panel(section)

    def update_prop_panel(self, section):
        if self.config.has_section(section):
            props = {}
            for key, val in self.config.items(section):
                props[key.lower()] = val
            # Seções sem Meter= são candidatas a MeterStyle
            style_sections = [
                s for s in self.config.sections()
                if s != section and not self.config.has_option(s, 'Meter')
            ]
            self.prop_panel.set_available_styles(style_sections)
            self.prop_panel.set_properties(section, props)

    def on_property_edited(self, section, key, value):
        # Aplicar mudança no arquivo INI usando o sistema de desfazer global
        old_val = self.config.get(section, key, fallback='')
        if old_val != value:
            command = ChangeValueCommand(self, section, key, old_val, value)
            self.undo_stack.push(command)

    def canvas_item_moved(self, section, x, y):
        if self.is_updating_from_canvas:
            return
            
        if self.config.has_section(section):
            old_x = self.config.get(section, 'X', fallback='0')
            old_y = self.config.get(section, 'Y', fallback='0')
            
            if str(x) != old_x or str(y) != old_y:
                command = MoveItemCommand(self, section, old_x, old_y, str(x), str(y))
                self.undo_stack.push(command)

    def on_canvas_multi_moved(self, moves):
        """Chamado quando múltiplos itens foram movidos de uma vez no canvas."""
        if self.is_updating_from_canvas:
            return
        self.undo_stack.beginMacro("Mover múltiplos itens")
        for section, x, y in moves:
            if self.config.has_section(section):
                old_x = self.config.get(section, 'X', fallback='0')
                old_y = self.config.get(section, 'Y', fallback='0')
                if str(x) != old_x or str(y) != old_y:
                    self.undo_stack.push(MoveItemCommand(self, section, old_x, old_y, str(x), str(y)))
        self.undo_stack.endMacro()

    def on_canvas_remove_multiple(self, sections):
        """Chamado quando múltiplos itens são excluídos via canvas."""
        if not sections:
            return
        self.undo_stack.beginMacro(f"Excluir {len(sections)} itens")
        for section in sections:
            if self.config.has_section(section):
                self.undo_stack.push(DeleteSectionCommand(self, section))
        self.undo_stack.endMacro()

    def on_canvas_add_requested(self, x, y, meter_type):
        if not self.ini_file:
            QMessageBox.warning(self, "Aviso", "Abra ou crie uma skin primeiro.")
            return
            
        section_name, ok = QInputDialog.getText(self, 'Novo Meter', f'Nome da nova seção para {meter_type}:')
        if ok and section_name:
            if self.config.has_section(section_name):
                QMessageBox.warning(self, "Erro", "Esta seção já existe.")
                return
                
            # Usar QUndoStack para agrupar comandos ou criar um comando macro
            self.undo_stack.beginMacro(f"Adicionar {meter_type} pelo Canvas")
            
            # 1. Adicionar seção
            self.undo_stack.push(AddSectionCommand(self, section_name))
            
            # 2. Adicionar tipo de Meter
            self.undo_stack.push(AddKeyCommand(self, section_name, 'Meter', meter_type))
            
            # 3. Adicionar posição
            self.undo_stack.push(AddKeyCommand(self, section_name, 'X', str(x)))
            self.undo_stack.push(AddKeyCommand(self, section_name, 'Y', str(y)))
            
            # 4. Propriedades padrão por tipo
            if meter_type == 'String':
                self.undo_stack.push(AddKeyCommand(self, section_name, 'Text', 'Texto Exemplo'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'FontSize', '12'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'FontColor', '255,255,255,255'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'AntiAlias', '1'))
            elif meter_type == 'Bar':
                self.undo_stack.push(AddKeyCommand(self, section_name, 'W', '100'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'H', '10'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'BarColor', '0,122,204,255'))
            elif meter_type == 'Roundline':
                self.undo_stack.push(AddKeyCommand(self, section_name, 'W', '120'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'H', '120'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'StartAngle', '0'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'RotationAngle', '360'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'LineStart', '20'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'LineLength', '40'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'LineWidth', '8'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'LineColor', '0,180,255,255'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'AntiAlias', '1'))
            elif meter_type == 'Image':
                # Solicitar imagem ao usuário
                img_path, filter_ = QFileDialog.getOpenFileName(
                    self, _('Selecionar Imagem'), '', 'Imagens (*.png *.jpg *.jpeg *.bmp *.gif);;Todos os arquivos (*)'
                )
                
                final_image_name = '#@#Image.png' # Fallback default
                
                if img_path:
                    # Tentar encontrar @Resources para caminho relativo
                    if self.var_file:
                        resources_dir = os.path.dirname(self.var_file)
                        abs_img = os.path.abspath(img_path)
                        abs_res = os.path.abspath(resources_dir)
                        
                        # Verificar se já está dentro de @Resources
                        try:
                            if os.path.commonpath([abs_img, abs_res]) == abs_res:
                                rel_path = os.path.relpath(abs_img, abs_res)
                                final_image_name = f'#@#{rel_path.replace(os.sep, "/")}'
                            else:
                                # Sugerir copiar para @Resources/Images
                                reply = QMessageBox.question(
                                    self, _('Copiar Imagem'),
                                    _('A imagem selecionada está fora da pasta @Resources. Deseja copiá-la para @Resources/Images?'),
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                                )
                                if reply == QMessageBox.StandardButton.Yes:
                                    target_dir = os.path.join(resources_dir, 'Images')
                                    if not os.path.exists(target_dir):
                                        os.makedirs(target_dir)
                                    target_path = os.path.join(target_dir, os.path.basename(img_path))
                                    try:
                                        import shutil
                                        shutil.copy2(img_path, target_path)
                                        final_image_name = f'#@#Images/{os.path.basename(img_path)}'
                                    except Exception as e:
                                        QMessageBox.critical(self, _('Erro'), f'Erro ao copiar imagem: {str(e)}')
                                        final_image_name = img_path # Usa absoluto se falhar
                                else:
                                    final_image_name = img_path # Usa absoluto se o usuário preferir não copiar
                        except ValueError:
                            # Caso commonpath falhe (ex: drives diferentes no Windows)
                            final_image_name = img_path
                    else:
                        final_image_name = img_path # Sem @Resources, usa absoluto
                
                self.undo_stack.push(AddKeyCommand(self, section_name, 'W', '50'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'H', '50'))
                self.undo_stack.push(AddKeyCommand(self, section_name, 'ImageName', final_image_name))
            elif meter_type == 'Shape':
                self.undo_stack.push(AddKeyCommand(self, section_name, 'Shape', 'Rectangle 0,0,100,50 | Fill Color 255,255,255,150 | Stroke Color 255,255,255,255 | StrokeWidth 1'))
            
            self.undo_stack.endMacro()

    def on_canvas_remove_requested(self, section):
        self.delete_item(section_name=section)

    def on_canvas_duplicate_requested(self, section):
        if not self.config.has_section(section):
            return
            
        new_name, ok = QInputDialog.getText(self, 'Duplicar Seção', 'Novo nome:', text=f"{section}_Copy")
        if ok and new_name:
            if not self.config.has_section(new_name):
                command = DuplicateSectionCommand(self, section, new_name)
                self.undo_stack.push(command)
                
                # Selecionar o novo item
                self.canvas_widget.select_item_by_section(new_name)
                self.on_canvas_item_selected(new_name)
            else:
                QMessageBox.warning(self, "Aviso", "Esta seção já existe.")

    def filter_tree(self, text):
        text = text.lower()
        for i in range(self.tree.topLevelItemCount()):
            section_item = self.tree.topLevelItem(i)
            section_visible = text in section_item.text(0).lower()
            
            any_key_visible = False
            for j in range(section_item.childCount()):
                key_item = section_item.child(j)
                key_visible = text in key_item.text(0).lower()
                key_item.setHidden(not key_visible)
                if key_visible:
                    any_key_visible = True
            
            section_item.setHidden(not (section_visible or any_key_visible))
            if any_key_visible:
                section_item.setExpanded(True)

    def on_item_clicked(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == 'key':
            _, section, key = data
            if section == 'DEFAULT':
                value = self.config.defaults().get(key, '')
            else:
                value = self.config.get(section, key, fallback='')
            
            # Bloquear sinais para evitar que o on_value_changed dispare 
            # enquanto estamos trocando de item (o que causaria "vazamento" de valor)
            self.value_editor.blockSignals(True)
            self.value_editor.setPlainText(value)
            self.value_editor.blockSignals(False)
            
            self.current_item = item
            self.last_saved_value = value
        else:
            self.value_editor.blockSignals(True)
            self.value_editor.clear()
            self.value_editor.blockSignals(False)
            self.current_item = None
            self.last_saved_value = None

    def on_value_changed(self):
        if hasattr(self, 'current_item') and self.current_item and not sip.isdeleted(self.current_item):
            # Iniciar timer para não inundar o.undo stack a cada tecla
            self.value_timer.start(1000)
            
            data = self.current_item.data(0, Qt.ItemDataRole.UserRole)
            if data and data[0] == 'key':
                _, section, key = data
                new_value = self.value_editor.toPlainText()
                
                # Atualizar o config parser em tempo real (para UI e Preview)
                # mas sem empurrar para o.undo stack ainda
                if section == 'DEFAULT':
                    self.config.defaults()[key] = new_value
                else:
                    self.config.set(section, key, new_value)
                
                # Atualizar o texto exibido na árvore (o delegate recoloriza automaticamente)
                self.current_item.setText(0, f'{key} = {new_value}')

    def push_value_command(self):
        if not self.current_item or sip.isdeleted(self.current_item):
            return
            
        data = self.current_item.data(0, Qt.ItemDataRole.UserRole)
        if not data or data[0] != 'key':
            return
            
        _, section, key = data
        new_value = self.value_editor.toPlainText()
        
        if new_value != self.last_saved_value:
            command = ChangeValueCommand(self, section, key, self.last_saved_value, new_value)
            self.undo_stack.push(command)
            self.last_saved_value = new_value



    def refresh_skin(self):
        success, message = refresh_skin(self.ini_file)
        if not success:
            QMessageBox.warning(self, 'Aviso', message)
        else:
            # Não é estritamente necessário mostrar sucesso aqui para não ser intrusivo
            pass

    def open_bang_generator(self):
        dialog = BangGeneratorDialog(self, self.dark_mode)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            bang_result = dialog.get_result()
            
            # Identificar qual editor está ativo
            # Determinar qual editor deve receber o bang
            editor = self.last_active_editor if self.last_active_editor else self.value_editor
            
            # Mudar para a aba correspondente se necessário
            if editor == self.value_editor:
                self.tabs.setCurrentIndex(0)
            elif editor == self.var_editor:
                self.tabs.setCurrentIndex(2) # Aba de Variáveis Globais
                
            # Inserir na posição do cursor
            editor.insertPlainText(bang_result)

    def insert_asset_path(self, path):
        # Determinar qual editor deve receber o caminho
        editor = self.last_active_editor if self.last_active_editor else self.value_editor
        
        # Mudar para a aba correspondente se necessário
        if editor == self.value_editor:
            self.tabs.setCurrentIndex(0)
        elif editor == self.var_editor:
            self.tabs.setCurrentIndex(2) # Aba de Variáveis Globais
            
        editor.insertPlainText(path)
        QMessageBox.information(self, _("Sucesso"), _("Caminho do ativo inserido no editor!"))

    def insert_snippet(self, code):
        """Insere um snippet de forma estruturada na árvore ou como texto no editor."""
        import re
        from io import StringIO
        
        # 1. Verificar se o snippet contém cabeçalhos de seção (ex: [MeterName])
        # Usamos uma busca por '[' no início de qualquer linha
        has_sections = bool(re.search(r'^\[.*\]', code, re.MULTILINE))
        
        if has_sections:
            # MODO ESTRUTURADO: Adicionar novas seções e chaves na árvore
            if not self.ini_file:
                # Fallback para texto se não houver arquivo aberto (ex: Variáveis Globais)
                self._insert_snippet_raw(code)
                return

            snippet_config = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                # Permitir linhas antes da primeira seção (comentários)
                snippet_config.read_string(code)
            except Exception as e:
                # Se falhar o parsing, fallback para texto
                self._insert_snippet_raw(code)
                return
            
            self.undo_stack.beginMacro(_("Inserir Snippet (Estruturado)"))
            for section in snippet_config.sections():
                # Gerar nome único para a seção se já existir
                new_name = section
                counter = 1
                while self.config.has_section(new_name):
                    new_name = f"{section}_{counter}"
                    counter += 1
                
                # Criar a seção e suas chaves via Undo Commands
                self.undo_stack.push(AddSectionCommand(self, new_name))
                for key, value in snippet_config.items(section):
                    self.undo_stack.push(AddKeyCommand(self, new_name, key, value))
            
            self.undo_stack.endMacro()
            self.tabs.setCurrentIndex(0) # Forçar volta para o editor de skin
            QMessageBox.information(self, _("Sucesso"), _("Snippet adicionado como novas seções na árvore!"))
            
        else:
            # MODO DE INSERÇÃO NA SEÇÃO: Se não tem cabeçalho, tenta inserir na seção selecionada
            selected_items = self.tree.selectedItems()
            target_section = None
            
            if selected_items:
                item = selected_items[0]
                data = item.data(0, Qt.ItemDataRole.UserRole)
                if data:
                    # Se for seção, usa ela. Se for chave, usa a seção pai dela.
                    target_section = data[1] if data[0] in ('section', 'key') else None
            
            if target_section and self.tabs.currentIndex() == 0:
                # Parsear o snippet simples (linha por linha key=value)
                self.undo_stack.beginMacro(_("Inserir Snippet na Seção"))
                added_keys = 0
                for line in code.splitlines():
                    line = line.strip()
                    if not line or line.startswith(';'): continue
                    if '=' in line:
                        k, v = line.split('=', 1)
                        self.undo_stack.push(AddKeyCommand(self, target_section, k.strip(), v.strip()))
                        added_keys += 1
                
                self.undo_stack.endMacro()
                if added_keys > 0:
                    QMessageBox.information(self, _("Sucesso"), _("Novas chaves adicionadas à seção selecionada!"))
                    return

            # FALLBACK FINAL: Inserir como texto bruto no editor focado
            self._insert_snippet_raw(code)

    def _insert_snippet_raw(self, code):
        """Fallback para inserir o snippet como texto bruto no editor focado."""
        editor = self.last_active_editor if self.last_active_editor else self.value_editor
        
        # Mudar para a aba correspondente se necessário
        if editor == self.value_editor:
            self.tabs.setCurrentIndex(0)
        elif editor == self.var_editor:
            self.tabs.setCurrentIndex(2) # Aba de Variáveis Globais
            
        editor.insertPlainText(code)
        QMessageBox.information(self, _("Sucesso"), _("Snippet inserido como texto no editor."))

    def _set_last_active(self, editor):
        self.last_active_editor = editor

    def show_log_viewer(self):
        if not self.log_window:
            self.log_window = LogViewer(dark_mode=self.dark_mode)
            self.log_window.setWindowTitle("Rainmeter Log - Independente")
            self.log_window.resize(600, 400)
            # Sincronizar tema inicial
            self.log_window.setStyleSheet(self.styleSheet())
        
        self.log_window.show()
        self.log_window.raise_()
        self.log_window.activateWindow()

    def export_rmskin(self):
        if not self.ini_file:
            QMessageBox.warning(self, "Aviso", "Abra uma skin primeiro para exportar.")
            return
            
        # Detectar a pasta principal da skin (ex: illustro)
        path_parts = os.path.normpath(self.ini_file).split(os.sep)
        skin_root = None
        try:
            for i, part in enumerate(path_parts):
                if part.lower() == 'skins':
                    # A pasta logo após 'Skins' é a raiz da suite (ex: illustro)
                    skin_root = os.sep.join(path_parts[:i+2])
                    break
        except Exception:
            pass
            
        if not skin_root:
            # Fallback: pasta da skin sendo editada
            skin_root = os.path.dirname(self.ini_file)
            
        default_name = os.path.basename(skin_root)
        
        dialog = RmskinExportDialog(self, default_name)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            data = dialog.get_data()
            success, result = package_rmskin(skin_root, data)
            if success:
                QMessageBox.information(self, "Sucesso", f"Skin exportada com sucesso!\nSalva em: {result}")
            else:
                QMessageBox.critical(self, "Erro", f"Falha ao exportar skin: {result}")

    def _on_var_file_selected(self, index):
        if index < 0:
            return
        file_path = self.var_file_combo.itemData(index)
        if not file_path:
            return
        for enc, _label in self.SUPPORTED_ENCODINGS:
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    content = f.read()
                self.var_file = file_path
                self.var_file_encoding = enc
                self.var_editor.setPlainText(content)
                self.btn_save_vars.setEnabled(True)
                var_idx = self.tabs.indexOf(self.var_widget)
                if var_idx != -1:
                    self.tabs.setTabText(var_idx, f"Variáveis ({os.path.basename(file_path)})")
                return
            except (UnicodeDecodeError, OSError):
                continue
        self.var_editor.setPlainText(f"Erro ao ler: {file_path}")
        self.btn_save_vars.setEnabled(False)

    def save_variables_file(self):
        if hasattr(self, 'var_file') and self.var_file:
            print(f"Tentando salvar variáveis em: {self.var_file}")
            try:
                create_backup(self.var_file)
                with open(self.var_file, 'w', encoding=self.current_encoding or self.var_file_encoding) as f:
                    f.write(self.var_editor.toPlainText())
                print("Salvo com sucesso!")
                QMessageBox.information(self, 'Sucesso', 'Variáveis globais salvas com sucesso!')
            except Exception as e:
                print(f"Erro ao salvar: {e}")
                QMessageBox.critical(self, 'Erro', f'Erro ao salvar variáveis: {str(e)}')
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum arquivo Variables.inc encontrado para salvar.")

    def _rebuild_from_raw(self):
        """Reconstrói o conteúdo do .ini a partir de raw_lines,
        substituindo valores conforme self.config (edições do usuário),
        preservando comentários e linhas em branco."""
        result = []
        current_section = None           # seção em processamento nas raw_lines
        sections_written = set()         # seções cujo header já foi escrito
        keys_written = {}                # section -> set de chaves já escritas
        # Conjunto de seções que existem no config atual
        existing_sections = set(self.config.sections())
        # Rastrear se estamos dentro de uma seção deletada (para pular suas chaves)
        in_deleted_section = False

        for line in self.raw_lines:
            stripped = line.strip()

            # ----- Linha de comentário ou em branco -----
            if not stripped or stripped.startswith(';') or stripped.startswith('#'):
                if not in_deleted_section:
                    result.append(line)
                continue

            # ----- Cabeçalho de seção -----
            if stripped.startswith('[') and ']' in stripped:
                # Antes de mudar de seção, escrever chaves novas da seção anterior
                if current_section and current_section in existing_sections:
                    for key, val in self.config.items(current_section):
                        if key not in keys_written.get(current_section, set()):
                            result.append(f'{key}={val}\n')
                            keys_written.setdefault(current_section, set()).add(key)

                section_name = stripped[1:stripped.index(']')]
                current_section = section_name

                if section_name in existing_sections:
                    result.append(line)
                    sections_written.add(section_name)
                    keys_written.setdefault(section_name, set())
                    in_deleted_section = False
                else:
                    # Seção foi deletada — pular até próxima seção
                    in_deleted_section = True
                continue

            # ----- Linha key=value -----
            if in_deleted_section:
                continue

            if '=' in stripped and current_section:
                key_raw = stripped.split('=', 1)[0].rstrip()
                key_lower = key_raw.lower()

                if current_section in existing_sections and \
                        self.config.has_option(current_section, key_lower):
                    # Pegar valor atualizado do config
                    val = self.config.get(current_section, key_lower)
                    # Preservar espaçamento original em torno do =
                    eq_idx = line.index('=')
                    lhs = line[:eq_idx]  # inclui espaços/tabs antes do =
                    result.append(f'{lhs}= {val}\n')
                    keys_written.setdefault(current_section, set()).add(key_lower)
                # Se a chave foi deletada, simplesmente a ignoramos
                continue

            # ----- Qualquer outra linha -----
            result.append(line)

        # Escrever chaves novas da última seção processada
        if current_section and current_section in existing_sections:
            for key, val in self.config.items(current_section):
                if key not in keys_written.get(current_section, set()):
                    result.append(f'{key}={val}\n')

        # Escrever seções completamente novas (não presentes em raw_lines)
        for section in self.config.sections():
            if section not in sections_written:
                result.append(f'\n[{section}]\n')
                for key, val in self.config.items(section):
                    result.append(f'{key}={val}\n')

        return ''.join(result)

    def save_file(self, silent=False):
        if not self.ini_file:
            if not silent:
                self.save_file_as()
            return

        try:
            create_backup(self.ini_file)
            content = self._rebuild_from_raw() if self.raw_lines else None
            with open(self.ini_file, 'w', encoding=self.current_encoding) as f:
                if content is not None:
                    f.write(content)
                else:
                    self.config.write(f)  # Fallback se raw_lines estiver vazio
            if not silent:
                QMessageBox.information(
                    self,
                    _('Sucesso'),
                    f'Arquivo salvo com sucesso em {self.encoding_display_name(self.current_encoding)}!'
                )
        except Exception as e:
            if not silent:
                QMessageBox.critical(self, _('Erro'), f'Erro ao salvar arquivo: {str(e)}')

    def save_file_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Salvar arquivo .ini', '', 'Arquivos INI (*.ini);;Todos os arquivos (*)'
        )
        if file_path:
            self.ini_file = file_path
            self.save_file()

    def encoding_display_name(self, encoding):
        for enc, label in self.SUPPORTED_ENCODINGS:
            if enc == encoding:
                return label
        return encoding

    def update_encoding_menu(self):
        if not hasattr(self, 'encoding_actions'):
            return
        for encoding, action in self.encoding_actions.items():
            action.blockSignals(True)
            action.setChecked(encoding == self.current_encoding)
            action.blockSignals(False)

    def set_file_encoding(self, encoding):
        self.current_encoding = encoding
        self.update_encoding_menu()
        if self.ini_file:
            QMessageBox.information(
                self,
                'Codificação atualizada',
                f'O arquivo atual será salvo em {self.encoding_display_name(encoding)}.'
            )

    # --- Funções de Projeto ---

    def save_project(self):
        if not self.ini_file:
            QMessageBox.warning(self, "Aviso", "Não há nenhuma skin aberta para salvar o projeto.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, 'Salvar Projeto', '', 'Arquivos de Projeto Rainmeter (*.rmproject);;Todos os arquivos (*)'
        )
        if not file_path:
            return

        # Montar o estado do projeto
        state = {
            "version": "1.0",
            "last_opened_ini": self.ini_file,
            "dark_mode": self.dark_mode_action.isChecked(),
            "canvas_boundary": self.show_boundary_action.isChecked(),
            "canvas_grid": self.show_grid_action.isChecked()
        }

        success, result = save_project_json(file_path, state)
        if success:
            QMessageBox.information(self, 'Sucesso', 'Projeto salvo com sucesso!')
            self.add_to_recent_projects(file_path)
        else:
            QMessageBox.critical(self, 'Erro', f'Erro ao salvar projeto: {result}')

    def open_project(self, file_path=None):
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, 'Abrir Projeto', '', 'Arquivos de Projeto Rainmeter (*.rmproject);;Todos os arquivos (*)'
            )
            
        if not file_path:
            return

        success, result = load_project_json(file_path)
        if not success:
            QMessageBox.critical(self, 'Erro', f'Falha ao carregar projeto: {result}')
            return

        # Aplicar o estado do projeto
        state = result
        self.add_to_recent_projects(file_path)
        
        # Tema e Interface
        if "dark_mode" in state:
            self.dark_mode_action.setChecked(state["dark_mode"])
            self.toggle_theme()
            
        if "canvas_boundary" in state:
            self.show_boundary_action.setChecked(state["canvas_boundary"])
            self.toggle_boundary()
            
        if "canvas_grid" in state:
            self.show_grid_action.setChecked(state["canvas_grid"])
            self.toggle_grid()
            
        # Abrir o arquivo .ini associado
        ini_path = state.get("last_opened_ini", "")
        if ini_path and os.path.exists(ini_path):
            self.load_ini_file(ini_path)
        else:
            QMessageBox.warning(self, 'Aviso', f'O arquivo original ({ini_path}) não foi encontrado.')

    def update_recent_menu(self):
        self.recent_menu.clear()
        
        # Garantir lista sem nulos/vazios
        valid_projects = [p for p in self.recent_projects if p and os.path.exists(p)]
        
        if not valid_projects:
            empty_action = QAction('Nenhum projeto recente', self)
            empty_action.setEnabled(False)
            self.recent_menu.addAction(empty_action)
            return

        for path in valid_projects[:10]:  # Máximo de 10
            action = QAction(os.path.basename(path), self)
            action.setToolTip(path)
            # Função com default arg para prender o valor do path no loop
            action.triggered.connect(lambda checked, p=path: self.open_project(p))
            self.recent_menu.addAction(action)
            
        self.recent_menu.addSeparator()
        clear_action = QAction('Limpar Histórico', self)
        clear_action.triggered.connect(self.clear_recent_projects)
        self.recent_menu.addAction(clear_action)

    def add_to_recent_projects(self, file_path):
        # Limpar duplicatas
        if file_path in self.recent_projects:
            self.recent_projects.remove(file_path)
            
        # Inserir no topo
        self.recent_projects.insert(0, file_path)
        
        # Salvar nos QSettings
        self.settings.setValue('recent_projects', self.recent_projects[:10])
        self.update_recent_menu()
        
    def clear_recent_projects(self):
        self.recent_projects = []
        self.settings.setValue('recent_projects', [])
        self.update_recent_menu()

    # --- Fim Funções de Projeto ---

    def add_section(self):
        dialog = AutocompleteInputDialog(
            self, 
            title=_('Adicionar Seção'), 
            label=_('Nome da seção:'), 
            keywords=[k for k in RainmeterEdit.KEYWORDS if k.startswith('[')]
        )
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            section_name = dialog.get_text()
            if section_name:
                # Se o usuário não colocou [], colocar para ele se for sugestão de seção
                if not section_name.startswith('['):
                    section_name = f"[{section_name}]"
                
                # Mas o configparser usa nomes SEM colchetes internamente
                section_config_name = section_name.strip('[]')
                
                if not self.config.has_section(section_config_name):
                    command = AddSectionCommand(self, section_config_name)
                    self.undo_stack.push(command)
                else:
                    QMessageBox.warning(self, _('Aviso'), _('Seção já existe!'))

    def add_key(self):
        current_item = self.tree.currentItem()
        if not current_item:
            QMessageBox.warning(self, 'Aviso', 'Selecione uma seção primeiro!')
            return

        data = current_item.data(0, Qt.ItemDataRole.UserRole)
        if data and data[0] == 'section':
            section_name = data[1]
        else:
            # Se selecionou uma chave, pegar a seção pai
            parent = current_item.parent()
            if parent:
                data = parent.data(0, Qt.ItemDataRole.UserRole)
                if data and data[0] == 'section':
                    section_name = data[1]
                else:
                    QMessageBox.warning(self, 'Aviso', 'Selecione uma seção válida!')
                    return
            else:
                QMessageBox.warning(self, 'Aviso', 'Selecione uma seção válida!')
                return

        dialog = AutocompleteInputDialog(
            self, 
            title=_('Adicionar Chave'), 
            label=_('Nome da chave:'),
            keywords=[k.split('=')[0] for k in RainmeterEdit.KEYWORDS if '=' in k]
        )
        dialog.setStyleSheet(self.styleSheet())
        
        if dialog.exec():
            key_name = dialog.get_text()
            if key_name:
                # Se o usuário selecionou algo como "Meter=String", pegar apenas "Meter"
                if '=' in key_name:
                    key_name = key_name.split('=')[0]
                
                if not self.config.has_option(section_name, key_name):
                    command = AddKeyCommand(self, section_name, key_name)
                    self.undo_stack.push(command)
                else:
                    QMessageBox.warning(self, _('Aviso'), _('Chave já existe nesta seção!'))

    def show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        menu = QMenu()
        
        if data[0] == 'section':
            section_name = data[1]
            add_key_action = menu.addAction(_('Adicionar Chave'))
            add_section_action = menu.addAction(_('Adicionar Seção'))
            menu.addSeparator()
            rename_action = menu.addAction(_('Renomear Seção'))
            dup_action = menu.addAction(_('Duplicar Item'))
            del_action = menu.addAction(_('Excluir Item'))
            menu.addSeparator()
            add_comment_action = menu.addAction(_('Adicionar Comentário na Seção'))

            action = menu.exec(self.tree.mapToGlobal(position))
            if action == add_key_action:
                self.tree.setCurrentItem(item)
                self.add_key()
            elif action == add_section_action:
                self.add_section()
            elif action == rename_action:
                self.rename_section()
            elif action == dup_action:
                self.duplicate_item()
            elif action == del_action:
                self.delete_item(item_to_delete=item)
            elif action == add_comment_action:
                self._prompt_add_comment(section_name)

        elif data[0] == 'key':
            add_key_action = menu.addAction(_('Adicionar Chave'))
            add_section_action = menu.addAction(_('Adicionar Seção'))
            menu.addSeparator()
            dup_action = menu.addAction(_('Duplicar Item'))
            del_action = menu.addAction(_('Excluir Item'))
            menu.addSeparator()
            add_comment_action = menu.addAction(_('Adicionar Comentário Acima'))

            action = menu.exec(self.tree.mapToGlobal(position))
            if action == add_key_action:
                self.tree.setCurrentItem(item)
                self.add_key()
            elif action == add_section_action:
                self.add_section()
            elif action == dup_action:
                self.duplicate_item()
            elif action == del_action:
                self.delete_item(item_to_delete=item)
            elif action == add_comment_action:
                # Inserir comentário antes desta chave na seção
                self._prompt_add_comment(data[1])

        elif data[0] == 'comment':
            _kind, section_name, line_idx = data
            add_section_action = menu.addAction(_('Adicionar Seção'))
            menu.addSeparator()
            del_comment_action = menu.addAction(_('Excluir Comentário'))
            add_comment_action = menu.addAction(_('Adicionar Comentário Acima'))

            action = menu.exec(self.tree.mapToGlobal(position))
            if action == add_section_action:
                self.add_section()
            elif action == del_comment_action:
                cmd = DeleteCommentCommand(self, line_idx)
                self.undo_stack.push(cmd)
            elif action == add_comment_action:
                self._prompt_add_comment(section_name, insert_at=line_idx)

    def _prompt_add_comment(self, section_name, insert_at=None):
        """Abre um diálogo para o usuário digitar o texto do comentário e o insere."""
        text, ok = QInputDialog.getText(
            self, _('Adicionar Comentário'),
            _('Texto do comentário (o ; será adicionado automaticamente):'),
            text='; '
        )
        if not ok or not text.strip():
            return

        # Encontrar a posição de inserção no raw_lines
        if insert_at is not None:
            idx = insert_at  # Inserir antes da linha indicada
        else:
            # Inserir no final do bloco da seção
            idx = len(self.raw_lines)
            in_section = False
            for i, raw in enumerate(self.raw_lines):
                stripped = raw.strip()
                if stripped.startswith('[') and ']' in stripped:
                    found_sec = stripped[1:stripped.index(']')]
                    if found_sec == section_name:
                        in_section = True
                    elif in_section:
                        # Chegamos à próxima seção
                        idx = i
                        break
            # Se seção não foi encontrada em raw_lines (seção nova), append ao final

        cmd = AddCommentCommand(self, idx, text)
        self.undo_stack.push(cmd)

    def rename_section(self, section_name=None):
        if section_name is None:
            item = self.tree.currentItem()
            if not item:
                return
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data or data[0] != 'section':
                return
            old_name = data[1]
        else:
            old_name = section_name

        if old_name == 'DEFAULT':
            return
            
        new_name, ok = QInputDialog.getText(
            self, _('Renomear Seção'), 
            _('Novo nome para a seção:'), 
            text=old_name
        )
        
        if ok and new_name and new_name != old_name:
            if self.config.has_section(new_name):
                QMessageBox.warning(self, _('Aviso'), _('Uma seção com este nome já existe.'))
                return
                
            command = RenameSectionCommand(self, old_name, new_name)
            self.undo_stack.push(command)

    def delete_current_item(self):
        item = self.tree.currentItem()
        if item:
            self.delete_item(item)

    def delete_item(self, item_to_delete=None, section_name=None):
        if section_name:
            target_name = section_name
            is_section = True
        elif item_to_delete:
            data = item_to_delete.data(0, Qt.ItemDataRole.UserRole)
            if not data:
                return
            if data[0] == 'section':
                target_name = data[1]
                is_section = True
            else:
                target_name = data[2] # key name
                section_name = data[1]
                is_section = False
        else:
            return

        if is_section:
            if target_name == 'DEFAULT':
                return
            reply = QMessageBox.question(
                self, 'Confirmar Exclusão',
                f'Tem certeza que deseja excluir a seção "{target_name}" e todas as suas chaves?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                command = DeleteSectionCommand(self, target_name)
                self.undo_stack.push(command)
        else:
            key_name = target_name
            reply = QMessageBox.question(
                self, 'Confirmar Exclusão',
                f'Tem certeza que deseja excluir a chave "{key_name}"?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                command = DeleteKeyCommand(self, section_name, key_name)
                self.undo_stack.push(command)

    def duplicate_item(self, section_name=None):
        if section_name:
            old_name = section_name
            duplicate_type = 'section'
        else:
            item = self.tree.currentItem()
            if not item:
                return None
            data = item.data(0, Qt.ItemDataRole.UserRole)
            if not data:
                return None
            duplicate_type = data[0]
            if duplicate_type == 'section':
                old_name = data[1]
            else:
                target_section_name, key_name = data[1], data[2]

        if duplicate_type == 'section':
            new_name, ok = QInputDialog.getText(self, 'Duplicar Seção', 'Novo nome:', text=f"{old_name}_Copy")
            if ok and new_name:
                if not self.config.has_section(new_name):
                    command = DuplicateSectionCommand(self, old_name, new_name)
                    self.undo_stack.push(command)
                    return new_name
                else:
                    QMessageBox.warning(self, "Aviso", "Esta seção já existe.")
        elif duplicate_type == 'key':
            new_key, ok = QInputDialog.getText(self, 'Duplicar Chave', 'Novo nome:', text=f"{key_name}_Copy")
            if ok and new_key:
                if not self.config.has_option(target_section_name, new_key):
                    command = DuplicateKeyCommand(self, target_section_name, key_name, new_key)
                    self.undo_stack.push(command)
                else:
                    QMessageBox.warning(self, "Aviso", "Esta chave já existe nesta seção.")
        return None

    def on_canvas_duplicate_requested(self, section):
        new_name = self.duplicate_item(section_name=section)
        if new_name:
            # Selecionar o novo item
            self.canvas_widget.select_item_by_section(new_name)
            self.on_canvas_item_selected(new_name)

