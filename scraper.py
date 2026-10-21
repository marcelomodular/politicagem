import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import feedparser
import requests


REQUEST_TIMEOUT_SECONDS = 10
CACHE_TTL_SECONDS = 120
MAX_WORKERS = 8
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
# Alguns servidores bloqueiam o User-Agent do Chrome em Windows (403) mas
# aceitam o mesmo Chrome em Linux. Tentamos o primario e, se falhar, o alternativo.
FALLBACK_USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
USER_AGENTS = (USER_AGENT, FALLBACK_USER_AGENT)
# Status que indicam bloqueio por User-Agent (e nao por feed inexistente).
BLOCKED_STATUS_CODES = {403, 406, 429}
SOURCES_FILE = Path(__file__).resolve().with_name("news_sources.json")


_cache_lock = threading.Lock()
_cache_state = {
    "expires_at": 0.0,
    "limit_per_source": None,
    "news": [],
}


def _load_sources():
    try:
        parsed = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

    normalized = []
    for item in parsed:
        if not isinstance(item, list) or len(item) != 2:
            continue
        url, name = item
        if not isinstance(url, str) or not isinstance(name, str):
            continue
        normalized.append((url.strip(), name.strip()))

    return normalized


SOURCES = _load_sources()


def _fetch_feed(url):
    """
    Busca o feed, trocando de User-Agent apenas quando o servidor bloqueia
    por status HTTP (403/406/429). Erros de rede e timeout nao sao repetidos:
    um dominio fora do ar apenascustaria o dobro do tempo de espera.
    """
    last_error = None

    for user_agent in USER_AGENTS:
        try:
            response = requests.get(
                url,
                timeout=REQUEST_TIMEOUT_SECONDS,
                headers={"User-Agent": user_agent},
            )
        except Exception as error:
            raise error

        if response.status_code in BLOCKED_STATUS_CODES:
            last_error = requests.HTTPError(
                f"HTTP {response.status_code} bloqueado por User-Agent.",
                response=response,
            )
            continue

        response.raise_for_status()
        return response.content

    raise last_error if last_error else RuntimeError("Falha ao buscar feed.")


def _extract_entry_date(entry, feed_level=None):
    """
    Extrai a data de publicacao de uma entrada RSS.

    Alguns feeds (ex.: Opera Mundi) publicam sem <pubDate> no item, mas
    trazem <lastBuildDate> no channel. Nesses casos caimos para a data do
    feed para que a noticia ainda entre na ordenacao cronologica.
    """
    for key in ("published", "updated", "created", "date"):
        value = entry.get(key)
        if value:
            return value

    if feed_level:
        for key in ("published_parsed", "updated_parsed", "created_parsed"):
            parsed = feed_level.get(key)
            if parsed:
                try:
                    from time import strftime

                    return strftime("%a, %d %b %Y %H:%M:%S %z", parsed)
                except Exception:
                    continue

        for key in ("updated", "published", "lastBuildDate"):
            value = feed_level.get(key)
            if value:
                return value

    return ""


def get_rss_news(url, source_name, limit=5):
    try:
        feed_data = _fetch_feed(url)
        feed = feedparser.parse(feed_data)
        feed_level = feed.feed if hasattr(feed, "feed") else {}
        noticias = []
        seen_titles = set()

        # Alguns feeds repetem o mesmo texto com links levemente diferentes
        # (ex.: a Embaixada da Venezuela publica "/post/" e "/post-2/").
        # Pegamos mais itens que o limite para ainda ter 'limit' uniques.
        for entry in feed.entries[: limit * 3]:
            titulo = (entry.get("title") or "Sem titulo").strip()
            assinatura = titulo.casefold()

            if assinatura in seen_titles:
                continue

            seen_titles.add(assinatura)
            noticias.append(
                {
                    "titulo": entry.get("title", "Sem titulo"),
                    "link": entry.get("link", "#"),
                    "resumo": entry.get("summary", ""),
                    "fonte": source_name,
                    "data": _extract_entry_date(entry, feed_level),
                }
            )

            if len(noticias) >= limit:
                break

        return noticias
    except Exception:
        return []


def _fetch_all_sources(limit_per_source, sources):
    all_news = []
    max_workers = min(MAX_WORKERS, max(1, len(sources)))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(get_rss_news, url, name, limit_per_source): (url, name)
            for url, name in sources
        }

        for future in as_completed(futures):
            all_news.extend(future.result())

    deduplicated = []
    seen_links = set()
    for noticia in all_news:
        link = noticia.get("link")
        if link and link in seen_links:
            continue
        if link:
            seen_links.add(link)
        deduplicated.append(noticia)

    return deduplicated


def get_all_news(limit_per_source=5):
    now = time.time()
    with _cache_lock:
        has_valid_cache = (
            _cache_state["news"]
            and _cache_state["limit_per_source"] == limit_per_source
            and _cache_state["expires_at"] > now
        )
        if has_valid_cache:
            return list(_cache_state["news"])

    refreshed_news = _fetch_all_sources(limit_per_source, SOURCES)

    with _cache_lock:
        _cache_state["news"] = list(refreshed_news)
        _cache_state["limit_per_source"] = limit_per_source
        _cache_state["expires_at"] = time.time() + CACHE_TTL_SECONDS

    return refreshed_news
