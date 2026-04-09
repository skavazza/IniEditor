# Rainmeter Skin Editor - Roadmap

## ✅ Concluído (v1.0 - Editor de Código Aprimorado)
- [x] **Seletor de Cores (Color Picker):** O Rainmeter usa formatos como `255,255,255,255`. Implementado seletor visual que insere o código RGB/RGBA automaticamente.
- [x] **Realce de Sintaxe (Syntax Highlighting):** Colorir de forma diferente o que é `[Seção]`, `Chave` e `#Variáveis#`.
- [x] **Auto-Completar:** Sugerir comandos comuns como `Meter=String`, `Measure=CPU` ou `FontColor=` conforme o usuário digita.
- [x] **Botão "Refresh Skin":** Adicionado botão para enviar o comando `!Refresh` ao Rainmeter imediatamente após salvar.
- [x] **Variáveis Globais:** Aba dedicada para editar automaticamente o arquivo `Variables.inc` localizado na pasta `@Resources`.
- [x] **Modo Escuro (Dark Mode):** Interface escura e moderna inspirada no VS Code para combinar com as skins `illustro`.
- [x] **Barra de Pesquisa:** Localizar rapidamente configurações em arquivos `.ini` complexos.
- [x] **Backup Automático:** Criação de arquivo `.bak` em cada salvamento para evitar perda de dados.
- [x] **Alternar Tema:** Adicionada a opção de trocar entre Modo Escuro e Modo Claro no menu "Exibir".
- [x] **Modularização:** O código foi organizado em módulos.
- [x] **Visualizador de Log:** Nova aba dedicada para ver o `Rainmeter.log` em tempo real.
- [x] **Gerador de Bangs:** Ferramenta visual para construir comandos complexos como `!SetOption` ou `!SetVariable` sem precisar decorar a sintaxe.
- [x] **Gerenciador de Ativos:** Galeria visual para navegar e inserir imagens da pasta `@Resources` diretamente no código.
- [x] **Snippets (Modelos):** Biblioteca de blocos de código prontos (Meters, Measures e Templates) para inserção rápida.

---

## 🚀 Fase Atual (v2.0 - Editor Visual Drag-and-Drop)

Estamos transformando o editor de código em um **Editor Visual (WYSIWYG)** completo, conforme especificado no `PROMPT_PYTHON_CODER.md`.

### 1. Interface Principal
- [x] **Canvas Visual:** Área de trabalho para renderizar os elementos visualmente.
- [x] **Painel de Camadas (Layers):** Lista de elementos na tela com suporte a seleção.
- [x] **Painel de Propriedades:** Aba lateral à direita que exibe informações do item selecionado.
- [x] **Barra de Ferramentas (Toolbar):** Botões rápidos para adicionar Texto, Imagem, Barra, Rotator, etc.

### 2. Funcionalidades de Design Visual
- [x] **Adicionar Itens:** Criação de elementos básicos diretamente no Canvas.
- [x] **Seleção Visual:** Clicar nos itens renderizados no Canvas para selecioná-los.
- [x] **Movimentação e Redimensionamento:** Arrasto e redimensionamento interativo dos itens no Canvas.
- [x] **Gestão de Camadas Avançada:** Reordenação via drag-and-drop, visibilidade (ícone de olho), trancar/destrancar e botões para adicionar/remover.
- [x] **Desfazer/Refazer (Undo/Redo):** Sistema global para reverter alterações (Ctrl+Z / Ctrl+Y) no posicionamento e propriedades.
- [x] **Atalhos de Teclado:** Duplicar (Ctrl+D), Excluir (Delete).

### 3. Edição Dinâmica de Propriedades
- [x] **Edição em Tempo Real:** Alterar campos no Painel de Propriedades reflete instantaneamente no Canvas.
- [x] **Propriedades Específicas por Tipo:** Campos dinâmicos dependendo se o item é Text, Image, Bar, Shape, etc.
- [x] **Gerenciador de Fontes:** Detector de fontes do sistema com dropdown list e preview visual. (Agora integrado na aba de Fontes)

### 4. Integração e Exportação
- [x] **Motor de Exportação:** Converter a representação visual (Canvas + Propriedades) em um arquivo `.ini` estruturado nativo do Rainmeter.
- [x] **Exportador RMSKIN:** Empacotamento profissional da skin (INI + Imagens + Fontes) pronta para distribuição/instalação no Rainmeter.
- [x] **Salvar/Carregar Projeto:** Estado do editor salvo em JSON para não perder o layout e poder continuar a edição posteriormente.
- [x] **Preferências de Usuário:** Auto-save configurável e troca de idioma (i18n).
- [x] **Gerenciador de Ativos:** Busca e visualização de imagens/fontes na pasta `@Resources`.

---

## 🚀 Fase 3 (v3.0 - Ferramentas de Design Avançadas)

### 1. Elementos e Ferramentas Dinâmicas
- [ ] **Elemento Rotator:** Suporte visual para meters do tipo Rotator com controle de centro e ângulo.
- [ ] **Unidades Percentuais:** Suporte para posições e tamanhos relativos (ex: `X=50%`).
- [ ] **Controles de Zoom:** Lupa para zoom in/out e botão "Ajustar à Tela" no Canvas.

### 2. Precisão e Alinhamento
- [ ] **Grid e Snap-to-Grid:** Grade visual com encaixe automático dos elementos.
- [ ] **Ferramentas de Alinhamento:** Botões para alinhar múltiplos itens (Esquerda, Centro, Topo, Distribuir).
- [ ] **Indicadores de Dimensão:** Exibir coordenadas (X, Y) e tamanho (W, H) flutuantes durante o arraste.

### 3. Usabilidade e Polimento
- [ ] **Multi-seleção:** Selecionar e mover múltiplos elementos de uma vez (Ctrl+Click / Rubberband).
- [ ] **Barra de Status:** Informações contextuais e coordenadas do mouse no rodapé.
- [ ] **Janela de Ajuda/Sobre:** Guia de atalhos e documentação integrada.