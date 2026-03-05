import feedparser

# ── RSS Sources ──────────────────────────────────────────────────────────────
# Each entry: (rss_url, display_name)
# Sources without a working public RSS feed are omitted or use best-known URL.
SOURCES = [
    # ── Imprensa independente / investigativa ──
    ("https://apublica.org/feed/",                          "Agência Pública"),
    ("https://theintercept.com/brasil/feed/",               "Intercept Brasil"),
    ("https://ponte.org/feed/",                             "Ponte Jornalismo"),
    ("https://observatoriodaimprensa.com.br/feed/",         "Observatório da Imprensa"),
    ("https://outraspalavras.net/feed",                     "Outras Palavras"),
    ("https://www.brasildefato.com.br/feed/",               "Brasil de Fato"),
    ("https://ojoioeotrigo.com.br/feed/",                   "O Joio e o Trigo"),
    ("https://www.nucleo.jor.br/rss/",                      "Núcleo Jornalismo"),
    ("https://agenciasportlight.com.br/index.php/feed/",    "Agência Sportlight"),
    ("https://passapalavra.info/feed/",                     "Passa Palavra"),
    ("https://www.nexojornal.com.br/rss.xml",               "Nexo Jornal"),
    

    # ── Imprensa de esquerda / progressista ──
    ("https://vermelho.org.br/feed/",                       "Vermelho"),
    ("https://jacobin.com.br/feed/",                        "Jacobin Brasil"),
    ("https://mst.org.br/feed/",                            "MST"),
    ("https://iclnoticias.com.br/feed/",                    "ICL Notícias"),
    ("https://consultapopularoficial.org/feed/",            "Consulta Popular"),
    ("https://piaui.uol.com.br/feed/",                      "Piauí"),

    # ── Imprensa de guerra ──
    ("https://noticiabrasil.net.br/export/rss2/archive/index.xml", "Sputnik Brasil"),
    ("https://www.aljazeera.com/xml/rss/all.xml",            "Al Jazeera"),
    ("https://operamundi.uol.com.br/rss",                    "Opera Mundi"),
    ("https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/internacional/portada", "El País Mundo"),

    # ── Embaixadas e organizações internacionais ──
    ("https://embaixadacuba.org.br/feed/",                  "Embaixada de Cuba"),
    ("https://embaixadavenezuela.org.br/feed/",             "Embaixada da Venezuela"),
    ("https://embaixadabolivia.org.br/feed/",               "Embaixada da Bolívia"),
    ("https://embaixadanicaragua.org.br/feed/",             "Embaixada da Nicarágua"),
    ("https://embaixadaequador.org.br/feed/",               "Embaixada do Equador"),
    ("https://embaixadachile.org.br/feed/",                 "Embaixada do Chile"),
    ("https://embaixadaargentina.org.br/feed/",             "Embaixada da Argentina"),
    ("https://embaixadamexico.org.br/feed/",                "Embaixada do México"),
    ("https://embaixadauruguai.org.br/feed/",               "Embaixada do Uruguai"),
    ("https://embaixadaparaguai.org.br/feed/",              "Embaixada do Paraguai"),
    ("https://embaixadaperu.org.br/feed/",                  "Embaixada do Peru"),





    # ── Outros ──
    ("https://revistaopera.com.br/feed/",                   "Revista Opera"),
    ("https://subverta.com.br/feed/",                       "Subverta"),
    ("https://ominhocario.com.br/feed/",                    "O Minhocário"),
]


def get_rss_news(url, source_name, limit=5):
    """Fetch articles from a single RSS feed."""
    try:
        feed = feedparser.parse(url)
        noticias = []
        for entry in feed.entries[:limit]:
            noticias.append({
                'titulo':  entry.get('title', 'Sem título'),
                'link':    entry.get('link', '#'),
                'resumo':  entry.get('summary', ''),
                'fonte':   source_name,
                'data':    entry.get('published', ''),
            })
        return noticias
    except Exception as e:
        print(f"Erro ao buscar {source_name}: {e}")
        return []


def get_all_news(limit_per_source=5):
    """Aggregate news from all sources."""
    all_news = []
    for url, name in SOURCES:
        all_news.extend(get_rss_news(url, name, limit=limit_per_source))
    return all_news
