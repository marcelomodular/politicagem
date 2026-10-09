#!/usr/bin/env python3
"""
Gerador de snapshots estáticos do Politicagem para IPFS.
Gera HTML estático com as notícias atuais do RSS e páginas de artigos.
"""

import json
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, unquote_plus, urljoin

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from readability import Document

from scraper import get_all_news
from security_utils import is_public_http_url, parse_published_date

REQUEST_TIMEOUT_SECONDS = 15
MAX_REDIRECTS = 3
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/122.0.0.0 Safari/537.36"
)
ALLOWED_INLINE_TAGS = {
    "p",
    "br",
    "strong",
    "b",
    "em",
    "i",
    "ul",
    "ol",
    "li",
    "blockquote",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "a",
    "img",
}


def sanitize_article_html(content_html, base_url):
    soup = BeautifulSoup(content_html or "", "html.parser")

    for bad in soup.find_all(
        [
            "script",
            "style",
            "iframe",
            "object",
            "embed",
            "form",
            "input",
            "button",
            "noscript",
            "svg",
            "canvas",
        ]
    ):
        bad.decompose()

    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_INLINE_TAGS:
            tag.unwrap()
            continue

        allowed_attrs = set()
        if tag.name == "a":
            allowed_attrs = {"href", "title", "target", "rel"}
        if tag.name == "img":
            allowed_attrs = {"src", "alt", "title"}

        for attr_name in list(tag.attrs.keys()):
            attr_lower = attr_name.lower()
            if attr_lower.startswith("on"):
                del tag.attrs[attr_name]
                continue
            if attr_lower in {"style", "class", "id", "srcset", "loading"}:
                del tag.attrs[attr_name]
                continue
            if attr_name not in allowed_attrs:
                del tag.attrs[attr_name]

        if tag.name == "a":
            href = tag.get("href")
            if href:
                resolved = urljoin(base_url, href)
                if is_public_http_url(resolved):
                    tag["href"] = resolved
                    tag["target"] = "_blank"
                    tag["rel"] = "noopener noreferrer"
                else:
                    tag.unwrap()
            else:
                tag.unwrap()

        if tag.name == "img":
            src = tag.get("src")
            if not src:
                tag.decompose()
                continue
            resolved = urljoin(base_url, src)
            if is_public_http_url(resolved):
                tag["src"] = resolved
            else:
                tag.decompose()

    return str(soup)


def fetch_public_url(url):
    current_url = url
    headers = {"User-Agent": USER_AGENT}

    with requests.Session() as session:
        for _ in range(MAX_REDIRECTS + 1):
            if not is_public_http_url(current_url):
                raise ValueError("URL bloqueada por politica de seguranca.")

            response = session.get(
                current_url,
                headers=headers,
                timeout=REQUEST_TIMEOUT_SECONDS,
                allow_redirects=False,
            )

            if 300 <= response.status_code < 400 and response.headers.get("Location"):
                current_url = urljoin(current_url, response.headers["Location"])
                continue

            response.raise_for_status()
            return current_url, response

    raise ValueError("Redirecionamentos excessivos.")


def extract_article_content(url):
    """Extrai o conteúdo de um artigo para versão estática."""
    try:
        final_url, response = fetch_public_url(url)
        html_text = response.text
        original_soup = BeautifulSoup(html_text, 'html.parser')

        image_url = None
        og_image = original_soup.find('meta', property='og:image')
        if og_image:
            image_url = og_image.get('content')

        if not image_url:
            twitter_image = original_soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image:
                image_url = twitter_image.get('content')

        if not image_url:
            article_img = original_soup.find('article')
            if article_img:
                img = article_img.find('img')
                if img and img.get('src'):
                    image_url = img.get('src')

        if not image_url:
            any_img = original_soup.find('img', src=True)
            if any_img:
                src = any_img.get('src')
                if src and not any(x in src.lower() for x in ['logo', 'icon', 'banner', 'ads', 'pixel', 'tracking']):
                    image_url = src

        if image_url:
            image_url = urljoin(final_url, image_url)
            if not is_public_http_url(image_url):
                image_url = None

        doc = Document(html_text)
        title = doc.short_title() or doc.title() or 'Sem titulo'
        content_html = doc.summary(html_partial=True)

        if isinstance(content_html, bytes):
            content_html = content_html.decode('utf-8', errors='ignore')

        safe_content = sanitize_article_html(content_html, base_url=final_url)
        if len(safe_content) > 80000:
            safe_content = safe_content[:80000]

        plain_text = BeautifulSoup(safe_content, 'html.parser').get_text(separator=' ', strip=True)
        if len(plain_text) < 100:
            return {
                'conteudo': safe_content,
                'titulo': title,
                'imagem': image_url,
                'sucesso': True,
                'aviso': 'Conteudo curto, pode nao ter extraido bem'
            }

        return {
            'conteudo': safe_content,
            'titulo': title,
            'imagem': image_url,
            'sucesso': True
        }

    except Exception as error:
        return {
            'error': str(error),
            'sucesso': False
        }


def generate_static_snapshot(output_dir=None, limit_per_source=5, extract_articles=True):
    """
    Gera um snapshot estático do Politicagem.
    
    Args:
        output_dir: Diretório de saída (default: static_snapshots/YYYY-MM-DD-HHMMSS)
        limit_per_source: Limite de notícias por fonte RSS
        extract_articles: Se deve extrair conteúdo dos artigos para páginas estáticas
    
    Returns:
        tuple: (caminho_do_snapshot, caminho_do_index_html)
    """
    # Configurar diretório de saída
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        output_dir = Path(__file__).parent / "static_snapshots" / timestamp
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Buscar notícias
    noticias = get_all_news(limit_per_source=limit_per_source)
    
    # Ordenar cronologicamente
    noticias.sort(
        key=lambda noticia: parse_published_date(noticia.get('data')) or datetime.min,
        reverse=True,
    )
    
    # Selecionar headline aleatório
    if noticias:
        headline_index = random.randint(0, len(noticias) - 1)
        headline = noticias[headline_index]
        noticias.pop(headline_index)
        noticias.insert(0, headline)
    
    # Configurar Jinja2
    template_dir = Path(__file__).parent / "templates"
    env = Environment(loader=FileSystemLoader(template_dir))
    
    # Criar diretório para páginas de artigos se necessário
    if extract_articles:
        articles_dir = output_dir / "visualizar"
        articles_dir.mkdir(exist_ok=True)
        
        # Mapeamento de links para arquivos estáticos
        link_to_file = {}
        
        # Processar cada notícia para extrair conteúdo
        for i, noticia in enumerate(noticias):
            print(f"📄 Processando artigo {i+1}/{len(noticias)}: {noticia['titulo'][:50]}...")
            
            # Extrair conteúdo
            article_data = extract_article_content(noticia['link'])
            
            # Gerar nome de arquivo seguro
            safe_filename = f"artigo-{i}.html"
            article_file_path = articles_dir / safe_filename
            
            # Renderizar template de visualização
            visualizar_template = env.get_template('visualizar.html')
            
            # Adaptar template para modo estático
            html_content = visualizar_template.render(
                url=noticia['link'],
                titulo=noticia['titulo'],
                fonte=noticia['fonte'],
                static_mode=True,
                article_data=article_data
            )
            
            # Salvar página do artigo
            article_file_path.write_text(html_content, encoding='utf-8')
            
            # Mapear link original para arquivo estático
            link_to_file[noticia['link']] = f"visualizar/{safe_filename}"
            
            # Adicionar dados extraídos à notícia
            noticia['static_url'] = f"visualizar/{safe_filename}"
            noticia['extracted_data'] = article_data
        
        print(f"✅ {len(noticias)} artigos processados e salvos em visualizar/")
    
    # Renderizar template principal
    template = env.get_template('index.html')
    html_content = template.render(
        noticias=noticias,
        busca='',
        static_mode=True,  # Flag para modo estático
        extract_articles=extract_articles
    )
    
    # Salvar HTML principal
    index_path = output_dir / "index.html"
    index_path.write_text(html_content, encoding='utf-8')
    
    # Criar metadata do snapshot
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "news_count": len(noticias),
        "limit_per_source": limit_per_source,
        "snapshot_version": "2.0",
        "extract_articles": extract_articles,
        "articles_generated": len(noticias) if extract_articles else 0,
        "note": "Para fazer upload para IPFS, use: ipfs add -r <snapshot_dir>",
        "correct_cid": "Será preenchido após upload para IPFS"
    }
    
    metadata_path = output_dir / "snapshot_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding='utf-8')
    
    print(f"✅ Snapshot gerado em: {output_dir}")
    print(f"📰 {len(noticias)} notícias processadas")
    print(f"📄 Index HTML: {index_path}")
    if extract_articles:
        print(f"📁 Artigos estáticos: {articles_dir}")
    
    return str(output_dir), str(index_path)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Gerar snapshot estático do Politicagem")
    parser.add_argument("--output", "-o", help="Diretório de saída")
    parser.add_argument("--limit", "-l", type=int, default=5, help="Limite de notícias por fonte")
    parser.add_argument("--no-extract", action="store_true", help="Não extrair conteúdo dos artigos")
    
    args = parser.parse_args()
    
    generate_static_snapshot(
        output_dir=args.output,
        limit_per_source=args.limit,
        extract_articles=not args.no_extract
    )