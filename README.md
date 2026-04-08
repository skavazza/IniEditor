# Rainmeter Editor em Python

Um editor visual interativo com interface drag-and-drop para criar skins do Rainmeter, eliminando a necessidade de editar arquivos INI manualmente.

## 🌟 Visão Geral

Esta aplicação desktop permite a designers e entusiastas do Rainmeter criar e editar skins de forma 100% visual. O editor oferece uma área de trabalho interativa (canvas), gerenciamento avançado de camadas e edição dinâmica de propriedades, exportando o resultado final diretamente para um arquivo INI compatível.

## ✨ Principais Funcionalidades

- **Editor Visual (Canvas):** Área interativa para adicionar, mover, redimensionar e selecionar elementos diretamente na tela.
- **Painel de Camadas (Layers):** Lista de camadas organizada com suporte a reordenação via drag-and-drop, alternância de visibilidade e bloqueio de itens.
- **Painel de Propriedades:** Edição dinâmica de atributos (texto, cores, posicionamento, fontes) de acordo com o medidor (Meter) selecionado.
- **Elementos Suportados:** Botões de criação rápida para os principais *Meters* do Rainmeter (Texto, Imagem, Barra, etc.).
- **Gerenciamento de Projetos:** Salve e carregue o estado completo do seu trabalho em arquivos `.rmproject` (JSON), incluindo posições de janelas e configurações de canvas.
- **Projetos Recentes:** Acesso rápido aos últimos projetos trabalhados através do menu "Projetos Recentes".
- **Preferências Customizáveis:**
    - **Auto-Save:** Nunca perca seu progresso com o salvamento automático configurável (1, 5 ou 10 minutos).
    - **Internacionalização (i18n):** Suporte nativo a múltiplos idiomas (atualmente Português-BR e Inglês-US).
- **Múltiplas Skins por Projeto:** Estrutura organizada que permite adicionar várias skins (`.ini`) dentro de um único nome de projeto, compartilhando a pasta `@Resources`.
- **Exportação:** Geração automatizada do código `.ini` estruturado e pronto para uso no Rainmeter.

## 🚀 Como Executar

1. Clone o repositório ou baixe os arquivos fonte.
2. Instale as dependências necessárias através do arquivo `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```
3. Execute o script principal:
   ```bash
   python main.py
   ```
4. Utilize a interface visual para começar a desenhar sua skin!

## 🛠️ Tecnologias Utilizadas

- **Python 3.10+**
- **PyQt6** (Interface Gráfica)
- **Pillow** (Processamento de Imagem)

## 📋 Roadmap e Arquitetura

O planejamento detalhado da aplicação, incluindo as fases de desenvolvimento, design da interface e arquitetura de classes, pode ser encontrado no arquivo [`TO_CODER.md`](TO_CODER.md).
