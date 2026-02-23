from flask import Flask, render_template, request
from scraper import get_all_news
import random
from datetime import datetime

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


if __name__ == '__main__':
    app.run(debug=True)
