const Parser = require('rss-parser');
const defaultSources = require('./newsSources');

const parser = new Parser({ timeout: 10000 });

// Alguns servidores (ex.: misiones.cubaminrex.cu) devolvem um header HTTP
// invalido - "X-Powered-By : -" com espaco antes dos dois-pontos. O parser
// HTTP do Node (undici) rejeita a resposta inteira, embora o XML esteja
// correto. Quando estamos dentro do Electron, o net.fetch (stack do
// Chromium) tolera esse header; por isso buscamos o corpo por ele e parseamos
// o XML separadamente.
let electronNet = null;
try {
  // eslint-disable-next-line global-require
  ({ net: electronNet } = require('electron'));
} catch {
  electronNet = null;
}

const USER_AGENT =
  'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36';
const REQUEST_TIMEOUT_MS = 10000;

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

async function fetchFeed(url) {
  if (electronNet && typeof electronNet.fetch === 'function') {
    try {
      // O net.fetch do Chromium nao aceita timeout nativo: aplicamos um
      // AbortController para nao travar o carregamento quando um dominio
      // esta fora do ar.
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

      try {
        const response = await electronNet.fetch(url, {
          headers: { 'User-Agent': USER_AGENT, Accept: 'application/rss+xml,application/xml;q=0.9,*/*;q=0.8' },
          signal: controller.signal,
        });

        if (response.ok) {
          const body = await response.text();
          if (body && body.trim()) {
            return await parser.parseString(body);
          }
        }
      } finally {
        clearTimeout(timer);
      }
    } catch {
      // Cai no caminho padrao abaixo.
    }
  }

  return parser.parseURL(url);
}

async function fetchSource(url, fonte, limit = 5) {
  try {
    const feed = await fetchFeed(url);
    const items = feed.items || [];

    const seen = new Set();
    const noticias = [];

    for (const item of items) {
      const titulo = String(item.title || 'Sem titulo').trim();
      const assinatura = titulo.toLowerCase();

      if (seen.has(assinatura)) continue;
      seen.add(assinatura);

      const rawDate = item.isoDate || item.pubDate || item.published || '';
      const publishedDate = normalizeDate(rawDate);

      noticias.push({
        titulo: item.title || 'Sem titulo',
        link: item.link || '#',
        resumo: summarize(item.contentSnippet || item.content || item.summary || ''),
        fonte,
        data: rawDate,
        publishedAt: publishedDate ? publishedDate.toISOString() : null,
      });

      if (noticias.length >= limit) break;
    }

    return noticias;
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
