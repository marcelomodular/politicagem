const express = require('express');
const path = require('path');
const cheerio = require('cheerio');
const { JSDOM } = require('jsdom');
const { Readability } = require('@mozilla/readability');
const { getAllNews } = require('./newsService');
const channelStore = require('./channelStore');

let server;

function sanitizeHtml(html = '') {
  return String(html)
    .replace(/<script[\s\S]*?<\/script>/gi, '')
    .replace(/<style[\s\S]*?<\/style>/gi, '')
    .replace(/<iframe[\s\S]*?<\/iframe>/gi, '');
}

function normalizeText(text = '') {
  return String(text).replace(/\s+/g, ' ').trim();
}

function textSignature(text = '') {
  return normalizeText(text)
    .toLowerCase()
    .replace(/[^\p{L}\p{N}]+/gu, ' ')
    .trim();
}

function looksLikeDateNoise(text = '') {
  const value = normalizeText(text).toLowerCase();
  if (!value) return false;

  const patterns = [
    /^\d{4}-\d{2}-\d{2}t?\d{0,2}:?\d{0,2}/,
    /^\d{2}\.\d{2}\.\d{4}/,
    /^\d{2}\/\d{2}\/\d{4}/,
    /^\d{1,2}:\d{2}(:\d{2})?$/,
  ];

  return patterns.some((pattern) => pattern.test(value));
}

function cleanArticleHtml(html, { titulo = '', subtitulo = '', fonteSite = '' } = {}) {
  const $ = cheerio.load(`<article id="content-root">${sanitizeHtml(html)}</article>`, {
    decodeEntities: false,
  });
  const root = $('#content-root');

  root.find('script, style, noscript, nav, footer, header, aside, form, button, input, iframe, svg').remove();
  root.find('[class*="share"], [class*="social"], [class*="related"], [class*="newsletter"], [class*="banner"], [class*="breadcrumb"], [class*="advert"], [id*="share"], [id*="social"]').remove();

  const seen = new Set();
  const titleSig = textSignature(titulo);
  const subtitleSig = textSignature(subtitulo);
  const sourceSig = textSignature(fonteSite);

  root.find('p, li, time, h1, h2, h3, h4, h5, h6, blockquote').each((_, el) => {
    const node = $(el);
    if (node.find('img').length > 0) return;

    const raw = normalizeText(node.text());
    if (!raw) {
      node.remove();
      return;
    }

    const sig = textSignature(raw);
    const isOnlyUrl = /^https?:\/\/\S+$/i.test(raw);
    const isDuplicate = sig && seen.has(sig);
    const isTitleRepeat = sig && (sig === titleSig || sig === subtitleSig);
    const isDateNoise = raw.length < 60 && looksLikeDateNoise(raw);
    const isSourceLine = sig && sourceSig && sig === sourceSig;
    const words = raw.split(/\s+/).filter(Boolean);
    const isCategoryLike =
      words.length > 0 &&
      words.length <= 4 &&
      raw.length <= 35 &&
      raw === raw.toLowerCase() &&
      /^[\p{L}\s-]+$/u.test(raw);
    const hasDateMetadata = /\b\d{2}[./-]\d{2}[./-]\d{4}\b/.test(raw) && raw.length < 180;
    const hasTeaserMetadata = /\.\.\.\s*\d{2}[./-]\d{2}[./-]\d{4}/.test(raw);
    const lower = raw.toLowerCase();
    const promoKeywords = [
      'telegram',
      'baixe o nosso aplicativo',
      'conteudos exclusivos',
      'conteúdos exclusivos',
      'grande midia',
      'grande mídia',
      'siga a ',
      'siga-nos',
      'assine',
      'newsletter',
      'apoie',
      'patrocinado',
    ];
    const hasPromoNoise = promoKeywords.some((keyword) => lower.includes(keyword));
    const isTinyLabel = words.length > 0 && words.length <= 2 && raw.length <= 20 && /^[\p{L}\s-]+$/u.test(raw);

    if (isOnlyUrl || isDuplicate || isTitleRepeat || isDateNoise || isSourceLine || isCategoryLike || hasDateMetadata || hasTeaserMetadata || hasPromoNoise || isTinyLabel) {
      node.remove();
      return;
    }

    const stripped = raw.replace(/\s+[|,-]?\s*\d{2}[./-]\d{2}[./-]\d{4}(?:,\s*[^,]{1,40})?$/, '').trim();
    if (stripped && stripped !== raw && stripped.length > 80) {
      node.text(stripped);
    }

    if (sig) {
      seen.add(sig);
    }
  });

  root.find('*').toArray().reverse().forEach((el) => {
    const node = $(el);
    const hasMedia = node.find('img, video, picture').length > 0;
    const text = normalizeText(node.text());
    if (!hasMedia && !text && node.children().length === 0) {
      node.remove();
    }
  });

  root.find('img').each((_, el) => {
    const node = $(el);
    const src = node.attr('src') || node.attr('data-src') || node.attr('data-lazy-src');
    if (!src) {
      node.remove();
      return;
    }
    node.attr('src', src);
    node.removeAttr('srcset');
    node.removeAttr('loading');
  });

  const cleanedHtml = root.html() || '';
  const cleanedTextLength = normalizeText(root.text()).length;

  if (cleanedTextLength >= 400) {
    return cleanedHtml;
  }

  const fallback$ = cheerio.load(`<article id="fallback-root">${sanitizeHtml(html)}</article>`, {
    decodeEntities: false,
  });
  const fallbackRoot = fallback$('#fallback-root');
  fallbackRoot.find('script, style, noscript, nav, footer, header, aside, form, button, input, iframe, svg').remove();
  fallbackRoot.find('[class*="share"], [class*="social"], [class*="related"], [class*="newsletter"], [class*="banner"], [class*="breadcrumb"], [class*="advert"], [id*="share"], [id*="social"]').remove();

  return fallbackRoot.html() || cleanedHtml;
}

function resolveImageUrl(image, baseUrl) {
  if (!image) return null;
  try {
    return new URL(image, baseUrl).href;
  } catch {
    return image;
  }
}

async function extractContent(url) {
  const response = await fetch(url, {
    headers: {
      'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
      Accept: 'text/html,application/xhtml+xml',
    },
    signal: AbortSignal.timeout(15000),
  });

  if (!response.ok) {
    throw new Error(`Falha ao carregar artigo (${response.status})`);
  }

  const html = await response.text();
  const $ = cheerio.load(html);
  const dom = new JSDOM(html, { url });
  const reader = new Readability(dom.window.document);
  const article = reader.parse();

  if (!article || !article.content) {
    return {
      sucesso: false,
      titulo: $('title').text() || 'Sem titulo',
      subtitulo: '',
      imagem: null,
      corpoHtml: '',
    };
  }

  const subtitulo =
    $('meta[property="og:description"]').attr('content') ||
    $('meta[name="description"]').attr('content') ||
    $('meta[name="twitter:description"]').attr('content') ||
    article.excerpt ||
    '';
  const fonteSite = $('meta[property="og:site_name"]').attr('content') || '';

  const firstImage =
    $('meta[property="og:image"]').attr('content') ||
    $('meta[name="twitter:image"]').attr('content') ||
    $('article img').first().attr('src') ||
    $('img').first().attr('src') ||
    null;

  const corpoHtml = cleanArticleHtml(article.content, {
    titulo: article.title || $('title').text() || '',
    subtitulo,
    fonteSite,
  }).slice(0, 80000);

  return {
    sucesso: true,
    titulo: article.title || $('title').text() || 'Sem titulo',
    subtitulo: normalizeText(subtitulo),
    imagem: resolveImageUrl(firstImage, url),
    corpoHtml,
  };
}

async function startServer({ dataDir } = {}) {
  const app = express();
  const publicDir = path.resolve(__dirname, '..', 'public');

  await channelStore.initStore(dataDir || path.resolve(process.cwd(), '.data'));

  app.use(express.json());
  app.use(express.static(publicDir));

  app.get('/api/news', async (req, res) => {
    try {
      const busca = String(req.query.busca || '').trim();
      const sources = await channelStore.getActiveSources();
      const noticias = await getAllNews({ busca, limitPerSource: 5, sources });
      res.json({ noticias, busca });
    } catch {
      res.status(500).json({ error: 'Erro ao carregar noticias.' });
    }
  });

  app.get('/api/channels', async (_req, res) => {
    try {
      const canais = await channelStore.getChannelList();
      res.json({ canais });
    } catch {
      res.status(500).json({ error: 'Erro ao carregar canais.' });
    }
  });

  app.post('/api/channels', async (req, res) => {
    try {
      await channelStore.addChannel(req.body || {});
      const canais = await channelStore.getChannelList();
      res.status(201).json({ canais });
    } catch (error) {
      res.status(400).json({ error: error.message });
    }
  });

  app.delete('/api/channels', async (req, res) => {
    try {
      await channelStore.removeChannel(String(req.query.url || ''));
      const canais = await channelStore.getChannelList();
      res.json({ canais });
    } catch (error) {
      res.status(400).json({ error: error.message });
    }
  });

  app.get('/api/extract', async (req, res) => {
    const { url } = req.query;
    if (!url) {
      res.status(400).json({ error: 'URL nao fornecida.' });
      return;
    }

    try {
      const data = await extractContent(String(url));
      res.json(data);
    } catch (error) {
      res.status(500).json({ error: `Erro ao extrair conteudo: ${error.message}` });
    }
  });

  app.get('/health', (_req, res) => {
    res.json({ ok: true });
  });

  const port = await new Promise((resolve) => {
    server = app.listen(0, '127.0.0.1', () => {
      const address = server.address();
      resolve(address.port);
    });
  });

  return { port, server };
}

function stopServer(serverRef) {
  return new Promise((resolve) => {
    if (!serverRef?.server) {
      resolve();
      return;
    }
    serverRef.server.close(() => resolve());
  });
}

module.exports = { startServer, stopServer };
