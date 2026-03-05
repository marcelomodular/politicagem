function escapeHtml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatDateLabel(value) {
  if (!value) return 'Data nao informada';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('pt-BR');
}

function makeRssViewerLink(noticia) {
  const url = new URL('/rss-viewer.html', window.location.origin);
  url.searchParams.set('url', noticia.link || '#');
  url.searchParams.set('titulo', noticia.titulo || 'Sem titulo');
  url.searchParams.set('fonte', noticia.fonte || 'Fonte desconhecida');
  url.searchParams.set('data', formatDateLabel(noticia.publishedAt || noticia.data));
  url.searchParams.set('resumo', noticia.resumo || '');
  return url.toString();
}

function buildHeadline(top) {
  if (!top) return '<div class="empty">Nenhum despacho encontrado.</div>';

  return `
    <div class="headline-banner">
      <div style="font-size:0.72rem;letter-spacing:0.15em;color:var(--red);text-transform:uppercase;">Noticia de destaque</div>
      <a href="${makeRssViewerLink(top)}" target="_blank" rel="noreferrer"><h2>${escapeHtml(top.titulo)}</h2></a>
      <p>${escapeHtml(top.resumo || '')}</p>
      <div class="date-info">${escapeHtml(top.fonte)} - ${escapeHtml(formatDateLabel(top.publishedAt || top.data))}</div>
    </div>
  `;
}

function buildColumns(rest) {
  if (!rest.length) return '<div class="empty">Nenhuma materia adicional para esta edicao.</div>';

  const perCol = Math.ceil(rest.length / 4);
  const columns = [0, 1, 2, 3].map((colIdx) => {
    const start = colIdx * perCol;
    const end = start + perCol;
    const items = rest.slice(start, end);

    const cards = items
      .map(
        (noticia) => `
        <article class="article">
          <div class="article-source">${escapeHtml(noticia.fonte)}</div>
          <h3><a href="${makeRssViewerLink(noticia)}" target="_blank" rel="noreferrer">${escapeHtml(noticia.titulo)}</a></h3>
          <div class="byline">${escapeHtml(formatDateLabel(noticia.publishedAt || noticia.data))}</div>
          <p>${escapeHtml(noticia.resumo || 'Sem resumo disponivel.')}</p>
          <span class="source-tag">Abrir janela RSS</span>
        </article>
      `
      )
      .join('');

    return `<div class="col">${cards}</div>`;
  });

  return `
    <div class="section-rule">Despachos Telegraphicos</div>
    <div class="columns">${columns.join('')}</div>
  `;
}

async function loadNews(busca = '') {
  const statsBar = document.getElementById('stats-bar');
  const headline = document.getElementById('headline');
  const list = document.getElementById('list');

  statsBar.textContent = 'Carregando noticias...';

  try {
    const params = new URLSearchParams();
    if (busca) params.set('busca', busca);

    const response = await fetch(`/api/news?${params.toString()}`);
    if (!response.ok) throw new Error('Erro ao obter noticias.');

    const data = await response.json();
    const noticias = data.noticias || [];
    const top = noticias[0];
    const rest = noticias.slice(1);

    document.getElementById('news-count').textContent = `Numero ${noticias.length}`;
    statsBar.textContent = busca
      ? `${noticias.length} resultado(s) para "${busca}"`
      : `${noticias.length} despachos recebidos nesta edicao`;

    headline.innerHTML = buildHeadline(top);
    list.innerHTML = buildColumns(rest);
  } catch {
    headline.innerHTML = '';
    list.innerHTML = '<div class="empty">Falha ao carregar os feeds RSS. Tente novamente.</div>';
    statsBar.textContent = 'Erro ao carregar noticias';
  }
}

function renderChannels(canais = []) {
  const container = document.getElementById('channel-list');

  if (!canais.length) {
    container.innerHTML = '<div class="empty">Nenhum canal cadastrado.</div>';
    return;
  }

  const rows = canais
    .filter((canal) => canal.enabled)
    .map(
      (canal) => `
      <div class="channel-row">
        <div>
          <strong>${escapeHtml(canal.fonte)}</strong>
          <div class="channel-url">${escapeHtml(canal.url)}</div>
        </div>
        <button type="button" class="channel-remove" data-url="${escapeHtml(canal.url)}">Remover</button>
      </div>
    `
    )
    .join('');

  container.innerHTML = rows || '<div class="empty">Nenhum canal ativo.</div>';

  container.querySelectorAll('.channel-remove').forEach((button) => {
    button.addEventListener('click', async () => {
      await removeChannel(button.dataset.url);
    });
  });
}

function setChannelError(message = '') {
  const box = document.getElementById('channel-error');
  if (!message) {
    box.style.display = 'none';
    box.textContent = '';
    return;
  }
  box.style.display = 'block';
  box.textContent = message;
}

async function loadChannels() {
  setChannelError('');
  const response = await fetch('/api/channels');
  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error || 'Erro ao carregar canais.');
  }

  renderChannels(data.canais || []);
}

async function addChannel(event) {
  event.preventDefault();
  setChannelError('');

  const fonte = document.getElementById('channel-name').value.trim();
  const url = document.getElementById('channel-url').value.trim();

  try {
    const response = await fetch('/api/channels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ fonte, url }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Erro ao adicionar canal.');

    document.getElementById('channel-form').reset();
    renderChannels(data.canais || []);
    await loadNews(document.getElementById('busca').value.trim());
  } catch (error) {
    setChannelError(error.message);
  }
}

async function removeChannel(url) {
  setChannelError('');

  try {
    const response = await fetch(`/api/channels?url=${encodeURIComponent(url)}`, {
      method: 'DELETE',
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Erro ao remover canal.');

    renderChannels(data.canais || []);
    await loadNews(document.getElementById('busca').value.trim());
  } catch (error) {
    setChannelError(error.message);
  }
}

function setupChannelsPanel() {
  const panel = document.getElementById('channels-panel');
  const toggle = document.getElementById('channels-toggle');

  toggle.addEventListener('click', async () => {
    const opened = panel.style.display !== 'none';
    panel.style.display = opened ? 'none' : 'block';

    if (!opened) {
      try {
        await loadChannels();
      } catch (error) {
        setChannelError(error.message);
      }
    }
  });

  document.getElementById('channel-form').addEventListener('submit', addChannel);
}

function setDate() {
  const now = new Date();
  document.getElementById('dateline-date').textContent = now.toLocaleDateString('pt-BR', {
    weekday: 'long',
    day: '2-digit',
    month: 'long',
    year: 'numeric',
  });
}

document.getElementById('search-form').addEventListener('submit', (event) => {
  event.preventDefault();
  const busca = document.getElementById('busca').value.trim();
  loadNews(busca);
});

setupChannelsPanel();
setDate();
loadNews();
