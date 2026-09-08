
## Sobre o projeto

O **Politicagem** é um agregador de notícias que reúne em uma única página os principais despachos de veículos independentes, investigativos, progressistas e de esquerda do Brasil e América Latina. 

As notícias são buscadas em tempo real via **RSS**, sem armazenamento em banco de dados. Cada visita apresenta uma notícia principal selecionada aleatoriamente, e todas as matérias são ordenadas cronologicamente por horário de publicação.

---

## Funcionalidades


- Tema escuro monocromático
- Seleção aleatória da notícia principal da capa
- Ordenação cronológica por horário de publicação
- Busca por palavra-chave em tempo real
- Agregação via RSS de +40 fontes
- Múltiplos parágrafos por artigo (mínimo 4)
- Modo terminal (sem servidor web)
- Visualização completa de artigos via scraping
- Layout responsivo com 4 colunas para desktop
- Correção de quebra de texto em colunas
- Popup de doação PIX configurado para 10 minutos
- **Geração de snapshots estáticos para IPFS** (descentralização)

---

## Snapshots estáticos e IPFS

O Politicagem agora suporta geração de snapshots estáticos que podem ser publicados no IPFS para acesso descentralizado.

### Gerar snapshot estático

```bash
# Gerar snapshot com extração de artigos
python snapshot_generator.py

# Com opções personalizadas
python snapshot_generator.py --output meu_snapshot --limit 10

# Sem extração de artigos (apenas página principal)
python snapshot_generator.py --no-extract
```

### Upload para IPFS

O script `generate_snapshot.sh` automatiza todo o processo:

```bash
./generate_snapshot.sh
```

Este script:
1. Gera o snapshot estático
2. Faz upload para IPFS
3. Retorna o CID para configurar seu domínio

### Pré-requisitos para IPFS

**Nota:** O IPFS não é uma dependência Python, mas uma ferramenta externa.

- IPFS instalado e rodando: https://docs.ipfs.io/install/
- Nó IPFS iniciado: `ipfs daemon`

### Acessar via IPFS

Após o upload, você pode acessar via:
- Gateway público: `https://ipfs.io/ipfs/<CID>`
- Gateway local: `http://localhost:8080/ipfs/<CID>`

Para configurar domínios descentralizados (.eth, .tezos), use o CID retornado.

---

## Tecnologias

- **Python 3** + **Flask** — servidor web
- **feedparser** — leitura de feeds RSS
- **requests** — requisições HTTP
- **beautifulsoup4** — parsing HTML
- **python-dateutil** — manipulação de datas
- **readability-lxml** — extração de conteúdo de páginas web
- **lxml_html_clean** — compatibilidade com Python 3.13+
- **Jinja2** — templates HTML (geração de snapshots estáticos)
- **IPFS** — rede descentralizada para publicação de snapshots (instalação externa)
- **Google Fonts** — UnifrakturMaguntia, IM Fell English, Playfair Display, Libre Baskerville
- **HTML/CSS** — design vintage responsivo com tema escuro monocromático

---

## Como rodar localmente

**Pré-requisitos:** Certifique-se de ter o Python 3 (versão 3.6 ou superior) e o pip instalados no seu sistema.

**Nota de compatibilidade:** O projeto foi testado e funciona com Python 3.13. As dependências foram atualizadas para garantir compatibilidade com versões mais recentes do Python.

### 1. Clone o repositório

```bash
git clone https://github.com/marcelomodular/politicagem
cd politicagem
```

### 2. Crie um ambiente virtual (recomendado)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Inicie o servidor

```bash
python app.py
```

Acesse **http://localhost:5000** no navegador.

### Modo terminal (sem servidor)

Para ver as notícias direto no terminal:

```bash
python main.py
```

---

## Versão desktop (Electron)

Também existe uma versão desktop em `electron-app/`.

```bash
cd electron-app
npm install
npm start
```

---

## Estrutura do projeto

```
politicagem/
├── app.py                    # Servidor Flask com ordenação cronológica e seleção aleatória
├── scraper.py                # Lógica de scraping via RSS (+40 fontes)
├── main.py                   # Modo terminal
├── snapshot_generator.py     # Gerador de snapshots estáticos para IPFS
├── security_utils.py         # Utilitários de segurança para URLs
├── requirements.txt          # Dependências Python
├── README.md                 # Esta documentação
├── LICENSE                   # Licença MIT
├── .gitignore                # Arquivos ignorados pelo Git
├── generate_snapshot.sh      # Script automático para gerar e fazer upload para IPFS
├── update_snapshot_cid.sh    # Script para atualizar metadata com CID após upload
├── static_snapshots/         # Diretório para snapshots estáticos gerados
└── templates/
    ├── index.html            # Interface estilo jornal com 4 colunas
    └── visualizar.html       # Página para visualização completa de artigos
```

---

## Contribuindo

Quer adicionar uma nova fonte? Basta editar `scraper.py` e incluir a URL do feed RSS e o nome do veículo na lista `SOURCES`:

```python
SOURCES = [
    ...
    ("https://exemplo.com.br/feed/", "Nome do Veículo"),
]
```

---

## Licença

MIT — use, modifique e distribua livremente.

---

*"A imprensa é a vista da nação."* — Hipólito da Costa, fundador do Correio Braziliense (1808)



## Onboarding CLI

Para facilitar a primeira configuracao e criar atalho com icone do Politicagem:

```bash
python onboard_cli.py
```

Modo automatico (sem perguntas):

```bash
python onboard_cli.py --auto
```

Pular instalacao do IPFS (apenas Python e Electron):

```bash
python onboard_cli.py --skip-ipfs
```

O onboarding:
- explica a proposta do projeto (agregador RSS sem armazenamento local);
- instala dependencias Python;
- instala e configura IPFS automaticamente (Linux, macOS, Windows);
- torna o script de snapshot executavel;
- instala dependencias Electron;
- cria atalho na Area de Trabalho (Windows) usando o icone `electron-app/assets/politicagem-p.ico`.
