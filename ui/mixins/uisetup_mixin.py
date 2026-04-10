from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QTreeWidget, QSplitter, 
    QTabWidget, QLineEdit, QLabel, QComboBox, QPushButton, QMenu, QMessageBox
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QAction, QActionGroup, QKeySequence

from ui import (
    RainmeterEdit, IniHighlighter, BangGeneratorDialog, 
    AssetManager, SnippetManager, RmskinExportDialog, FontManager, 
    VisualCanvas, LayerPanel, PropertyPanel, HelpDialog, PreferencesDialog
)
from ui.delegates import KeyValueDelegate
from core.constants import SUPPORTED_ENCODINGS
from i18n import _, T

class UISetupMixin:
    """Mixin para gerenciar a inicialização da interface e temas do IniEditor."""

    def init_ui(self):
        self.setWindowTitle('Editor de Arquivos .ini - Rainmeter Skins')
        self.setGeometry(100, 100, 800, 600)

        self._init_menubar()
        
        # Janela central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.main_layout = QVBoxLayout(central_widget)
        
        self._init_tabs()
        self._init_footer()
        
        self.statusBar().showMessage(_("Rainmeter IDE Iniciado"))

    def _init_menubar(self):
        menubar = self.menuBar()
        
        # Arquivo
        file_menu = menubar.addMenu(_('Arquivo'))

        new_action = QAction(_('Novo'), self)
        new_action.setShortcut('Ctrl+N')
        new_action.triggered.connect(self.new_skin)
        file_menu.addAction(new_action)
        
        self.add_skin_action = QAction(_('Adicionar Skin ao Projeto'), self)
        self.add_skin_action.triggered.connect(self.add_skin_to_project_action)
        self.add_skin_action.setEnabled(False)
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

        close_action = QAction(_('Fechar'), self)
        close_action.setShortcut('Ctrl+W')
        close_action.triggered.connect(self.close_file)
        file_menu.addAction(close_action)
        
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

        file_menu.addSeparator()

        exit_action = QAction(_('Sair'), self)
        exit_action.setShortcut('Alt+F4')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Formatação
        format_menu = menubar.addMenu(_('Formatação'))
        encoding_menu = format_menu.addMenu(_('Codificação'))
        self.encoding_action_group = QActionGroup(self)
        self.encoding_action_group.setExclusive(True)
        self.encoding_actions = {}
        for encoding, label in SUPPORTED_ENCODINGS:
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

        # Atalhos de grupos
        group_action = QAction(_("Agrupar selecionados"), self)
        group_action.setShortcut("Ctrl+G")
        group_action.triggered.connect(self._group_from_shortcut)
        edit_menu.addAction(group_action)

        ungroup_action = QAction(_("Desagrupar"), self)
        ungroup_action.setShortcut("Ctrl+Shift+G")
        ungroup_action.triggered.connect(self._ungroup_from_shortcut)
        edit_menu.addAction(ungroup_action)

        # Exibir
        view_menu = menubar.addMenu(_('Exibir'))
        
        self.dark_mode_action = QAction(_('Modo Escuro'), self, checkable=True)
        self.dark_mode_action.setChecked(self.dark_mode)
        self.dark_mode_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(self.dark_mode_action)
        
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

    def _init_tabs(self):
        self.tabs = QTabWidget()
        
        # Aba 1: Editor
        editor_tab = QWidget()
        editor_layout = QHBoxLayout(editor_tab)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        
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

        self.value_editor = RainmeterEdit()
        self.value_editor.setPlaceholderText(_('Selecione uma chave para editar seu valor'))
        self.value_editor.textChanged.connect(self.on_value_changed)
        self.value_editor.focused.connect(lambda: self._set_last_active(self.value_editor))
        self.highlighter = IniHighlighter(self.value_editor.document(), dark_mode=self.dark_mode)
        self.splitter.addWidget(self.value_editor)
        editor_layout.addWidget(self.splitter)

        # Aba 2: Canvas Visual
        self._init_canvas_tab()

        # Aba 3: Variáveis Globais
        self._init_variable_tab()

        # Aba 4: Gerenciador de Ativos
        self.asset_tab = AssetManager(dark_mode=self.dark_mode)

        # Aba 5: Snippets
        self.snippet_tab = SnippetManager(dark_mode=self.dark_mode)

        self.tabs.addTab(editor_tab, _('Editor de Skin'))
        self.tabs.addTab(self.canvas_panel, _('Canvas Visual'))
        self.tabs.addTab(self.var_widget, _('Variáveis Globais (@Resources)'))
        self.tabs.addTab(self.asset_tab, _('Ativos (@Resources)'))
        self.tabs.addTab(self.snippet_tab, _('Snippets (Modelos)'))

        self.main_layout.addWidget(self.tabs)

    def _init_canvas_tab(self):
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
        self.canvas_widget.item_dragging_signal = self.on_canvas_item_dragging
        self.canvas_widget.mouse_move_signal = self.on_canvas_mouse_move
        self.canvas_widget.group_requested_signal = self.on_canvas_group_requested
        self.canvas_widget.ungroup_requested_signal = self.on_canvas_ungroup_requested
        
        self.prop_panel = PropertyPanel()
        self.prop_panel.property_changed = self.on_property_edited
        self.prop_panel.set_theme(self.dark_mode)
        
        self.canvas_container = QWidget()
        canvas_cont_layout = QVBoxLayout(self.canvas_container)
        canvas_cont_layout.setContentsMargins(0, 0, 0, 0)
        canvas_cont_layout.setSpacing(0)
        
        canvas_toolbar = QHBoxLayout()
        canvas_toolbar.setContentsMargins(5, 5, 5, 5)
        
        self.btn_fit = QPushButton(_("Ajustar"))
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
        
        # Alinhamentos
        self.btn_align_left = QPushButton(_("Alinhar Esq."))
        self.btn_align_left.clicked.connect(lambda: self.align_selected_meters("left"))
        self.btn_align_center = QPushButton(_("Centro H."))
        self.btn_align_center.clicked.connect(lambda: self.align_selected_meters("center_h"))
        self.btn_align_right = QPushButton(_("Alinhar Dir."))
        self.btn_align_right.clicked.connect(lambda: self.align_selected_meters("right"))
        self.btn_align_top = QPushButton(_("Alinhar Topo"))
        self.btn_align_top.clicked.connect(lambda: self.align_selected_meters("top"))
        self.btn_align_middle = QPushButton(_("Meio V."))
        self.btn_align_middle.clicked.connect(lambda: self.align_selected_meters("middle_v"))
        self.btn_align_bottom = QPushButton(_("Alinhar Baixo"))
        self.btn_align_bottom.clicked.connect(lambda: self.align_selected_meters("bottom"))

        canvas_toolbar.addWidget(self.btn_fit)
        canvas_toolbar.addWidget(self.chk_snap)
        canvas_toolbar.addSpacing(10)
        canvas_toolbar.addWidget(self.btn_zoom_in)
        canvas_toolbar.addWidget(self.btn_zoom_out)
        canvas_toolbar.addSpacing(10)
        canvas_toolbar.addWidget(QLabel("|  " + _("Alinhamento") + ":"))
        canvas_toolbar.addWidget(self.btn_align_left)
        canvas_toolbar.addWidget(self.btn_align_center)
        canvas_toolbar.addWidget(self.btn_align_right)
        canvas_toolbar.addWidget(self.btn_align_top)
        canvas_toolbar.addWidget(self.btn_align_middle)
        canvas_toolbar.addWidget(self.btn_align_bottom)
        canvas_toolbar.addStretch()
        
        canvas_cont_layout.addLayout(canvas_toolbar)
        canvas_cont_layout.addWidget(self.canvas_widget)
        
        self.canvas_panel.addWidget(self.layer_panel)
        self.canvas_panel.addWidget(self.canvas_container)
        self.canvas_panel.addWidget(self.prop_panel)
        self.canvas_panel.setSizes([200, 600, 250])

    def _init_variable_tab(self):
        self.var_widget = QWidget()
        var_layout = QVBoxLayout(self.var_widget)
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

    def _init_footer(self):
        button_layout = QHBoxLayout()
        save_button = QPushButton(_('Salvar'))
        save_button.clicked.connect(self.save_file)
        button_layout.addWidget(save_button)
        add_section_button = QPushButton(_('Adicionar Seção'))
        add_section_button.clicked.connect(self.add_section)
        button_layout.addWidget(add_section_button)
        add_key_button = QPushButton(_('Adicionar Chave'))
        add_key_button.clicked.connect(self.add_key)
        button_layout.addWidget(add_key_button)
        refresh_button = QPushButton(_('Atualizar Skin'))
        refresh_button.clicked.connect(self.refresh_skin)
        button_layout.addWidget(refresh_button)
        bang_btn = QPushButton(_('Gerador de Bangs'))
        bang_btn.clicked.connect(self.open_bang_generator)
        button_layout.addWidget(bang_btn)
        self.main_layout.addLayout(button_layout)

    def toggle_theme(self):
        self.dark_mode = self.dark_mode_action.isChecked()
        self.apply_theme()
        if self.ini_file:
            self.update_tree()
        if self.log_window:
            self.log_window.setStyleSheet(self.styleSheet())

    def toggle_boundary(self):
        show = self.show_boundary_action.isChecked()
        self.canvas_widget.set_show_boundary(show)

    def toggle_grid(self):
        show = self.show_grid_action.isChecked()
        self.canvas_widget.set_show_grid(show)

    def toggle_snap(self):
        sender = self.sender()
        is_checked = sender.isChecked()
        self.snap_to_grid_action.setChecked(is_checked)
        self.chk_snap.setChecked(is_checked)
        self.canvas_widget.set_snap_to_grid(is_checked)

    def open_preferences(self):
        dialog = PreferencesDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        if dialog.exec():
            self.configure_auto_save()
            QMessageBox.information(self, _("Preferências salvas"), _("Suas preferências foram salvas."))

    def show_help_dialog(self):
        dialog = HelpDialog(self)
        dialog.setStyleSheet(self.styleSheet())
        dialog.exec()

    def configure_auto_save(self):
        from PyQt6.QtCore import QSettings
        settings = QSettings('RainmeterEditor', 'RainmeterEditorAppSettings')
        is_enabled = settings.value("auto_save_enabled", False, type=bool)
        interval = settings.value("auto_save_interval", 300000, type=int)
        if is_enabled:
            self.auto_save_timer.start(interval)
        else:
            self.auto_save_timer.stop()

    def apply_theme(self):
        if self.dark_mode:
            qss = """
                QMainWindow, QWidget { background-color: #1e1e1e; color: #e0e0e0; }
                QTreeWidget, QTextEdit { background-color: #252526; border: 1px solid #3e3e3e; font-family: 'Consolas'; font-size: 10pt; }
                QPushButton { background-color: #333333; color: #ffffff; border: 1px solid #555555; padding: 6px 12px; border-radius: 4px; }
                QPushButton:hover { background-color: #007acc; border: 1px solid #0098ff; }
                QMenuBar { background-color: #2d2d2d; color: #ffffff; }
                QMenuBar::item:selected { background-color: #3e3e3e; }
                QMenu { background-color: #2d2d2d; color: #ffffff; border: 1px solid #454545; }
            """
        else:
            qss = """
                QMainWindow, QWidget { background-color: #ffffff; color: #000000; }
                QTreeWidget, QTextEdit { background-color: #ffffff; border: 1px solid #cccccc; font-family: 'Consolas'; font-size: 10pt; }
                QPushButton { background-color: #e1e1e1; color: #000000; border: 1px solid #adadad; padding: 6px 12px; border-radius: 4px; }
                QPushButton:hover { background-color: #cfe5ff; border: 1px solid #007acc; }
                QMenuBar { background-color: #f0f0f0; color: #000000; }
                QMenu { background-color: #ffffff; color: #000000; border: 1px solid #cccccc; }
                QTabWidget::pane { border: 1px solid #cccccc; }
                QTabBar::tab { background: #e1e1e1; color: #000000; padding: 8px; }
                QTabBar::tab:selected { background: #ffffff; }
            """
        self.setStyleSheet(qss)
        self.layer_panel.set_theme(self.dark_mode)
        self.prop_panel.set_theme(self.dark_mode)
        self.asset_tab.set_theme(self.dark_mode)
        self.canvas_widget.set_theme(self.dark_mode)
        self.snippet_tab.set_theme(self.dark_mode)
        if hasattr(self, 'highlighter'):
            self.highlighter.set_theme(self.dark_mode)
