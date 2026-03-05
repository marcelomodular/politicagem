function byId(id) {
  return document.getElementById(id);
}

function normalizeResumo(text = '') {
  const clean = String(text).trim();
  if (!clean) return '<p>Sem resumo RSS disponivel para esta materia.</p>';

  const paragraphs = clean
    .split(/\n{2,}/)
    .map((part) => part.trim())
    .filter(Boolean)
    .map((part) => `<p>${part}</p>`);

  return paragraphs.length ? paragraphs.join('') : `<p>${clean}</p>`;
}

function setContent() {
  const loading = byId('rss-loading');
  const errorBox = byId('rss-error');
  const contentBox = byId('rss-content');
  const subtitleBox = byId('rss-subtitle');
  const imageBox = byId('rss-image');
  const params = new URLSearchParams(window.location.search);
  const titulo = params.get('titulo') || 'Sem titulo';
  const fonte = params.get('fonte') || 'Fonte desconhecida';
  const data = params.get('data') || 'Data nao informada';
  const resumo = params.get('resumo') || '';
  const link = params.get('url') || '#';

  byId('rss-title').textContent = titulo;
  byId('rss-source').textContent = fonte;
  byId('rss-date').textContent = data;
  contentBox.innerHTML = normalizeResumo(resumo);
  byId('original-link').href = link;

  if (!link || link === '#') {
    loading.style.display = 'none';
    return;
  }

  fetch(`/api/extract?url=${encodeURIComponent(link)}`)
    .then(async (response) => {
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || 'Falha ao extrair materia completa.');
      }
      return data;
    })
    .then((payload) => {
      if (payload.sucesso) {
        if (payload.titulo) {
          byId('rss-title').textContent = payload.titulo;
        }

        if (payload.subtitulo) {
          subtitleBox.style.display = 'block';
          subtitleBox.textContent = payload.subtitulo;
        }

        if (payload.imagem) {
          imageBox.src = payload.imagem;
          imageBox.style.display = 'block';
        }

        if (payload.corpoHtml) {
          contentBox.innerHTML = payload.corpoHtml;
        }
      }
      loading.style.display = 'none';
    })
    .catch((error) => {
      loading.style.display = 'none';
      errorBox.style.display = 'block';
      errorBox.textContent = `${error.message} Exibindo resumo RSS.`;
    });
}

setContent();
