function byId(id) {
  return document.getElementById(id);
}

function escapeHtml(value = '') {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

async function loadArticle() {
  const params = new URLSearchParams(window.location.search);
  const url = params.get('url') || '';
  const titulo = params.get('titulo') || 'Sem titulo';
  const fonte = params.get('fonte') || 'Fonte desconhecida';

  byId('viewer-title').textContent = titulo;
  byId('viewer-source').textContent = fonte;
  byId('original-link').href = url;

  if (!url) {
    byId('loading').style.display = 'none';
    byId('error').style.display = 'block';
    byId('error').textContent = 'URL da materia nao informada.';
    return;
  }

  try {
    const response = await fetch(`/api/extract?url=${encodeURIComponent(url)}`);
    const data = await response.json();

    if (!response.ok || !data.sucesso) {
      throw new Error(data.error || 'Falha na extracao.');
    }

    byId('loading').style.display = 'none';
    const content = byId('content');
    content.style.display = 'block';
    content.innerHTML = `<h3>${escapeHtml(data.titulo || titulo)}</h3>${data.conteudo}`;

    if (data.imagem) {
      const img = byId('article-image');
      img.src = data.imagem;
      img.style.display = 'block';
    }
  } catch (error) {
    byId('loading').style.display = 'none';
    byId('error').style.display = 'block';
    byId('error').textContent = `Nao foi possivel extrair o conteudo: ${error.message}`;
  }
}

loadArticle();
