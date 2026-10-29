import os
import random
from datetime import datetime
from urllib.parse import unquote_plus, urljoin

import requests
from bs4 import BeautifulSoup
from flask import Flask, jsonify, render_template, request, send_from_directory
from readability import Document

from scraper import get_all_news
from security_utils import is_public_http_url, is_safe_embed_url, parse_published_date
from snapshot_archive import (
    build_archive_payload,
    build_calendar_data,
    list_snapshots,
    resolve_snapshot_file,
    resolve_snapshot_path,
)


app = Flask(__name__)


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


@app.route('/')
def index():
    busca = request.args.get('busca', '').strip().lower()
    noticias = get_all_news()

    if busca:
        noticias = [
            n for n in noticias
            if busca in n['titulo'].lower() or busca in n['resumo'].lower()
        ]

    noticias.sort(
        key=lambda noticia: parse_published_date(noticia.get('data')) or datetime.min,
        reverse=True,
    )

    if noticias:
        headline_index = random.randint(0, len(noticias) - 1)
        headline = noticias[headline_index]
        noticias.pop(headline_index)
        noticias.insert(0, headline)

    return render_template(
        'index.html',
        noticias=noticias,
        busca=busca,
        arquivo=list_snapshots(),
    )


@app.route('/arquivo')
def arquivo():
    """Linha do tempo e calendario das edicoes (snapshots) ja geradas."""
    payload = build_archive_payload()
    return render_template(
        'arquivo.html',
        snapshots=payload['snapshots'],
        calendar=payload['calendar'],
        payload_json=payload,
    )


@app.route('/api/arquivo')
def api_arquivo():
    """Dados do arquivo em JSON, para consumo programatico."""
    return jsonify(build_archive_payload())


@app.route('/arquivo/<slug>')
@app.route('/arquivo/<slug>/')
@app.route('/arquivo/<slug>/<path:filename>')
def abrir_snapshot(slug, filename="index.html"):
    """Abre o indice ou qualquer arquivo estatico de um snapshot especifico."""
    try:
        snapshot_dir, safe_filename = resolve_snapshot_file(slug, filename)
    except ValueError:
        return jsonify({'error': 'Identificador de snapshot ou arquivo invalido.'}), 400
    except FileNotFoundError:
        return jsonify({'error': 'Snapshot ou arquivo nao encontrado.'}), 404

    return send_from_directory(
        snapshot_dir,
        safe_filename,
    )



@app.route('/visualizar')
def visualizar_noticia():
    url = request.args.get('url', '')
    titulo = request.args.get('titulo', '')
    fonte = request.args.get('fonte', '')

    if url:
        url = unquote_plus(url)
    if titulo:
        titulo = unquote_plus(titulo)
    if fonte:
        fonte = unquote_plus(fonte)

    if not url:
        return jsonify({'error': 'URL nao fornecida'}), 400

    if not is_safe_embed_url(url):
        return render_template(
            'visualizar.html',
            url='',
            titulo=titulo,
            fonte=fonte,
            url_invalida=True,
        ), 400

    return render_template('visualizar.html', url=url, titulo=titulo, fonte=fonte)


@app.route('/extrair_conteudo')
def extrair_conteudo():
    url = request.args.get('url', '')

    if url:
        url = unquote_plus(url)

    if not url:
        return jsonify({'error': 'URL nao fornecida'}), 400

    if not is_public_http_url(url):
        return jsonify({'error': 'URL bloqueada por politica de seguranca.'}), 400

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
            return jsonify({
                'conteudo': safe_content,
                'titulo': title,
                'sucesso': True,
                'aviso': 'Conteudo curto, pode nao ter extraido bem'
            })

        return jsonify({
            'conteudo': safe_content,
            'titulo': title,
            'imagem': image_url,
            'sucesso': True
        })

    except ValueError as error:
        return jsonify({'error': str(error)}), 400
    except requests.RequestException as error:
        return jsonify({'error': f'Erro de rede ao extrair conteudo: {str(error)}'}), 502
    except Exception as error:
        return jsonify({'error': f'Erro ao extrair conteudo: {str(error)}'}), 500


if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG') == '1',
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', '5000')),
    )
