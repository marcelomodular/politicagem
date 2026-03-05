const fs = require('fs/promises');
const path = require('path');
const defaultSources = require('./newsSources');

let filePath;

function normalizeUrl(url = '') {
  return String(url).trim();
}

function normalizeName(name = '') {
  return String(name).trim();
}

function asMap(sources) {
  return new Map(sources.map(([url, fonte]) => [normalizeUrl(url), normalizeName(fonte)]));
}

function getDefaultMap() {
  return asMap(defaultSources);
}

async function readConfig() {
  try {
    const raw = await fs.readFile(filePath, 'utf8');
    const parsed = JSON.parse(raw);
    return {
      custom: Array.isArray(parsed.custom) ? parsed.custom : [],
      disabled: Array.isArray(parsed.disabled) ? parsed.disabled : [],
    };
  } catch {
    return { custom: [], disabled: [] };
  }
}

async function writeConfig(config) {
  await fs.mkdir(path.dirname(filePath), { recursive: true });
  await fs.writeFile(filePath, JSON.stringify(config, null, 2), 'utf8');
}

async function initStore(dataDir) {
  filePath = path.join(dataDir, 'channels.json');
  const cfg = await readConfig();
  await writeConfig(cfg);
}

function isValidHttpUrl(url) {
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

async function getChannelList() {
  const cfg = await readConfig();
  const defaults = getDefaultMap();
  const disabled = new Set(cfg.disabled.map(normalizeUrl));

  const all = [];

  defaults.forEach((fonte, url) => {
    all.push({ url, fonte, custom: false, enabled: !disabled.has(url) });
  });

  for (const item of cfg.custom) {
    const url = normalizeUrl(item.url);
    const fonte = normalizeName(item.fonte);
    if (!url || !fonte) continue;
    if (defaults.has(url)) continue;
    all.push({ url, fonte, custom: true, enabled: !disabled.has(url) });
  }

  return all.sort((a, b) => a.fonte.localeCompare(b.fonte, 'pt-BR'));
}

async function getActiveSources() {
  const channels = await getChannelList();
  return channels.filter((c) => c.enabled).map((c) => [c.url, c.fonte]);
}

async function addChannel({ url, fonte }) {
  const cleanUrl = normalizeUrl(url);
  const cleanName = normalizeName(fonte);

  if (!isValidHttpUrl(cleanUrl)) {
    throw new Error('URL invalida. Use http:// ou https://');
  }

  if (!cleanName) {
    throw new Error('Nome do canal e obrigatorio.');
  }

  const cfg = await readConfig();
  const defaults = getDefaultMap();

  cfg.disabled = cfg.disabled.filter((u) => normalizeUrl(u) !== cleanUrl);

  if (!defaults.has(cleanUrl)) {
    const exists = cfg.custom.find((c) => normalizeUrl(c.url) === cleanUrl);
    if (exists) {
      exists.fonte = cleanName;
    } else {
      cfg.custom.push({ url: cleanUrl, fonte: cleanName });
    }
  }

  await writeConfig(cfg);
}

async function removeChannel(url) {
  const cleanUrl = normalizeUrl(url);
  if (!cleanUrl) {
    throw new Error('URL do canal e obrigatoria.');
  }

  const cfg = await readConfig();
  const defaults = getDefaultMap();

  if (defaults.has(cleanUrl)) {
    if (!cfg.disabled.some((u) => normalizeUrl(u) === cleanUrl)) {
      cfg.disabled.push(cleanUrl);
    }
  } else {
    cfg.custom = cfg.custom.filter((c) => normalizeUrl(c.url) !== cleanUrl);
    cfg.disabled = cfg.disabled.filter((u) => normalizeUrl(u) !== cleanUrl);
  }

  await writeConfig(cfg);
}

module.exports = {
  initStore,
  getChannelList,
  getActiveSources,
  addChannel,
  removeChannel,
};
