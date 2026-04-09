# Prompt para IA Coder - Rainmeter Editor em Python

## 🎯 Objetivo Principal

Criar uma aplicação desktop **Rainmeter Editor em Python** - um editor visual GUI para criar skins Rainmeter sem necessidade de editar arquivos INI manualmente. A aplicação deve ser multiplataforma (Windows, macOS, Linux) com interface intuitiva drag-and-drop.

---

## 📋 Descrição da Aplicação

### Visão Geral
Uma ferramenta desktop que permite aos usuários criar visualmente skins para Rainmeter através de:
- Editor visual com canvas interativo
- Painel de camadas com drag-and-drop
- Painel de propriedades dinâmico
- Exportação para arquivo INI compatível com Rainmeter
- Gerenciamento de fontes e imagens locais

### Público-alvo
- Designers sem conhecimento técnico de INI
- Usuários Rainmeter iniciantes
- Profissionais que querem prototipagem rápida

---

## ✨ Funcionalidades Obrigatórias

### 1. Interface Principal com 3 Painéis

#### Painel Superior (Toolbar)
```
[File] [Edit] [View] [Help]
[🔘 Text] [🖼️ Image] [📊 Bar] [🔄 Rotator] [⚙️ Settings] [📤 Export]
[🔍 Zoom Controls] [↔️ Align] [🎨 Theme Toggle]
```

**Funcionalidades:**
- Botões para criar novos elementos (Text, Image, Bar, Rotator)
- Controles de zoom (aumentar, diminuir, ajustar à tela)
- Botão de export
- Toggle de tema claro/escuro

#### Painel Esquerdo (Layers Sidebar)
- Lista de camadas criadas
- Reordenação via drag-and-drop
- Checkbox para visibilidade (eye icon)
- Lock/unlock de camadas
- Botões de adicionar/remover camadas
- Seleção de camada ao clicar

#### Painel Central Editor de Skin(Canvas)
- Área de trabalho visual com fundo branco
- Renderização de todos os elementos
- Suporte a seleção de objetos ao clicar
- Manipulação interativa (move, resize, rotate)
- Grid/snap-to-grid opcional
- Indicators de posição e dimensões

#### Painel Direito (Properties Sidebar)
- Propriedades dinâmicas baseadas no tipo de elemento selecionado
- Grupos de propriedades organizadas em abas/grupos

**Para Elemento TEXT:**
- Conteúdo do texto
- Fonte (dropdown com fonte instaladas no sistema)
- Tamanho da fonte
- Cor (color picker)
- Alinhamento (left, center, right)
- Posição XY
- Rotação

**Para Elemento IMAGE:**
- Seleção de arquivo (file picker)
- Preview mini
- Tamanho (width, height)
- Proporções (lock aspect ratio)
- Posição XY
- Opacidade/Alpha
- Rotação

**Para Elemento BAR:**
- Comprimento (width)
- Altura (height)
- Cor (color picker)
- Valor mínimo/máximo
- Valor atual
- Orientação (horizontal/vertical)
- Estilo (sólido, gradient, padrão)
- Posição XY

**Para Elemento ROTATOR:**
- Tamanho (width, height)
- Ângulo inicial
- Velocidade de rotação
- Cor de fundo
- Cor da linha
- Posição XY
- Tipo (circle, square, custom)

**Para Configuração SKIN (global):**
- Nome da skin
- Autor
- Descrição
- Versão
- Dimensões padrão (width, height)
- Cor de fundo
- Transparência

---

### 2. Funcionalidades de Edição

#### Adição de Elementos
- Ao clicar em botão, elemento é criado no centro do canvas
- Elemento é automaticamente selecionado
- Nome automático é gerado (Text1, Image1, etc.)
- Elemento aparece na lista de camadas

#### Seleção e Manipulação
- Click no canvas seleciona elemento
- Drag para mover elemento
- Corners para resize (mantendo proporção se locked)
- Rotação via alça circular
- Propriedades são atualizadas em tempo real

#### Reordenação de Camadas
- Drag dentro da lista de camadas
- Suport para drag up/down
- Z-index automático atualizado
- Pode reordenar pelo botão "Bring to Front" / "Send to Back"

#### Operações Comuns
- Duplicar camada (Ctrl+D)
- Deletar camada (Delete key)
- Selecionar tudo (Ctrl+A)
- Deselecionar (Escape)
- Multi-seleção (Ctrl+Click)
- Alinhar elementos (left, center, right, top, middle, bottom)
- Distribuir espaçamento

---

### 3. Gerenciamento de Fontes

#### Detecção de Fontes do Sistema
- Scan automático na inicialização
- Lista de fontes instaladas no sistema
- Dropdown com preview visual
- Busca/filtro de fontes

#### Fontes Customizadas
- Importar arquivo .ttf ou .otf
- Armazenar localmente na pasta do projeto
- Validar validade da fonte
- Ao exportar, incluir fonte na skin

---

### 4. Gerenciamento de Imagens

#### Importação
- File picker para selecionar imagem
- Validar formato (PNG, JPG, BMP)
- Copiar para pasta local do projeto
- Gerar thumbnail para preview

#### Gerenciamento
- Listar imagens usadas
- View dos arquivos armazenados
- Ao exportar, incluir na skin

---

### 5. Exportação para INI

#### Geração de Arquivo INI
Exportar para formato Rainmeter INI com:
```ini
[Rainmeter]
Update=1000

[MeterMyText]
Meter=String
Text=Hello World
FontFace=Arial
FontSize=12
FontColor=FFFFFF
X=10px
Y=10px

[MeterMyImage]
Meter=Image
ImageName=images\background.png
X=0
Y=0
W=800
H=600

[MeterMyBar]
Meter=Bar
BarImage=...
X=100
Y=100
W=200
H=20
...
```

#### Estrutura de Pastas
```
SkinName/
├── Skin/
│   └── Skin.ini
├── fonts/
│   └── (fontes customizadas)
└── images/
    └── (imagens usadas)
```

#### Arquivo .rmskin
- Compactar pasta exportada em arquivo .rmskin
- Adicionar metadados em JSON
- Pronto para instalar com Rainmeter

---

### 6. Funcionalidades Adicionais

#### Projeto/Salvamento
- Salvar projeto (JSON com estado completo)
- Abrir projeto (load de arquivo JSON)
- Novo projeto (limpar canvas)
- Recent projects

#### Desfazer/Refazer
- Stack de ações
- Ctrl+Z e Ctrl+Y
- Limite de 50 ações

#### Preferências
- Tema claro/escuro
- Unidades (pixels, percentual)
- Grid snap
- Auto-save
- Idioma

#### Preview em Tempo Real
- Mostrar como ficaria em Rainmeter
- Toggle entre editor e preview

---

## 🏗️ Arquitetura Técnica Recomendada

### Tecnologia Principal
- **Python 3.10+**
- **PyQt6 ou PySimpleGUI** - Framework GUI (PyQt6 recomendado para mais controle)
- **Pillow (PIL)** - Processamento de imagens
- **fontTools** - Gerenciamento de fontes
- **json** - Persistência de projetos

### Alternativas Modernas
- **PySide6** (Qt para Python, mais leve que PyQt6)
- **Tkinter** (built-in, limitado para este caso)
- **PySimpleGUI** (mais rápido para prototipagem)
- **Kivy** (multi-plataforma)

### Estrutura de Pastas Recomendada
```
rainmeter_editor_python/
├── main.py                      # Ponto de entrada
├── requirements.txt             # Dependências
├── app/
│   ├── __init__.py
│   ├── ui/
│   │   ├── main_window.py      # Janela principal
│   │   ├── canvas.py           # Renderização do canvas
│   │   ├── toolbar.py          # Barra de ferramentas
│   │   ├── layers_panel.py     # Painel de camadas
│   │   └── properties_panel.py # Painel de propriedades
│   ├── models/
│   │   ├── element.py          # Classe base de elementos
│   │   ├── text_element.py     # Elemento de texto
│   │   ├── image_element.py    # Elemento de imagem
│   │   ├── bar_element.py      # Elemento de barra
│   │   ├── rotator_element.py  # Elemento rotador
│   │   └── skin.py             # Configuração da skin
│   ├── services/
│   │   ├── canvas_manager.py   # Gerenciador do canvas
│   │   ├── layer_manager.py    # Gerenciador de camadas
│   │   ├── font_manager.py     # Gerenciador de fontes
│   │   ├── export_manager.py   # Exportação INI
│   │   └── project_manager.py  # Salvamento/Carregamento
│   ├── utils/
│   │   ├── constants.py        # Constantes
│   │   ├── validators.py       # Validações
│   │   └── helpers.py          # Funções auxiliares
│   └── config.py               # Configurações da app
├── resources/
│   ├── icons/
│   ├── themes/
│   └── fonts/
└── tests/
    └── test_*.py
```

### Dependências Principais (PyQt6)
```txt
PyQt6==6.6.0
PyQt6-sip==13.5.0
Pillow==10.0.0
fontTools==4.40.0
jsonschema==4.19.0
```

---

## 🔄 Fluxo de Implementação

### Fase 1: Setup Base
1. Criar estrutura do projeto
2. Setup PyQt6 com janela principal
3. Dividir em 3 painéis (toolbar, canvas, sidebars)
4. Criar menu básico (File, Edit, Help)

### Fase 2: Canvas e Renderização
1. Implementar custom QGraphicsView/QGraphicsScene
2. Criar classe base Element com properties
3. Implementar elementos específicos (Text, Image, Bar, Rotator)
4. Render visual no canvas com transformações

### Fase 3: Interação
1. Eventos de mouse (click, drag, resize)
2. Manipulação visual de objetos
3. Sistema de seleção
4. Cursor feedback (move, resize, rotate)

### Fase 4: UI Dinâmica
1. Layers panel com drag-and-drop
2. Properties panel dinâmico (muda conforme seleção)
3. Update em tempo real das propriedades
4. Validação de inputs

### Fase 5: Gerenciamento
1. Font manager com detecção de sistema
2. Image manager com file picker
3. Color picker integrado
4. Undo/Redo system

### Fase 6: Exportação
1. Gerador de INI
2. Estrutura de pastas
3. Compactação .rmskin
4. Validação do export

### Fase 7: Persistência
1. Salvar projeto (JSON)
2. Carregar projeto
3. Recent files
4. Auto-save

### Fase 8: Polish
1. Tema claro/escuro
2. Preferências de usuário
3. Hotkeys
4. Sobre e Help
5. Testes

---

## 🎨 Design da Interface

### Paleta de Cores Sugerida
- **Light theme:**
  - Background: #FFFFFF
  - Panel: #F5F5F5
  - Text: #333333
  - Accent: #0078D4

- **Dark theme:**
  - Background: #1E1E1E
  - Panel: #2D2D30
  - Text: #CCCCCC
  - Accent: #0078D4

### Ícones
- Use bibliotecas como `font-awesome` ou `PySimpleSVG`
- Ícones para: Text, Image, Bar, Rotator, Save, Export, etc.

### Responsividade
- Janela mínima: 1000x700
- Janelas maximizáveis
- Painéis redimensionáveis
- Salvamento de layout preferido

---

## 📊 Requisitos Não-Funcionais

### Performance
- Renderização suave com mínimo 60 FPS
- Suporte para até 100 elementos sem lag
- Load de projeto em <2 segundos
- Export em <5 segundos

### Estabilidade
- Tratamento completo de erros
- Logging de actions
- Recovery de crashes
- Validação de dados

### Usabilidade
- Hotkeys padrão (Ctrl+S, Ctrl+Z, etc.)
- Tooltips informativos
- Status bar com info contextual
- Mensagens de erro claras

### Compatibilidade
- Python 3.10+
- Windows, macOS, Linux
- Rainmeter 4.x+

---

## 🧪 Testes Recomendados

```python
# Testes de unidade
- test_element_creation()
- test_layer_reordering()
- test_property_validation()
- test_export_ini_generation()
- test_font_loading()
- test_project_save_load()

# Testes de integração
- test_full_workflow()
- test_canvas_rendering()
- test_drag_and_drop()

# Testes de interface
- test_ui_responsiveness()
- test_shortcuts()
```

---

## 📦 Arquivo de Configuração (config.py)

```python
# Constantes da aplicação
APP_NAME = "Rainmeter Editor"
APP_VERSION = "0.2.6"
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MAX_UNDO_STEPS = 50
SUPPORTED_IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".bmp"]
SUPPORTED_FONT_FORMATS = [".ttf", ".otf"]
```

---

## 🎯 Objetivos de Sucesso

- [ ] Interface funcional com 3 painéis principais
- [ ] Adição e manipulação de elementos
- [ ] Reordenação de camadas com drag-and-drop
- [ ] Propriedades dinâmicas por tipo de elemento
- [ ] Exportação para arquivo INI válido
- [ ] Gerenciamento de fontes
- [ ] Salvamento/carregamento de projetos
- [ ] Undo/Redo funcionando
- [ ] Tema claro/escuro
- [ ] Geração de .rmskin
- [ ] Sem crashes ou erros não tratados

---

## 📝 Considerações Especiais

### Rainmeter Compatibility
- Garantir que INI gerado seja 100% compatível
- Seguir convenções de nomeação de Rainmeter
- Validar sintaxe INI antes de export
- Testar exports em Rainmeter real

### Python-Specific
- Usar type hints (PEP 484)
- Seguir PEP 8 para estilo de código
- Documentar com docstrings
- Criar arquivo de requisitos.txt

### Distribuição
- Empacotar com PyInstaller para .exe (Windows)
- DMG para macOS
- AppImage ou snap para Linux
- Incluir instalador com uninstaller

---

## 🚀 como Começar

1. Criar repositório Git
2. Setup ambiente Python virtual
3. Instalar dependências (pip install -r requirements.txt)
4. Implementar em fases conforme prioridade
5. Testes contínuos
6. Documentação conforme progresso
7. Build releases quando pronto

---

**Prompt criado em:** Março 2026
**Para:** IA Coder (GitHub Copilot, Claude, etc.)
**Linguagem:** Python 3.10+
**Complexidade:** Média-Alta (200-400 horas de desenvolvimento estimado)
