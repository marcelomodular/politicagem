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

    # ── Imprensa de esquerda / progressista ──
    ("https://vermelho.org.br/feed/",                       "Vermelho"),
    ("https://operamundi.uol.com.br/feed/",                 "Opera Mundi"),
    ("https://jacobin.com.br/feed/",                        "Jacobin Brasil"),
    ("https://diplomatique.org.br/feed/",                   "Le Monde Diplomatique"),
    ("https://mst.org.br/feed/",                            "MST"),
    ("https://iclnoticias.com.br/feed/",                    "ICL Notícias"),
    ("https://revistaforum.com.br/feed/",                   "Revista Fórum"),
    ("https://jornalggn.com.br/feed/",                      "Jornal GGN"),
    ("https://cartacapital.com.br/feed/",                   "Carta Capital"),
    ("https://www.brasildefato.com.br/rss.xml",             "Brasil de Fato"),
    ("https://www.redebrasilatual.com.br/rss.xml",          "Rede Brasil Atual"),
    ("https://www.juventuderebelde.uol.com.br/feed/",       "Juventude Rebelde"),
    ("https://resistir.info/feed/",                         "Resistência"),
    ("https://www.esquerdaonline.com.br/feed/",             "Esquerda.net"),
    ("https://www.criteriohoy.com/feed/",                   "Crítica HN"),
    ("https://consultasocialista.com.br/feed/",             "Consulta Socialista"),

    # ── Partidos / organizações ──
    ("https://fpabramo.org.br/feed/",                       "Fundação Perseu Abramo"),
    ("https://pcb.org.br/feed/",                            "PCB"),
    ("https://www.psol.org.br/feed/",                       "PSOL"),
    ("https://www.pstu.org.br/feed/",                       "PSTU"),
    ("https://www.pcdob.org.br/feed/",                      "PCdoB"),
    ("https://www.pt.org.br/feed/",                         "Partido dos Trabalhadores"),
    ("https://www.cut.org.br/feed/",                        "CUT - Central Única dos Trabalhadores"),
    ("https://www.ctb.org.br/feed/",                        "CTB - Central dos Trabalhadores e Trabalhadoras"),
    ("https://www.nova.org.br/feed/",                       "Nova Central Sindical"),
    ("https://www.csb.org.br/feed/",                        "CSB - Central dos Sindicatos Brasileiros"),

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
    ("https://jonesmanoel.com.br/feed/",                    "Jones Manoel"),
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
