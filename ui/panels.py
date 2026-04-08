from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, 
    QFormLayout, QLineEdit, QComboBox, QFontComboBox, QHBoxLayout, QPushButton, QColorDialog
)
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtCore import Qt, QSize
from utils import resource_path

class LayerItemWidget(QWidget):
    visibility_toggled = None # function(section, is_visible)
    lock_toggled = None       # function(section, is_locked)
    
    def __init__(self, section_name, is_visible=True, is_locked=False, parent=None):
        super().__init__(parent)
        self.section_name = section_name
        self.is_visible = is_visible
        self.is_locked = is_locked
        self.dark_mode = True # Default
        self.init_ui()
        
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Visibilidade (Olho)
        self.vis_btn = QPushButton()
        self.vis_btn.setFixedSize(24, 24)
        self.vis_btn.setIconSize(QSize(16, 16))
        self.vis_btn.setFlat(True)
        self.vis_btn.clicked.connect(self._toggle_vis)
        layout.addWidget(self.vis_btn)
        
        # Bloqueio (Cadeado)
        self.lock_btn = QPushButton()
        self.lock_btn.setFixedSize(24, 24)
        self.lock_btn.setIconSize(QSize(16, 16))
        self.lock_btn.setFlat(True)
        self.lock_btn.clicked.connect(self._toggle_lock)
        layout.addWidget(self.lock_btn)
        
        # Nome da Camada
        self.label = QLabel(self.section_name)
        layout.addWidget(self.label, stretch=1)
        
        self.update_icons()

    def set_theme(self, dark_mode):
        self.dark_mode = dark_mode
        self.update_icons()
        
    def update_icons(self):
        theme_prefix = "dark" if self.dark_mode else "light"
        vis_icon = resource_path(f"assets/{theme_prefix}_show.png") if self.is_visible else resource_path(f"assets/{theme_prefix}_hidden.png")
        lock_icon = resource_path(f"assets/{theme_prefix}_lock.png") if self.is_locked else resource_path(f"assets/{theme_prefix}_unlock.png")
        
        self.vis_btn.setIcon(QIcon(vis_icon))
        self.lock_btn.setIcon(QIcon(lock_icon))
        
    def _toggle_vis(self):
        self.is_visible = not self.is_visible
        self.update_icons()
        if self.visibility_toggled:
            self.visibility_toggled(self.section_name, self.is_visible)
            
    def _toggle_lock(self):
        self.is_locked = not self.is_locked
        self.update_icons()
        if self.lock_toggled:
            self.lock_toggled(self.section_name, self.is_locked)

class LayerPanel(QWidget):
    selection_changed = None # Callback function(section_name)
    visibility_changed = None # Callback function(section_name, is_visible)
    lock_changed = None       # Callback function(section_name, is_locked)
    order_changed = None      # Callback function(new_order_list)
    add_requested = None      # Callback function()
    remove_requested = None   # Callback function(section_name)
    rename_requested = None   # Callback function(section_name)
    duplicate_requested = None # Callback function(section_name)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<b>Camadas (Meters)</b>"))
        
        self.list = QListWidget()
        self.list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.list.model().rowsMoved.connect(self._on_rows_moved)
        self.list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list)
        
        # Botões Adicionar/Remover
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("+ Layer")
        self.add_btn.clicked.connect(lambda: self.add_requested() if self.add_requested else None)
        self.remove_btn = QPushButton("- Layer")
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.remove_btn)
        layout.addLayout(btn_layout)
        
        self.setMinimumWidth(150)
        self.list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.list.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, pos):
        item = self.list.itemAt(pos)
        if not item:
            return
            
        section = item.data(Qt.ItemDataRole.UserRole)
        from PyQt6.QtWidgets import QMenu
        from i18n import _
        
        menu = QMenu()
        rename_action = menu.addAction(_('Renomear'))
        dup_action = menu.addAction(_('Duplicar'))
        del_action = menu.addAction(_('Excluir'))
        
        action = menu.exec(self.list.mapToGlobal(pos))
        if action == rename_action:
            if self.rename_requested: self.rename_requested(section)
        elif action == dup_action:
            if self.duplicate_requested: self.duplicate_requested(section)
        elif action == del_action:
            if self.remove_requested: self.remove_requested(section)

    def set_theme(self, dark_mode):
        self.dark_mode = dark_mode
        if dark_mode:
            self.setStyleSheet("background-color: #252526; border-right: 1px solid #3e3e3e;")
        else:
            self.setStyleSheet("background-color: #f0f0f0; border-right: 1px solid #cccccc;")
            
        # Atualizar ícones dos widgets na lista
        for i in range(self.list.count()):
            item = self.list.item(i)
            widget = self.list.itemWidget(item)
            if isinstance(widget, LayerItemWidget):
                widget.set_theme(dark_mode)

    def set_meters(self, meters_data):
        # meters_data pode ser uma lista de dicts: [{'section': 'Meter1', 'visible': True, 'locked': False}, ...]
        self.list.clear()
        for item_data in meters_data:
            if isinstance(item_data, str):
                # Fallback se apenas strings forem passadas
                section = item_data
                vis = True
                loc = False
            else:
                section = item_data.get('section', '')
                vis = item_data.get('visible', True)
                loc = item_data.get('locked', False)
                
            item = QListWidgetItem(self.list)
            # Associar nome da seção ao item para facilitar buscas e drops
            item.setData(Qt.ItemDataRole.UserRole, section)
            
            widget = LayerItemWidget(section, vis, loc)
            # Aplicamos o tema ao criar
            if hasattr(self, 'dark_mode'):
                widget.set_theme(self.dark_mode)
                
            widget.visibility_toggled = self._on_vis_toggled
            widget.lock_toggled = self._on_lock_toggled
            
            # Necessário para o QListWidgetItem ter o tamanho correto do widget
            item.setSizeHint(widget.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, widget)

    def select_meter(self, section_name):
        for i in range(self.list.count()):
            item = self.list.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == section_name:
                self.list.setCurrentItem(item)
                break

    def _on_selection_changed(self):
        item = self.list.currentItem()
        if item and self.selection_changed:
            self.selection_changed(item.data(Qt.ItemDataRole.UserRole))

    def _on_vis_toggled(self, section, is_visible):
        if self.visibility_changed:
            self.visibility_changed(section, is_visible)
            
    def _on_lock_toggled(self, section, is_locked):
        if self.lock_changed:
            self.lock_changed(section, is_locked)
            
    def _on_rows_moved(self, parent, start, end, destination, row):
        # Recuperar a nova ordem das seções após o drop
        if self.order_changed:
            new_order = []
            for i in range(self.list.count()):
                item = self.list.item(i)
                new_order.append(item.data(Qt.ItemDataRole.UserRole))
            self.order_changed(new_order)
            
    def _on_remove_clicked(self):
        item = self.list.currentItem()
        if item and self.remove_requested:
            self.remove_requested(item.data(Qt.ItemDataRole.UserRole))

class PropertyPanel(QWidget):
    property_changed = None # Callback function(section, key, value)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_section = None
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)
        
        self.label = QLabel("<b>Propriedades</b>")
        self.layout.addWidget(self.label)
        
        self.form_container = QWidget()
        self.form_layout = QFormLayout(self.form_container)
        self.layout.addWidget(self.form_container)
        
        self.layout.addStretch()
        self.setMinimumWidth(200)

    def set_theme(self, dark_mode):
        if dark_mode:
            self.setStyleSheet("background-color: #252526; border-left: 1px solid #3e3e3e;")
        else:
            self.setStyleSheet("background-color: #f0f0f0; border-left: 1px solid #cccccc;")

    def set_properties(self, section, props):
        self.current_section = section
        # Limpar formulário atual
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        self.label.setText(f"<b>Propriedades: {section}</b>")
        
        # Propriedades de Transformação (Comuns)
        self._add_property("X", props.get('x', '0'))
        self._add_property("Y", props.get('y', '0'))
        self._add_property("W", props.get('w', ''))
        self._add_property("H", props.get('h', ''))
        self._add_color_property("SolidColor", props.get('solidcolor', ''))
        self._add_color_property("SolidColor2", props.get('solidcolor2', ''))
        self._add_combo_property("AntiAlias", props.get('antialias', '1'), ['1', '0'])
        self._add_property("Padding", props.get('padding', ''))
        self._add_combo_property("DynamicVariables", props.get('dynamicvariables', '0'), ['0', '1'])
        
        # Propriedades específicas por Meter
        meter_type = props.get('meter', '').lower()
        if meter_type == 'string':
            self._add_property("Text", props.get('text', ''))
            self._add_property("FontSize", props.get('fontsize', ''))
            self._add_font_property("FontFace", props.get('fontface', ''))
            self._add_color_property("FontColor", props.get('fontcolor', ''))
            self._add_property("Angle", props.get('angle', '0'))
            self._add_combo_property("StringAlign", props.get('stringalign', 'Left'), ['Left', 'Right', 'Center', 'Justified'])
            self._add_combo_property("StringCase", props.get('stringcase', 'None'), ['None', 'Upper', 'Lower', 'Proper'])
            self._add_combo_property("StringStyle", props.get('stringstyle', 'Normal'), ['Normal', 'Bold', 'Italic', 'BoldItalic'])
            self._add_combo_property("StringEffect", props.get('stringeffect', 'None'), ['None', 'Shadow', 'Border'])
        elif meter_type == 'image':
            self._add_property("ImageName", props.get('imagename', ''))
            self._add_property("ImagePath", props.get('imagepath', ''))
            self._add_color_property("ImageTint", props.get('imagetint', ''))
            self._add_combo_property("PreserveAspectRatio", props.get('preserveaspectratio', '0'), ['0', '1', '2'])
        elif meter_type == 'bar':
            self._add_color_property("BarColor", props.get('barcolor', ''))
            self._add_combo_property("BarOrientation", props.get('barorientation', 'Horizontal'), ['Horizontal', 'Vertical'])
        elif meter_type == 'shape':
            self._add_property("Shape", props.get('shape', ''))
            self._add_property("Shape2", props.get('shape2', ''))
            self._add_property("Shape3", props.get('shape3', ''))
            self._add_combo_property("AntiAlias", props.get('antialias', '1'), ['1', '0'])

    def _add_property(self, key, value):
        edit = QLineEdit(str(value))
        edit.editingFinished.connect(lambda k=key, e=edit: self._on_property_changed(k, e.text()))
        self.form_layout.addRow(key + ":", edit)

    def _add_color_property(self, key, value):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        edit = QLineEdit(str(value))
        edit.editingFinished.connect(lambda k=key, e=edit: self._on_property_changed(k, e.text()))
        layout.addWidget(edit)
        
        picker_btn = QPushButton()
        picker_btn.setFixedWidth(25)
        picker_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Estilizar o botão com a cor atual
        self._update_color_button_style(picker_btn, value)
        
        picker_btn.clicked.connect(lambda: self._open_color_picker(key, edit, picker_btn))
        layout.addWidget(picker_btn)
        
        self.form_layout.addRow(key + ":", container)

    def _update_color_button_style(self, button, color_str):
        if not color_str:
            color_str = "255,255,255"
        
        parts = [p.strip() for p in str(color_str).split(',')]
        bg_color = "white"
        if 3 <= len(parts) <= 4:
            try:
                r, g, b = parts[0], parts[1], parts[2]
                bg_color = f"rgb({r},{g},{b})"
            except: pass
            
        button.setStyleSheet(f"background-color: {bg_color}; border: 1px solid #888; border-radius: 3px;")

    def _open_color_picker(self, key, edit, button):
        initial_color = QColor(255, 255, 255)
        current_text = edit.text()
        if current_text:
            parts = [p.strip() for p in current_text.split(',')]
            if 3 <= len(parts) <= 4:
                try:
                    r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                    a = int(parts[3]) if len(parts) == 4 else 255
                    initial_color = QColor(r, g, b, a)
                except ValueError: pass

        color = QColorDialog.getColor(initial_color, self, "Selecionar Cor", QColorDialog.ColorDialogOption.ShowAlphaChannel)
        
        if color.isValid():
            r, g, b, a = color.red(), color.green(), color.blue(), color.alpha()
            color_str = f"{r},{g},{b}" if a == 255 else f"{r},{g},{b},{a}"
            edit.setText(color_str)
            self._update_color_button_style(button, color_str)
            self._on_property_changed(key, color_str)

    def _add_font_property(self, key, value):
        combo = QFontComboBox()
        combo.setFontFilters(QFontComboBox.FontFilter.ScalableFonts)
        if value:
            combo.setCurrentText(value)
        combo.currentFontChanged.connect(lambda f, k=key: self._on_property_changed(k, f.family()))
        self.form_layout.addRow(key + ":", combo)

    def _add_combo_property(self, key, value, options):
        combo = QComboBox()
        combo.addItems(options)
        
        # Tentar selecionar o valor atual (case-insensitive)
        index = -1
        for i in range(combo.count()):
            if combo.itemText(i).lower() == str(value).lower():
                index = i
                break
        
        if index != -1:
            combo.setCurrentIndex(index)
        else:
            combo.setCurrentText(str(value))
            
        combo.currentTextChanged.connect(lambda t, k=key: self._on_property_changed(k, t))
        self.form_layout.addRow(key + ":", combo)

    def _on_property_changed(self, key, value):
        if self.property_changed and self.current_section:
            self.property_changed(self.current_section, key, value)
