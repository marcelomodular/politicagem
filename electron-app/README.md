# Politicagem Electron

Versao desktop (Electron) do projeto Politicagem, com agregacao RSS e visualizador de materia.

## Requisitos

- Node.js 20+
- npm

## Rodando localmente

```bash
cd electron-app
npm install
npm start
```

## Recursos

- Capa com agregacao RSS de multiplas fontes
- Busca por palavra-chave
- Abertura de noticia em nova janela
- Visualizacao com titulo, subtitulo, imagem e corpo da materia
- Gestao de canais RSS (adicionar/remover)

## Estrutura

- `src/main.js`: processo principal Electron
- `src/server`: API local (news/channels/extract)
- `src/public`: interface da capa e visualizador
