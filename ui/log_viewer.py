import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QCheckBox, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer

class LogViewer(QWidget):
    def __init__(self, parent=None, dark_mode=True):
        super().__init__(parent)
        self.dark_mode = dark_mode
        if parent is None:
            self.setWindowFlags(Qt.WindowType.Window)
        self.log_file = os.path.join(os.getenv('APPDATA'), 'Rainmeter', 'Rainmeter.log')
        self.last_pos = 0
        self.init_ui()
        
        # Timer para monitorar o arquivo
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_log)
        self.timer.start(1000) # Checar a cada 1 segundo

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.clear_btn = QPushButton("Limpar console")
        self.clear_btn.clicked.connect(self.clear_log)
        toolbar.addWidget(self.clear_btn)
        
        self.autoscroll_cb = QCheckBox("Auto-scroll")
        self.autoscroll_cb.setChecked(True)
        toolbar.addWidget(self.autoscroll_cb)
        
        self.choose_btn = QPushButton("Escolher arquivo de Log...")
        self.choose_btn.clicked.connect(self.choose_file)
        toolbar.addWidget(self.choose_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Console
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setPlaceholderText("Aguardando atividade do log...")
        layout.addWidget(self.console)
        
        # Se o arquivo não existir inicialmente, avisar
        if not os.path.exists(self.log_file):
            self.console.append(f"<b>Aviso:</b> Arquivo de log não encontrado em: {self.log_file}")
            self.console.append("Por favor, certifique-se que o log está ativado no Rainmeter ou escolha o arquivo manualmente.")

    def clear_log(self):
        self.console.clear()

    def choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, 'Selecionar Rainmeter.log', '', 'Log Files (*.log);;All Files (*)'
        )
        if file_path:
            self.log_file = file_path
            self.last_pos = 0
            self.console.append(f"\n--- Monitorando: {file_path} ---\n")

    def check_log(self):
        if not os.path.exists(self.log_file):
            return
            
        try:
            current_size = os.path.getsize(self.log_file)
            
            # Se o arquivo diminuiu (foi limpo ou rotacionado), resetar posição
            if current_size < self.last_pos:
                self.last_pos = 0
                
            if current_size > self.last_pos:
                with open(self.log_file, 'r', encoding='utf-8-sig', errors='ignore') as f:
                    f.seek(self.last_pos)
                    new_data = f.read()
                    self.last_pos = f.tell()
                    
                    if new_data:
                        self.console.append(new_data.strip())
                        
                        if self.autoscroll_cb.isChecked():
                            self.console.verticalScrollBar().setValue(
                                self.console.verticalScrollBar().maximum()
                            )
        except Exception:
            # Silenciosamente ignorar erros de leitura temporários (arquivo travado, etc)
            pass
