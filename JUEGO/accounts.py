from ursina import *
import json
import os
import uuid

class AccountManager:
    def __init__(self):
        self.save_path = 'accounts.json'
        self.accounts = []
        self.load()

    def load(self):
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, 'r', encoding='utf-8') as f:
                    self.accounts = json.load(f)
            except:
                self.accounts = []
        else:
            self.accounts = []
            
        for acc in self.accounts:
            if 'stats' not in acc:
                acc['stats'] = {
                    'total_score': 0,
                    'high_score': 0,
                    'enemies_destroyed': 0,
                    'time_flown': 0
                }

    def save(self):
        try:
            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"[Cuentas] Error al guardar: {e}")

    def create_account(self, name):
        if len(self.accounts) >= 5:
            return False
        acc_id = str(uuid.uuid4())
        self.accounts.append({
            'id': acc_id, 
            'name': name,
            'stats': {
                'total_score': 0,
                'high_score': 0,
                'enemies_destroyed': 0,
                'time_flown': 0
            }
        })
        self.save()
        return True

    def delete_account(self, acc_id):
        self.accounts = [a for a in self.accounts if a['id'] != acc_id]
        self.save()
        
        # Opcional: borrar archivo de logros de esta cuenta
        ach_path = f'achievements_{acc_id}.json'
        if os.path.exists(ach_path):
            try:
                os.remove(ach_path)
            except:
                pass

    def rename_account(self, acc_id, new_name):
        for a in self.accounts:
            if a['id'] == acc_id:
                a['name'] = new_name
                break
        self.save()


class AccountButton(Entity):
    def __init__(self, text, y_pos, on_click, accent='#00EFFF', parent_entity=None):
        super().__init__(parent=parent_entity, z=-1)
        self.border = Entity(
            parent=self, model=Quad(radius=0.015), color=color.hex(accent),
            scale=(0.62, 0.08), position=(0, y_pos), z=0.05
        )
        self.btn = Button(
            parent=self, text=text, scale=(0.60, 0.06), position=(0, y_pos),
            color=color.hex('#071526'), highlight_color=color.hex('#123049'),
            text_color=color.white, on_click=on_click, z=0
        )

class AccountMenu(Entity):
    def __init__(self, on_account_selected, **kwargs):
        super().__init__(parent=camera.ui, z=0, **kwargs)
        self.manager = AccountManager()
        self.on_account_selected = on_account_selected
        
        # Fondo oscuro puro
        self.bg = Entity(parent=self, model='quad', color=color.black, scale=(99, 99), z=5)
        
        # Panel Principal
        self.panel_border = Entity(parent=self, model=Quad(radius=0.025), color=color.hex('#00EFFF'), scale=(0.90, 0.86), z=0.20)
        self.panel = Entity(parent=self, model=Quad(radius=0.025), color=color.hex('#05101E'), scale=(0.88, 0.84), z=0.10)
        
        # Título
        Text(parent=self, text='ASTRA 3D', origin=(0, 0), position=(0, 0.36), scale=0.8, color=color.hex('#6E8798'), z=-0.3)
        Text(parent=self, text='SELECCIÓN DE PILOTO', origin=(0, 0), position=(0, 0.29), scale=2.5, color=color.hex('#BFEFFF'), z=-0.3)
        Entity(parent=self, model='quad', color=color.hex('#00EFFF'), scale=(0.5, 0.003), position=(0, 0.23), z=-0.2)

        # Decoraciones futuristas
        Entity(parent=self, model='circle', color=color.hex('#00EFFF').tint(0.2), scale=(0.015, 0.015), position=(-0.41, 0.40), z=-0.2)
        Entity(parent=self, model='circle', color=color.hex('#00EFFF').tint(0.2), scale=(0.015, 0.015), position=(0.41, 0.40), z=-0.2)
        Entity(parent=self, model='quad', color=color.hex('#00EFFF').tint(0.2), scale=(0.82, 0.002), position=(0, 0.40), z=-0.2)
        
        Entity(parent=self, model='quad', color=color.hex('#00EFFF').tint(0.2), scale=(0.82, 0.002), position=(0, -0.38), z=-0.2)
        Entity(parent=self, model='circle', color=color.hex('#00EFFF').tint(0.2), scale=(0.015, 0.015), position=(-0.41, -0.38), z=-0.2)
        Entity(parent=self, model='circle', color=color.hex('#00EFFF').tint(0.2), scale=(0.015, 0.015), position=(0.41, -0.38), z=-0.2)

        # Consejos aleatorios
        import random
        tips = [
            "CONSEJO: No intentes embestir un asteroide dorado, no son de oro suave.",
            "TRANSMISIÓN: 'Si escuchas pitidos rápidos, no te quedes quieto.'",
            "MANTENIMIENTO: Revisa los propulsores laterales después de cada misión.",
            "CONSEJO: Jugar como invitado significa que nadie recordará tus hazañas.",
            "SISTEMA: Conexión cifrada con ASTRA 3D establecida. Esperando biometría.",
            "RECUERDA: El espacio es inmenso, pero tú eres más rápido.",
        ]
        Text(parent=self, text=random.choice(tips), origin=(0, 0), position=(0, -0.33), scale=0.8, color=color.hex('#4AA3C7'), z=-0.3)

        self.list_container = Entity(parent=self, y=0.15)
        self.buttons = []
        
        self.build_ui()
        
        # Menú de Entrada (Nuevo Piloto / Renombrar)
        self.input_layer = Entity(parent=self, enabled=False, z=-10)
        Entity(parent=self.input_layer, model='quad', color=color.rgba(0,0,0,220), scale=(99, 99), z=5) # Oscurecer fondo
        
        self.input_border = Entity(parent=self.input_layer, model=Quad(radius=0.02), color=color.hex('#4AA3C7'), scale=(0.62, 0.36), z=0.2)
        self.input_panel = Entity(parent=self.input_layer, model=Quad(radius=0.02), color=color.hex('#071526'), scale=(0.60, 0.34), z=0.1)
        
        self.input_title = Text(parent=self.input_layer, text='NUEVO PILOTO', origin=(0, 0), position=(0, 0.10), scale=1.8, color=color.hex('#4AA3C7'), z=-0.3)
        
        self.input_field = InputField(parent=self.input_layer, position=(0, 0.02), scale=(0.5, 0.06), 
                                      limit_content_to='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-', 
                                      character_limit=15, color=color.hex('#030A12'), text_color=color.white, z=-0.3)
        
        self.btn_confirm = Button(parent=self.input_layer, text='ACEPTAR', scale=(0.25, 0.06), position=(-0.14, -0.08), 
                                  color=color.hex('#1A4D2E'), highlight_color=color.hex('#2E8B57'), z=-0.3)
        self.btn_cancel = Button(parent=self.input_layer, text='CANCELAR', scale=(0.25, 0.06), position=(0.14, -0.08), 
                                 color=color.hex('#4D1A1A'), highlight_color=color.hex('#8B2E2E'), on_click=self.close_prompt, z=-0.3)

        # Animación de entrada inicial
        self.panel.scale = (0.80, 0.76)
        self.panel_border.scale = (0.82, 0.78)
        self.panel.animate_scale((0.88, 0.84), duration=0.4, curve=curve.out_back)
        self.panel_border.animate_scale((0.90, 0.86), duration=0.4, curve=curve.out_back)

    def build_ui(self):
        for b in self.buttons:
            destroy(b)
        self.buttons.clear()

        y_pos = 0.02
        
        for acc in self.manager.accounts:
            acc_id = acc['id']
            acc_name = acc['name']
            
            # Fila de cuenta
            bg_row = Entity(parent=self.list_container, model=Quad(radius=0.01), color=color.hex('#0A1A2F'), scale=(0.7, 0.08), position=(0, y_pos), z=0)
            
            t = Text(parent=self.list_container, text=acc_name, position=(-0.32, y_pos + 0.01), scale=1.3, origin=(-0.5, 0), color=color.white, z=-1)
            
            b_play = Button(parent=self.list_container, text='VUELO', scale=(0.12, 0.05), position=(0.0, y_pos),
                            color=color.hex('#00EFFF').tint(-0.6), highlight_color=color.hex('#00EFFF').tint(-0.4),
                            on_click=Func(self.select_account, acc_id, acc_name), z=-1)
            
            b_ren = Button(parent=self.list_container, text='EDITAR', scale=(0.12, 0.05), position=(0.14, y_pos),
                           color=color.hex('#4AA3C7').tint(-0.6), highlight_color=color.hex('#4AA3C7').tint(-0.4),
                           on_click=Func(self.prompt_rename, acc_id, acc_name), z=-1)
                           
            b_del = Button(parent=self.list_container, text='BORRAR', scale=(0.12, 0.05), position=(0.28, y_pos),
                           color=color.red.tint(-0.4), highlight_color=color.red.tint(-0.2),
                           on_click=Func(self.do_delete_and_refresh, acc_id), z=-1)
                           
            self.buttons.extend([bg_row, t, b_play, b_ren, b_del])
            y_pos -= 0.1

        if len(self.manager.accounts) < 5:
            btn_crear = AccountButton('+ CREAR NUEVO PILOTO', y_pos - 0.02, self.prompt_create, accent='#00EFFF', parent_entity=self.list_container)
            self.buttons.append(btn_crear)
            y_pos -= 0.1
            
        y_pos -= 0.04
        
        btn_invitado = AccountButton('JUGAR COMO INVITADO', y_pos, Func(self.select_account, 'guest', 'Invitado'), accent='#6E8798', parent_entity=self.list_container)
        self.buttons.append(btn_invitado)

    def do_delete_and_refresh(self, acc_id):
        self.manager.delete_account(acc_id)
        self.build_ui()

    def close_prompt(self):
        self.input_layer.enabled = False

    def prompt_create(self):
        self.input_layer.enabled = True
        self.input_field.text = ''
        self.input_title.text = 'NUEVO PILOTO'
        self.btn_confirm.on_click = self.do_create
        self.input_field.active = True

    def do_create(self):
        name = self.input_field.text.strip()
        if name:
            self.manager.create_account(name)
        self.close_prompt()
        self.build_ui()

    def prompt_rename(self, acc_id, old_name):
        self.input_layer.enabled = True
        self.input_field.text = old_name
        self.input_title.text = 'RENOMBRAR PILOTO'
        self.btn_confirm.on_click = Func(self.do_rename, acc_id)
        self.input_field.active = True

    def do_rename(self, acc_id):
        name = self.input_field.text.strip()
        if name:
            self.manager.rename_account(acc_id, name)
        self.close_prompt()
        self.build_ui()

    def select_account(self, acc_id, acc_name):
        self.disable()
        if self.on_account_selected:
            self.on_account_selected(acc_id, acc_name)
