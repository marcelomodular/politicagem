# 📰 Politicagem

> Agregador de notícias da imprensa progressista brasileira e latino-americana, com interface inspirada nos jornais do início do século XX.

---

## Sobre o projeto

O **Politicagem** é um agregador de notícias que reúne em uma única página os principais despachos de veículos independentes, investigativos, progressistas e de esquerda do Brasil e América Latina. A interface imita a estética dos jornais impressos da década de 1930 — tipografia serifada, colunas, capitulares e papel envelhecido — como contraponto irônico à era da desinformação.

As notícias são buscadas em tempo real via **RSS**, sem armazenamento em banco de dados. Cada visita apresenta uma notícia principal selecionada aleatoriamente, e todas as matérias são ordenadas cronologicamente por horário de publicação.

---

## Fontes monitoradas

| Categoria | Veículos |
|---|---|
| Imprensa investigativa | Agência Pública, Intercept Brasil, Ponte Jornalismo, Observatório da Imprensa |
| Imprensa progressista | Vermelho, Opera Mundi, Jacobin Brasil, Le Monde Diplomatique, MST, ICL Notícias, Revista Fórum, Jornal GGN, Carta Capital, Brasil de Fato, Rede Brasil Atual, Resistência, Esquerda.net, Crítica HN, Consulta Socialista, Juventude Rebelde |
| Partidos / organizações | Fundação Perseu Abramo, PCB, PSOL, PSTU, PCdoB, PT, CUT, CTB, Nova Central Sindical, CSB |
| Embaixadas | Cuba, Venezuela, Bolívia, Nicarágua, Equador, Chile, Argentina, México, Uruguai, Paraguai, Peru |
| Outros | Revista Opera, Jones Manoel, Subverta, O Minhocário |

---

## Funcionalidades

- 🗞️ Interface estilo jornal impresso dos anos 1930
- 🎲 Seleção aleatória da notícia principal da capa
- � Ordenação cronológica por horário de publicação
- �🔎 Busca por palavra-chave em tempo real
- 📡 Agregação via RSS de +40 fontes
- � Múltiplos parágrafos por artigo (mínimo 4)
- �🖥️ Modo terminal (sem servidor web)
- � Visualização completa de artigos via scraping
- � Layout responsivo com 4 colunas para desktop

---

## Tecnologias

- **Python 3** + **Flask** — servidor web
- **feedparser** — leitura de feeds RSS
- **requests** — requisições HTTP
- **beautifulsoup4** — parsing HTML
- **python-dateutil** — manipulação de datas
- **Jinja2** — templates HTML
- **Google Fonts** — UnifrakturMaguntia, IM Fell English, Playfair Display, Libre Baskerville
- **HTML/CSS** — design vintage responsivo

---

## Como rodar localmente

**Pré-requisitos:** Certifique-se de ter o Python 3 (versão 3.6 ou superior) e o pip instalados no seu sistema.

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
├── app.py              # Servidor Flask com ordenação cronológica e seleção aleatória
├── scraper.py          # Lógica de scraping via RSS (+40 fontes)
├── main.py             # Modo terminal
├── requirements.txt    # Dependências Python
├── README.md           # Esta documentação
├── LICENSE             # Licença MIT
├── .gitignore          # Arquivos ignorados pelo Git
└── templates/
    ├── index.html      # Interface estilo jornal com 4 colunas
    └── visualizar.html  # Página para visualização completa de artigos
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


