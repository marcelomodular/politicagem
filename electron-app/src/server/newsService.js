const Parser = require('rss-parser');
const defaultSources = require('./newsSources');

const parser = new Parser({ timeout: 10000 });

function normalizeDate(raw) {
  if (!raw) return null;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
}

function summarize(text = '') {
  const clean = String(text).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  if (!clean) return 'Sem resumo disponivel.';
  return clean.length > 800 ? `${clean.slice(0, 797)}...` : clean;
}

async function fetchSource(url, fonte, limit = 5) {
  try {
    const feed = await parser.parseURL(url);
    return (feed.items || []).slice(0, limit).map((item) => {
      const rawDate = item.isoDate || item.pubDate || item.published || '';
      const publishedDate = normalizeDate(rawDate);

      return {
        titulo: item.title || 'Sem titulo',
        link: item.link || '#',
        resumo: summarize(item.contentSnippet || item.content || item.summary || ''),
        fonte,
        data: rawDate,
        publishedAt: publishedDate ? publishedDate.toISOString() : null,
      };
    });
  } catch {
    return [];
  }
}

function pickHeadline(list) {
  if (!list.length) return list;
  const copy = [...list];
  const index = Math.floor(Math.random() * copy.length);
  const [headline] = copy.splice(index, 1);
  return [headline, ...copy];
}

async function getAllNews({ busca = '', limitPerSource = 5, sources = defaultSources } = {}) {
  const settled = await Promise.all(
    sources.map(([url, fonte]) => fetchSource(url, fonte, limitPerSource))
  );

  let noticias = settled.flat();

  if (busca) {
    const term = busca.toLowerCase();
    noticias = noticias.filter(
      (n) => n.titulo.toLowerCase().includes(term) || n.resumo.toLowerCase().includes(term)
    );
  }

  noticias.sort((a, b) => {
    const dateA = a.publishedAt ? new Date(a.publishedAt).getTime() : 0;
    const dateB = b.publishedAt ? new Date(b.publishedAt).getTime() : 0;
    return dateB - dateA;
  });

  return pickHeadline(noticias);
}

module.exports = { getAllNews };
