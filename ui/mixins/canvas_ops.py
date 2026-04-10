import os
import re
import configparser
from PyQt6.QtWidgets import QMessageBox, QFileDialog, QInputDialog
from commands import (
    ChangeValueCommand, MoveItemCommand, DeleteSectionCommand, 
    AddSectionCommand, AddKeyCommand
)
from utils import (
    resolve_rainmeter_variables, 
    parse_variables_from_config, 
    resolve_variable_references
)
from i18n import _

class CanvasIntegrationMixin:
    """Mixin para sincronização entre os dados (INI) e a visualização gráfica (Canvas e Painel de Camadas)."""
    
    # Grupos de sections: { group_id: [section, section, ...] }
    # Inicializado em __init__ do IniEditor via init_groups()
    def init_groups(self):
        """Inicializa o estado de grupos (chamar no __init__ do editor)."""
        if not hasattr(self, '_section_groups'):
            self._section_groups = {}   # group_id  -> [section, ...]
            self._section_to_group = {} # section   -> group_id
            self._next_group_id = 1
    
    def _get_group_members(self, section):
        """Retorna todos os membros do grupo ao qual a seção pertence, ou [section]."""
        self.init_groups()
        gid = self._section_to_group.get(section)
        if gid:
            return list(self._section_groups.get(gid, [section]))
        return [section]

    def synchronize_canvas(self):
        self.canvas_widget.clear_canvas()
        if not self.ini_file: return

        if self.config.has_section('Rainmeter'):
            raw_bg = self.config.get('Rainmeter', 'Background', fallback='')
            bg_mode = int(self.config.get('Rainmeter', 'BackgroundMode', fallback='2'))
            solid_color = self.config.get('Rainmeter', 'SolidColor', fallback=None)
            res = self._resolve_props({'bg': raw_bg})
            bg_path = res['bg']
            if bg_path and not os.path.isabs(bg_path):
                bg_path = os.path.join(os.path.dirname(self.ini_file), bg_path)
            self.canvas_widget.set_skin_background(bg_path, bg_mode, solid_color)

        meters_data = []
        prev_item = None
        for section in self.config.sections():
            if self.config.has_option(section, 'Meter'):
                is_visible = self.config.get(section, 'Hidden', fallback='0') != '1'
                meters_data.append({'section': section, 'visible': is_visible, 'locked': False})
                if not is_visible: continue
                
                meter_type = self.config.get(section, 'Meter')
                raw_props = {k.lower(): v for k, v in self.config.items(section)}
                props = self._resolve_props(raw_props)
                item = self.canvas_widget.add_meter(section, meter_type, props, prev_item=prev_item)
                if item: prev_item = item
        
        self.layer_panel.set_meters(meters_data)

    def on_layer_selected(self, section):
        self.canvas_widget.select_item_by_section(section)
        self.update_prop_panel(section)

    def on_layer_visibility_changed(self, section, is_visible):
        val = '0' if is_visible else '1'
        old = self.config.get(section, 'Hidden', fallback='0')
        if old != val:
            self.undo_stack.push(ChangeValueCommand(self, section, 'Hidden', old, val))
            
    def on_layer_lock_changed(self, section, is_locked):
        self.canvas_widget.set_item_locked(section, is_locked)
        
    def on_layer_order_changed(self, new_order):
        from collections import OrderedDict
        new_sections = OrderedDict()
        for sec in self.config.sections():
            if not self.config.has_option(sec, 'Meter'):
                new_sections[sec] = self.config._sections[sec]
        for sec in new_order:
            if sec in self.config._sections:
                new_sections[sec] = self.config._sections[sec]
        for sec in self.config.sections():
            if sec not in new_sections:
                new_sections[sec] = self.config._sections[sec]
        self.config._sections = new_sections
        self.update_tree()
        self.synchronize_canvas()

    def on_layer_add_requested(self):
        self.on_canvas_add_requested(0, 0, 'String')
        
    def on_layer_remove_requested(self, section):
        self.on_canvas_remove_requested(section)

    def on_layer_rename_requested(self, section):
        self.rename_section(section_name=section)
        
    def on_layer_duplicate_requested(self, section):
        self.duplicate_item(section_name=section)

    def on_canvas_item_selected(self, section):
        # Expandir para o grupo se existir
        members = self._get_group_members(section)
        if len(members) > 1:
            self.canvas_widget.select_sections(members)
            self.statusBar().showMessage(f"Grupo selecionado: {', '.join(members)}")
        else:
            self.layer_panel.select_meter(section)
        self.update_prop_panel(section)

    def on_canvas_group_requested(self, sections):
        """Agrupa as sections dadas sob um novo grupo."""
        self.init_groups()
        # Remover de grupos antigos primeiro
        for s in sections:
            old_gid = self._section_to_group.pop(s, None)
            if old_gid and old_gid in self._section_groups:
                self._section_groups[old_gid] = [
                    m for m in self._section_groups[old_gid] if m != s
                ]
                if not self._section_groups[old_gid]:
                    del self._section_groups[old_gid]
        # Criar novo grupo
        gid = f"group_{self._next_group_id}"
        self._next_group_id += 1
        self._section_groups[gid] = list(sections)
        for s in sections:
            self._section_to_group[s] = gid
        
        # Destacar visualmente o grupo no canvas
        self.canvas_widget.select_sections(sections)
        group_label = ', '.join(sections[:3]) + (f' +{len(sections)-3}' if len(sections) > 3 else '')
        self.statusBar().showMessage(f"Grupo criado: [{group_label}]")

    def on_canvas_ungroup_requested(self, section):
        """Remove a section (e seu grupo inteiro) de qualquer agrupamento."""
        self.init_groups()
        gid = self._section_to_group.get(section)
        if not gid:
            self.statusBar().showMessage(f"'{section}' não pertence a nenhum grupo.")
            return
        members = self._section_groups.pop(gid, [])
        for m in members:
            self._section_to_group.pop(m, None)
        self.statusBar().showMessage(f"Grupo desfeito: [{', '.join(members)}]")

    def _group_from_shortcut(self):
        """Handler do atalho Ctrl+G: agrupa os itens selecionados no canvas."""
        selected = self.canvas_widget._selected_meter_items()
        if len(selected) < 2:
            self.statusBar().showMessage(_("Selecione pelo menos 2 itens no Canvas para agrupar (Ctrl+Click)."))
            return
        self.on_canvas_group_requested([i.section_name for i in selected])

    def _ungroup_from_shortcut(self):
        """Handler do atalho Ctrl+Shift+G: desfaz grupo do primeiro item selecionado."""
        selected = self.canvas_widget._selected_meter_items()
        if not selected:
            self.statusBar().showMessage(_("Nenhum item selecionado para desagrupar."))
            return
        self.on_canvas_ungroup_requested(selected[0].section_name)

    def update_prop_panel(self, section):
        if self.config.has_section(section):
            props = {k.lower(): v for k, v in self.config.items(section)}
            styles = [s for s in self.config.sections() if s != section and not self.config.has_option(s, 'Meter')]
            self.prop_panel.set_available_styles(styles)
            self.prop_panel.set_properties(section, props)

    def on_property_edited(self, section, key, value):
        old = self.config.get(section, key, fallback='')
        if old != value:
            self.undo_stack.push(ChangeValueCommand(self, section, key, old, value))

    def canvas_item_moved(self, section, x, y):
        if self.is_updating_from_canvas: return
        if self.config.has_section(section):
            old_x = self.config.get(section, 'X', fallback='0')
            old_y = self.config.get(section, 'Y', fallback='0')
            if str(x) != old_x or str(y) != old_y:
                self.undo_stack.push(MoveItemCommand(self, section, old_x, old_y, str(x), str(y)))

    def on_canvas_multi_moved(self, moves):
        if self.is_updating_from_canvas: return
        self.undo_stack.beginMacro("Multi-move")
        for s, x, y in moves:
            if self.config.has_section(s):
                ox, oy = self.config.get(s, 'X', fallback='0'), self.config.get(s, 'Y', fallback='0')
                if str(x) != ox or str(y) != oy:
                    self.undo_stack.push(MoveItemCommand(self, s, ox, oy, str(x), str(y)))
        self.undo_stack.endMacro()

    def on_canvas_remove_multiple(self, sections):
        if not sections: return
        self.undo_stack.beginMacro(f"Excluir {len(sections)} itens")
        for s in sections:
            if self.config.has_section(s):
                self.undo_stack.push(DeleteSectionCommand(self, s))
        self.undo_stack.endMacro()

    def on_canvas_add_requested(self, x, y, meter_type):
        name, ok = QInputDialog.getText(self, 'Novo Meter', f'Nome para {meter_type}:')
        if ok and name:
            if self.config.has_section(name):
                QMessageBox.warning(self, "Erro", "Seção já existe.")
                return
            self.undo_stack.beginMacro(f"Adicionar {meter_type} pelo Canvas")
            self.undo_stack.push(AddSectionCommand(self, name))
            self.undo_stack.push(AddKeyCommand(self, name, 'Meter', meter_type))
            self.undo_stack.push(AddKeyCommand(self, name, 'X', str(x)))
            self.undo_stack.push(AddKeyCommand(self, name, 'Y', str(y)))
            if meter_type == 'String':
                self.undo_stack.push(AddKeyCommand(self, name, 'Text', 'Texto'))
                self.undo_stack.push(AddKeyCommand(self, name, 'FontSize', '12'))
                self.undo_stack.push(AddKeyCommand(self, name, 'FontColor', '255,255,255,255'))
            elif meter_type == 'Image':
                path, _filter = QFileDialog.getOpenFileName(self, _('Selecionar Imagem'))
                if path: self.undo_stack.push(AddKeyCommand(self, name, 'ImageName', path))
            elif meter_type == 'Rotator':
                path, _filter = QFileDialog.getOpenFileName(
                    self, _('Selecionar Imagem do Ponteiro'),
                    filter="Imagens (*.png *.jpg *.bmp *.gif)"
                )
                if path:
                    self.undo_stack.push(AddKeyCommand(self, name, 'ImageName', path))
                self.undo_stack.push(AddKeyCommand(self, name, 'W', '100'))
                self.undo_stack.push(AddKeyCommand(self, name, 'H', '100'))
                self.undo_stack.push(AddKeyCommand(self, name, 'OffsetX', '50'))
                self.undo_stack.push(AddKeyCommand(self, name, 'OffsetY', '50'))
                self.undo_stack.push(AddKeyCommand(self, name, 'StartAngle', '4.71239'))
                self.undo_stack.push(AddKeyCommand(self, name, 'RotationAngle', '6.28318'))
            self.undo_stack.endMacro()

    def on_canvas_remove_requested(self, section):
        self.delete_item(section_name=section)

    def on_canvas_duplicate_requested(self, section):
        new = self.duplicate_item(section_name=section)
        if new:
            self.canvas_widget.select_item_by_section(new)
            self.on_canvas_item_selected(new)

    def on_canvas_item_dragging(self, section, x, y, w, h):
        self.statusBar().showMessage(f"🖱 {section}  |  X: {x}  Y: {y}  |  W: {w}  H: {h}")

    def on_canvas_mouse_move(self, scene_x, scene_y):
        # Só atualiza com coordenadas simples se não estiver arrastando
        if not getattr(self.canvas_widget, '_drag_active', False):
            self.statusBar().showMessage(f"X: {scene_x},  Y: {scene_y}")

    def align_selected_meters(self, alignment_mode):
        items = self.canvas_widget._selected_meter_items()
        if len(items) < 2:
            QMessageBox.information(self, _("Alinhamento"), _("Selecione pelo menos 2 itens no Canvas para alinhar (Segure Ctrl)."))
            return
            
        bounds = [i.sceneBoundingRect() for i in items]
        if not bounds: return
        
        min_x = min([b.x() for b in bounds])
        max_x = max([b.x() + b.width() for b in bounds])
        min_y = min([b.y() for b in bounds])
        max_y = max([b.y() + b.height() for b in bounds])
        
        self.undo_stack.beginMacro(f"Alinhar ({alignment_mode})")
        for item in items:
            section = item.section_name
            if not self.config.has_section(section): continue
            
            old_x = self.config.get(section, 'X', fallback='0')
            old_y = self.config.get(section, 'Y', fallback='0')
            
            rect = item.sceneBoundingRect()
            new_x = int(rect.x())
            new_y = int(rect.y())
            
            if alignment_mode == "left":
                new_x = int(min_x)
            elif alignment_mode == "right":
                new_x = int(max_x - rect.width())
            elif alignment_mode == "center_h":
                new_x = int((min_x + max_x) / 2 - rect.width() / 2)
            elif alignment_mode == "top":
                new_y = int(min_y)
            elif alignment_mode == "bottom":
                new_y = int(max_y - rect.height())
            elif alignment_mode == "middle_v":
                new_y = int((min_y + max_y) / 2 - rect.height() / 2)
                
            if str(new_x) != old_x or str(new_y) != old_y:
                self.undo_stack.push(MoveItemCommand(self, section, old_x, old_y, str(new_x), str(new_y)))
                
        self.undo_stack.endMacro()

    def _build_resolved_vars(self):
        # Extrair variáveis básicas e de arquivos incluídos
        self.resolved_vars = parse_variables_from_config(self.config)
        
        def _read_inc(content):
            t = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                t.read_string(content)
                self.resolved_vars.update(parse_variables_from_config(t))
            except Exception as e:
                import utils
                utils.logger.warning(f"Erro ao ler include string no configparser: {e}")

        if self.ini_file:
            ini_dir = os.path.dirname(self.ini_file)
            for section in self.config.sections():
                for kc in ['@include', '@include2', '@include3']:
                    raw_inc = self.config.get(section, kc, fallback=None)
                    if raw_inc:
                        # Resolver #@# para o path do include
                        res_dir = os.path.dirname(self.var_file) if self.var_file else os.path.join(ini_dir, '@Resources')
                        raw_inc = raw_inc.replace('#@#', res_dir + os.sep)
                        if os.path.exists(raw_inc):
                            try:
                                with open(raw_inc, 'r', encoding='utf-8-sig') as f: 
                                    _read_inc(f.read())
                            except Exception as e:
                                import utils
                                utils.logger.warning(f"Erro ao carregar e ler arquivo de include '{raw_inc}': {e}")
        
        if self.var_file and os.path.exists(self.var_file):
            try:
                with open(self.var_file, 'r', encoding='utf-8-sig') as f: 
                    _read_inc(f.read())
            except Exception as e:
                import utils
                utils.logger.warning(f"Erro ao carregar e ler arquivo de variável global '{self.var_file}': {e}")

        # Resolver referências cruzadas (#A# = #B#)
        self.resolved_vars = resolve_variable_references(self.resolved_vars)

    def _resolve_props(self, props):
        ini_dir = os.path.dirname(self.ini_file) if self.ini_file else ''
        res_dir = os.path.dirname(self.var_file) if self.var_file else (os.path.join(ini_dir, '@Resources') if ini_dir else '')
        
        return resolve_rainmeter_variables(props, self.resolved_vars, resources_dir=res_dir)
