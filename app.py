from flask import Flask, render_template, request, jsonify
from scraper import get_all_news
import random
from datetime import datetime
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def index():
    busca = request.args.get('busca', '').strip().lower()
    noticias = get_all_news()

    if busca:
        noticias = [
            n for n in noticias
            if busca in n['titulo'].lower() or busca in n['resumo'].lower()
        ]

    # Ordenar todas as notícias por data de publicação (mais recentes primeiro)
    def parse_date(noticia):
        if noticia.get('data'):
            try:
                # Tentar diferentes formatos de data
                formatos = [
                    '%a, %d %b %Y %H:%M:%S %Z',  # RFC 2822
                    '%Y-%m-%dT%H:%M:%S%z',       # ISO 8601
                    '%Y-%m-%d %H:%M:%S',         # YYYY-MM-DD HH:MM:SS
                    '%d/%m/%Y %H:%M',            # DD/MM/YYYY HH:MM
                    '%d/%m/%Y',                  # DD/MM/YYYY
                    '%Y-%m-%d',                  # YYYY-MM-DD
                ]
                for formato in formatos:
                    try:
                        return datetime.strptime(noticia['data'], formato)
                    except ValueError:
                        continue
                # Se nenhum formato funcionar, usar timestamp atual
                return datetime.now()
            except:
                return datetime.now()
        return datetime.now()

    # Filtrar notícias que têm data válida e ordenar por data
    noticias_com_data = [n for n in noticias if n.get('data')]
    noticias_sem_data = [n for n in noticias if not n.get('data')]

    # Ordenar notícias com data (mais recentes primeiro)
    noticias_com_data.sort(key=parse_date, reverse=True)

    # Combinar: notícias com data ordenadas + notícias sem data
    noticias = noticias_com_data + noticias_sem_data

    # Selecionar aleatoriamente a notícia principal (headline)
    if len(noticias) > 0:
        # Escolher aleatoriamente uma notícia para ser o headline
        headline_index = random.randint(0, len(noticias) - 1)
        headline = noticias[headline_index]

        # Remover o headline da lista e colocar no início
        noticias.pop(headline_index)
        noticias.insert(0, headline)

    return render_template('index.html', noticias=noticias, busca=busca)


@app.route('/visualizar')
def visualizar_noticia():
    from urllib.parse import unquote_plus
    
    url = request.args.get('url', '')
    titulo = request.args.get('titulo', '')
    fonte = request.args.get('fonte', '')
    
    # Decodificar parâmetros
    if url:
        url = unquote_plus(url)
    if titulo:
        titulo = unquote_plus(titulo)
    if fonte:
        fonte = unquote_plus(fonte)
    
    if not url:
        return jsonify({'error': 'URL não fornecida'}), 400
    
    return render_template('visualizar.html', url=url, titulo=titulo, fonte=fonte)


@app.route('/extrair_conteudo')
def extrair_conteudo():
    from urllib.parse import unquote_plus
    from readability import Document
    
    url = request.args.get('url', '')
    
    # Decodificar URL
    if url:
        url = unquote_plus(url)
    
    print(f"DEBUG: Extraindo conteúdo da URL: {url}")
    
    if not url:
        return jsonify({'error': 'URL não fornecida'}), 400
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        # Parse do HTML original para buscar imagem (decode para string)
        html_text = response.content.decode('utf-8', errors='ignore')
        original_soup = BeautifulSoup(html_text, 'html.parser')
        
        # Extrair imagem principal (og:image, twitter:image, ou primeira img do artigo)
        image_url = None
        
        # 1. Tentar og:image
        og_image = original_soup.find('meta', property='og:image')
        if og_image:
            image_url = og_image.get('content')
        
        # 2. Se não tiver, tentar twitter:image
        if not image_url:
            twitter_image = original_soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image:
                image_url = twitter_image.get('content')
        
        # 3. Se não tiver, tentar primeira img no article
        if not image_url:
            article_img = original_soup.find('article')
            if article_img:
                img = article_img.find('img')
                if img and img.get('src'):
                    image_url = img.get('src')
        
        # 4. Última tentativa: qualquer img com src válida
        if not image_url:
            any_img = original_soup.find('img', src=True)
            if any_img:
                src = any_img.get('src')
                # Ignorar logos, ícones, trackers
                if src and not any(x in src.lower() for x in ['logo', 'icon', 'banner', 'ads', 'pixel', 'tracking']):
                    image_url = src
        
        # Usar readability-lxml para extrair o conteúdo principal
        doc = Document(html_text)
        
        title = doc.title()
        content_html = doc.summary()
        
        # Garantir que content_html seja string
        if isinstance(content_html, bytes):
            content_html = content_html.decode('utf-8', errors='ignore')
        
        # Converter HTML para texto com parágrafos
        soup = BeautifulSoup(content_html, 'html.parser')
        
        # Limpar elementos indesejados dentro do conteúdo
        for elem in soup(['script', 'style', 'aside', 'nav', 'footer', 'header']):
            elem.decompose()
        
        # Usar o HTML diretamente para manter parágrafos
        text_content = str(soup)
        
        # Limitar tamanho
        if len(text_content) > 15000:
            text_content = text_content[:15000] + '...'
        
        # Limitar tamanho
        text_content = text_content[:8000] + '...' if len(text_content) > 8000 else text_content
        
        # Validar conteúdo
        if len(text_content.strip()) < 100:
            return jsonify({
                'conteudo': text_content,
                'titulo': title,
                'sucesso': True,
                'aviso': 'Conteúdo curto, pode não ter extraído bem'
            })
        
        print(f"DEBUG: Título extraído: {title}")
        print(f"DEBUG: Imagem extraída: {image_url}")
        print(f"DEBUG: Primeiros 200 chars: {text_content[:200]}...")
        
        return jsonify({
            'conteudo': text_content,
            'titulo': title,
            'imagem': image_url,
            'sucesso': True
        })
            
    except Exception as e:
        import traceback
        print(f"DEBUG: Erro: {str(e)}")
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Erro ao extrair conteúdo: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5002)
