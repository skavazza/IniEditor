import os
from PyQt6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsItem, 
    QGraphicsTextItem, QGraphicsPixmapItem, QGraphicsRectItem, QMenu,
    QGraphicsPathItem
)
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QColor, QPixmap, QFont, QPen, QBrush, QPainter, QTransform, QPainterPath
from PyQt6.QtWidgets import QGraphicsColorizeEffect

class VisualMeterItem(QGraphicsRectItem):
    """Base class for Rainmeter visual items, providing background support (SolidColor)."""
    def __init__(self, section_name, x=0, y=0, w=0, h=0):
        super().__init__(0, 0, w, h)
        self.section_name = section_name
        self.setPos(x, y)
        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))

    def itemChange(self, change, value):
        try:
            # Lógica de Snapping (Posição prestes a mudar)
            if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
                try:
                    scene = self.scene()
                    if scene:
                        canvas = getattr(scene, 'canvas', None)
                        if canvas and getattr(canvas, 'snap_to_grid_flag', False):
                            grid = getattr(canvas, 'grid_size', 10)
                            # Snapping relativo ao cenário
                            x = round(value.x() / grid) * grid
                            y = round(value.y() / grid) * grid
                            return QPointF(x, y)
                except: pass
                
            if change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
                if hasattr(self.scene(), 'item_moved'):
                    self.scene().item_moved(self.section_name, value)
            elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
                if value and hasattr(self.scene(), 'item_selected'):
                    self.scene().item_selected(self.section_name)
            return super().itemChange(change, value)
        except RuntimeError:
            # O objeto C++ subjacente foi deletado (ex: durante scene.clear()).
            # Ignorar silenciosamente para evitar crash.
            return value

    def apply_solid_color(self, color_str):
        if not color_str:
            self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            return
        parts = [p.strip() for p in color_str.split(',')]
        if len(parts) >= 3:
            try:
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                a = int(parts[3]) if len(parts) == 4 else 255
                self.setBrush(QBrush(QColor(r, g, b, a)))
            except: pass

    def apply_padding(self, padding_str):
        if not padding_str: return
        parts = [p.strip() for p in padding_str.split(',')]
        if len(parts) == 4:
            try:
                l, t, r, b = [int(p) for p in parts]
                rect = self.rect()
                # Expandir o retângulo do background conforme o padding
                # No Rainmeter, padding adiciona espaço ao redor do conteúdo
                self.setRect(rect.x() - l, rect.y() - t, rect.width() + l + r, rect.height() + t + b)
            except: pass

class VisualStringItem(VisualMeterItem):
    def __init__(self, section_name, text="Texto", x=0, y=0):
        super().__init__(section_name, x, y)
        self.text_item = QGraphicsTextItem(text, self)
        self.text_item.setDefaultTextColor(QColor("white"))
        # Atualizar o tamanho do background rect baseado no texto
        self.setRect(self.text_item.boundingRect())

    def setFont(self, font):
        self.text_item.setFont(font)
        self.setRect(self.text_item.boundingRect())

    def setDefaultTextColor(self, color):
        self.text_item.setDefaultTextColor(color)

    def setPlainText(self, text):
        self.text_item.setPlainText(text)
        self.setRect(self.text_item.boundingRect())

class VisualImageItem(VisualMeterItem):
    def __init__(self, section_name, pixmap_path, x=0, y=0):
        super().__init__(section_name, x, y)
        self.pixmap_item = QGraphicsPixmapItem(self)
        if os.path.exists(pixmap_path):
            self.pixmap_item.setPixmap(QPixmap(pixmap_path))
        else:
            placeholder = QPixmap(50, 50)
            placeholder.fill(QColor(100, 100, 100, 150))
            self.pixmap_item.setPixmap(placeholder)
        self.setRect(self.pixmap_item.boundingRect())

    def setPixmap(self, pixmap):
        self.pixmap_item.setPixmap(pixmap)
        self.setRect(self.pixmap_item.boundingRect())

class VisualBarItem(VisualMeterItem):
    def __init__(self, section_name, x=0, y=0, w=100, h=10):
        super().__init__(section_name, x, y, w, h)
        self.bar_foreground = QGraphicsRectItem(0, 0, w * 0.6, h, self) # 60% default progress
        self.bar_foreground.setBrush(QBrush(QColor(0, 122, 204)))
        self.bar_foreground.setPen(QPen(Qt.PenStyle.NoPen))

    def set_bar_color(self, color_str):
        parts = [p.strip() for p in color_str.split(',')]
        if len(parts) >= 3:
            try:
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                a = int(parts[3]) if len(parts) == 4 else 255
                self.bar_foreground.setBrush(QBrush(QColor(r, g, b, a)))
            except: pass

class VisualShapeItem(VisualMeterItem):
    """Implementa o suporte básico para Meter=Shape."""
    def __init__(self, section_name, x=0, y=0):
        super().__init__(section_name, x, y)
        self.path_item = QGraphicsPathItem(self)
        self.path_item.setPen(QPen(QColor("white"), 1))
        self.path_item.setBrush(QBrush(QColor(255, 255, 255, 150)))

    def apply_shape_string(self, shape_str):
        if not shape_str: return
        
        # Parse básico: "Tipo Coords | Modificadores"
        # Ex: Rectangle 0,0,100,50 | Fill Color 255,0,0 | StrokeWidth 2
        parts = [p.strip() for p in shape_str.split('|')]
        if not parts: return
        
        cmd_part = parts[0]
        cmd_parts = cmd_part.split()
        if not cmd_parts: return
        
        shape_type = cmd_parts[0].lower()
        args = []
        if len(cmd_parts) > 1:
            # Tentar extrair argumentos (ex: 0,0,100,50)
            args_raw = "".join(cmd_parts[1:])
            try:
                args = [float(a.strip()) for a in args_raw.split(',') if a.strip()]
            except: pass

        path = QPainterPath()
        if shape_type == 'rectangle' and len(args) >= 4:
            path.addRect(args[0], args[1], args[2], args[3])
        elif shape_type == 'ellipse' and len(args) >= 4:
            # Rainmeter Ellipse: CenterX, CenterY, RadiusX, RadiusY
            path.addEllipse(QPointF(args[0], args[1]), args[2], args[3])
        elif shape_type == 'line' and len(args) >= 4:
            path.moveTo(args[0], args[1])
            path.lineTo(args[2], args[3])
        
        # Combinar com o caminho existente
        current_path = self.path_item.path()
        current_path.addPath(path)
        self.path_item.setPath(current_path)
        self.setRect(self.path_item.boundingRect())

        # Aplicar modificadores básicos
        fill_color = None
        stroke_color = QColor("white")
        stroke_width = 1

        for mod in parts[1:]:
            low_mod = mod.lower()
            if low_mod.startswith('fill color'):
                fill_color = self._parse_shape_color(mod[10:].strip())
            elif low_mod.startswith('stroke color'):
                stroke_color = self._parse_shape_color(mod[12:].strip())
            elif low_mod.startswith('strokewidth'):
                try: stroke_width = float(low_mod[11:].strip())
                except: pass

        if fill_color:
            self.path_item.setBrush(QBrush(fill_color))
        else:
            self.path_item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            
        pen = QPen(stroke_color, stroke_width)
        if stroke_width == 0:
            pen.setStyle(Qt.PenStyle.NoPen)
        self.path_item.setPen(pen)
        
        self.setRect(self.path_item.boundingRect())

    def _parse_shape_color(self, color_str):
        parts = [p.strip() for p in color_str.split(',')]
        if len(parts) >= 3:
            try:
                r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                a = int(parts[3]) if len(parts) == 4 else 255
                return QColor(r, g, b, a)
            except: pass
        return None

class SkinBoundaryItem(QGraphicsRectItem):
    """Representa visualmente os limites da skin."""
    def __init__(self):
        super().__init__()
        pen = QPen(QColor(0, 122, 204, 200), 2, Qt.PenStyle.DashLine)
        pen.setCosmetic(True) # Espessura constante independente do zoom
        self.setPen(pen)
        self.setZValue(-10) # Fica atrás dos meters
        self.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self.setAcceptHoverEvents(False)
        self.setFlags(QGraphicsItem.GraphicsItemFlag.ItemHasNoContents) # Não bloqueia cliques


class VisualScene(QGraphicsScene):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.canvas = parent

    def item_moved(self, section, pos):
        if self.canvas:
            self.canvas.item_moved(section, pos)

    def item_selected(self, section):
        if self.canvas:
            self.canvas.on_item_selected(section)

class VisualCanvas(QGraphicsView):
    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.scene_obj = VisualScene(self)
        self.setScene(self.scene_obj)
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self._apply_background_color()
        
        # Elementos auxiliares
        self.show_boundary_flag = True
        self.show_grid_flag = False
        self.snap_to_grid_flag = False
        self.grid_size = 10
        self._setup_auxiliary_items()
        
        # Sinais para comunicar mudanças ao Editor principal

        self.item_moved_signal = None 
        self.item_selected_signal = None
        self.add_requested_signal = None # function(x, y, meter_type)
        self.remove_requested_signal = None # function(section)
        self.duplicate_requested_signal = None # function(section)

    def contextMenuEvent(self, event):
        item = self._get_meter_item_at(event.pos())
        menu = QMenu()
        
        if item:
            # Menu para item selecionado
            section = item.section_name
            dup_action = menu.addAction(f"Duplicar '{section}'")
            del_action = menu.addAction(f"Excluir '{section}'")
            menu.addSeparator()
            
            action = menu.exec(event.globalPos())
            if action == dup_action:
                if self.duplicate_requested_signal: self.duplicate_requested_signal(section)
            elif action == del_action:
                if self.remove_requested_signal: self.remove_requested_signal(section)
        else:
            # Menu para área vazia
            add_string = menu.addAction("Adicionar Texto (String)")
            add_image = menu.addAction("Adicionar Imagem (Image)")
            add_bar = menu.addAction("Adicionar Barra (Bar)")
            add_shape = menu.addAction("Adicionar Forma (Shape)")
            
            action = menu.exec(event.globalPos())
            
            # Obter coordenadas no scene
            scene_pos = self.mapToScene(event.pos())
            x, y = int(scene_pos.x()), int(scene_pos.y())
            
            if action == add_string:
                if self.add_requested_signal: self.add_requested_signal(x, y, 'String')
            elif action == add_image:
                if self.add_requested_signal: self.add_requested_signal(x, y, 'Image')
            elif action == add_bar:
                if self.add_requested_signal: self.add_requested_signal(x, y, 'Bar')
            elif action == add_shape:
                if self.add_requested_signal: self.add_requested_signal(x, y, 'Shape')

    def keyPressEvent(self, event):
        # Atalhos do Canvas
        items = self.scene_obj.selectedItems()
        if not items:
            super().keyPressEvent(event)
            return
            
        # Tentar encontrar o meter item (pode ser o item selecionado ou seu pai)
        item = None
        for selected in items:
            curr = selected
            while curr:
                if hasattr(curr, 'section_name'):
                    item = curr
                    break
                curr = curr.parentItem()
            if item: break
            
        if not item:
            super().keyPressEvent(event)
            return
            
        section = item.section_name
        
        if event.key() == Qt.Key.Key_Delete:
            if self.remove_requested_signal: self.remove_requested_signal(section)
        elif event.key() == Qt.Key.Key_D and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            if self.duplicate_requested_signal: self.duplicate_requested_signal(section)
        else:
            super().keyPressEvent(event)

    def _apply_background_color(self):
        if self.dark_mode:
            self.setBackgroundBrush(QBrush(QColor("#1e1e1e")))  # Dark Rainmeter Background
        else:
            self.setBackgroundBrush(QBrush(QColor("#f0f0f0")))  # Light background

    def set_theme(self, dark_mode):
        self.dark_mode = dark_mode
        self._apply_background_color()
        self.update()

    def set_show_boundary(self, show):
        self.show_boundary_flag = show
        self.boundary_item.setVisible(show)
        self.update_boundary()

    def set_show_grid(self, show):
        self.show_grid_flag = show
        self.update()

    def set_snap_to_grid(self, snap):
        self.snap_to_grid_flag = snap

    def set_grid_size(self, size):
        self.grid_size = size
        self.update()

    def drawBackground(self, painter, rect):
        """Desenha a grade se estiver ativada."""
        super().drawBackground(painter, rect)
        if self.show_grid_flag:
            grid_size = self.grid_size
            left = int(rect.left()) - (int(rect.left()) % grid_size)
            top = int(rect.top()) - (int(rect.top()) % grid_size)
            
            # Cores para grade
            if self.dark_mode:
                color_minor = QColor(255, 255, 255, 15)
                color_major = QColor(255, 255, 255, 40)
            else:
                color_minor = QColor(0, 0, 0, 15)
                color_major = QColor(0, 0, 0, 40)
            
            # Desenhar linhas verticais
            x_start = left
            while x_start < rect.right():
                is_major = int(x_start) % (grid_size * 5) == 0
                painter.setPen(QPen(color_major if is_major else color_minor, 1))
                painter.drawLine(int(x_start), int(rect.top()), int(x_start), int(rect.bottom()))
                x_start += grid_size
            
            # Desenhar linhas horizontais
            y_start = top
            while y_start < rect.bottom():
                is_major = int(y_start) % (grid_size * 5) == 0
                painter.setPen(QPen(color_major if is_major else color_minor, 1))
                painter.drawLine(int(rect.left()), int(y_start), int(rect.right()), int(y_start))
                y_start += grid_size

    def update_boundary(self):
        """Atualiza o retângulo que envolve todos os meters."""
        if not self.show_boundary_flag:
            return
            
        # Encontrar a bounding box de todos os items que são meters
        meter_items = [i for i in self.scene_obj.items() if isinstance(i, VisualMeterItem)]
        
        if not meter_items:
            self.boundary_item.setVisible(False)
            return
            
        rect = None
        for item in meter_items:
            if rect is None:
                rect = item.sceneBoundingRect()
            else:
                rect = rect.united(item.sceneBoundingRect())
        
        if rect and not rect.isNull():
            self.boundary_item.setRect(rect)
            self.boundary_item.setVisible(True)
        else:
            self.boundary_item.setVisible(False)



    def _get_meter_item_at(self, pos):
        item = self.itemAt(pos)
        while item:
            if hasattr(item, 'section_name'):
                return item
            item = item.parentItem()
        return None

    def _setup_auxiliary_items(self):
        """Inicializa ou reinicializa itens que não são meters (ex: limites)."""
        self.boundary_item = SkinBoundaryItem()
        self.scene_obj.addItem(self.boundary_item)
        self.boundary_item.setVisible(self.show_boundary_flag)

    def clear_canvas(self):
        self.scene_obj.clear()
        self._setup_auxiliary_items()

    def item_moved(self, section, pos):
        if self.item_moved_signal:
            self.item_moved_signal(section, int(pos.x()), int(pos.y()))
        self.update_boundary()


    def on_item_selected(self, section):
        if self.item_selected_signal:
            self.item_selected_signal(section)

    def select_item_by_section(self, section):
        for item in self.scene_obj.items():
            if hasattr(item, 'section_name') and item.section_name == section:
                item.setSelected(True)
                # Deselecionar outros
                for other in self.scene_obj.items():
                    if other != item:
                        other.setSelected(False)
                break

    def set_item_locked(self, section, is_locked):
        for item in self.scene_obj.items():
            if hasattr(item, 'section_name') and item.section_name == section:
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, not is_locked)
                item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, not is_locked)
                if is_locked:
                    item.setSelected(False)
                break

    def _parse_coord(self, value, prev_item=None, is_y=False):
        """Tenta converter valores de coordenadas do Rainmeter para int.
        Suporta: números simples, sufixos 'r' e 'R' (relativos), expressões matemáticas como (1*260)."""
        if isinstance(value, (int, float)):
            return int(value)
        if not value or not isinstance(value, str):
            return 0
        
        clean = value.strip()
        
        # Verificar sufixos relativos
        is_rel_r = clean.endswith('r')
        is_rel_R = clean.endswith('R')
        
        if is_rel_r or is_rel_R:
            clean = clean[:-1].strip()
            if not clean: # Apenas 'r' ou 'R'
                clean = "0"
        
        # Se ainda contém variáveis não resolvidas (#...#), retornar 0 localmente
        if '#' in clean:
            base_val = 0
        else:
            try:
                base_val = int(float(clean))
            except (ValueError, TypeError):
                # Tentar avaliar expressão matemática segura
                expr = clean.strip('()')
                try:
                    base_val = int(eval(expr, {"__builtins__": {}}, {}))
                except Exception:
                    base_val = 0
                    
        # Aplicar relatividade se necessário e se houver um item anterior
        if (is_rel_r or is_rel_R) and prev_item:
            # Obter bounding rect do item anterior no coordinate system do canvas (cena)
            rect = prev_item.sceneBoundingRect()
            if is_y:
                if is_rel_r:
                    return int(rect.y() + base_val)
                else: # is_rel_R
                    return int(rect.y() + rect.height() + base_val)
            else:
                if is_rel_r:
                    return int(rect.x() + base_val)
                else: # is_rel_R
                    return int(rect.x() + rect.width() + base_val)
                    
        return base_val

    def add_meter(self, section, meter_type, props, prev_item=None):
        x = self._parse_coord(props.get('x', 0), prev_item, False)
        y = self._parse_coord(props.get('y', 0), prev_item, True)
        
        item = None
        m_type = meter_type.lower()
        
        if m_type == 'string':
            text = props.get('text', section)
            item = VisualStringItem(section, text, x, y)
            
            # Aplicar fonte
            font_face = props.get('fontface')
            font_size = props.get('fontsize')
            font_style = props.get('stringstyle', '').lower()
            
            if font_face or font_size or font_style:
                font = QFont(font_face if font_face else "Arial")
                if font_size:
                    try: font.setPointSize(int(font_size))
                    except: pass
                if 'bold' in font_style: font.setBold(True)
                if 'italic' in font_style: font.setItalic(True)
                item.setFont(font)
            
            # Case
            font_case = props.get('stringcase', '').lower()
            if font_case == 'upper':
                item.setPlainText(item.text_item.toPlainText().upper())
            elif font_case == 'lower':
                item.setPlainText(item.text_item.toPlainText().lower())
            elif font_case == 'proper':
                item.setPlainText(item.text_item.toPlainText().title())
            
            # Cor do Texto
            color_str = props.get('fontcolor')
            if color_str:
                parts = [p.strip() for p in color_str.split(',')]
                if len(parts) >= 3:
                    try:
                        r, g, b = int(parts[0]), int(parts[1]), int(parts[2])
                        a = int(parts[3]) if len(parts) == 4 else 255
                        item.setDefaultTextColor(QColor(r, g, b, a))
                    except: pass
            
            # Aplicar Rotação (Angle - Rainmeter usa radianos, mas PyQt usa graus)
            angle = props.get('angle')
            if angle:
                try:
                    # Converter radianos para graus se for o caso, ou assumir graus se o usuário preferir
                    # Rainmeter oficial é radianos. 1 rad = 57.2958 graus.
                    item.setRotation(float(angle) * 57.2958)
                except: pass

        elif m_type == 'image':
            # Combinar imagepath + imagename para obter o caminho completo
            img_name = props.get('imagename', '')
            img_path_prefix = props.get('imagepath', '')
            if img_path_prefix and img_name and not os.path.isabs(img_name):
                # imagepath é uma pasta; juntar com imagename
                img_full = os.path.join(img_path_prefix.rstrip('/\\'), img_name)
            elif img_name:
                img_full = img_name
            else:
                img_full = ''
            item = VisualImageItem(section, img_full, x, y)
            w_str = props.get('w')
            h_str = props.get('h')
            if w_str or h_str:
                try:
                    w = self._parse_coord(w_str) if w_str else 0
                    h = self._parse_coord(h_str) if h_str else 0
                    pix = item.pixmap_item.pixmap()
                    if not pix.isNull() and w > 0 and h > 0:
                        item.setPixmap(pix.scaled(w, h, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.SmoothTransformation))
                    elif w > 0 and h > 0:
                        # Ajustar o placeholder para o tamanho esperado
                        placeholder = QPixmap(w, h)
                        placeholder.fill(QColor(100, 100, 100, 150))
                        item.setPixmap(placeholder)
                except (ValueError, TypeError): pass
            
            # Aplicar ImageTint
            tint_color = props.get('imagetint')
            if tint_color:
                parts = [p.strip() for p in tint_color.split(',')]
                if len(parts) >= 3:
                    try:
                        effect = QGraphicsColorizeEffect()
                        effect.setColor(QColor(int(parts[0]), int(parts[1]), int(parts[2])))
                        item.setGraphicsEffect(effect)
                    except: pass

        elif m_type == 'bar':
            w = int(props.get('w', 100))
            h = int(props.get('h', 10))
            item = VisualBarItem(section, x, y, w, h)
            
            # Cor da Barra (Foreground)
            bar_color = props.get('barcolor')
            if bar_color:
                item.set_bar_color(bar_color)
            
            # Orientação da Barra
            orientation = props.get('barorientation', '').lower()
            if orientation == 'vertical':
                # Simular orientação vertical no canvas (trocar W por H simplificadamente)
                item.setRect(0, 0, h, w)
                item.bar_foreground.setRect(0, h * 0.4, h, h * 0.6) # Preenchimento de baixo para cima

        elif m_type == 'shape':
            item = VisualShapeItem(section, x, y)
            # Shapes podem vir como Shape, Shape2, Shape3... 
            # Processar em ordem correta (Shape, Shape2, Shape3...)
            keys = sorted([k for k in props.keys() if k.startswith('shape')], 
                         key=lambda x: int(x[5:]) if x[5:].isdigit() else 0)
            
            for k in keys:
                item.apply_shape_string(props[k])

        if item:
            # Aplicar SolidColor (Background) para qualquer meter
            item.apply_solid_color(props.get('solidcolor'))
            # Aplicar Padding
            item.apply_padding(props.get('padding'))
            
            self.scene_obj.addItem(item)
            self.update_boundary()
            return item

        return None

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def zoom_in(self):
        factor = 1.25
        self.scale(factor, factor)

    def zoom_out(self):
        factor = 1 / 1.25
        self.scale(factor, factor)

    def fit_to_view(self):
        """Ajusta o zoom e a posição para mostrar todos os elementos da cena."""
        items = self.scene_obj.items()
        if not items:
            return
            
        rect = self.scene_obj.itemsBoundingRect()
        if rect.width() > 0 and rect.height() > 0:
            # Adicionar uma margem pequena (10%)
            margin = max(rect.width(), rect.height()) * 0.1
            rect.adjust(-margin, -margin, margin, margin)
            self.fitInView(rect, Qt.AspectRatioMode.KeepAspectRatio)
