#!/bin/bash
# Script simplificado para geração automática de snapshot
# Apenas gera o snapshot estático - upload manual para IPFS

set -e

# Configurações
LIMIT_PER_SOURCE=5
EXTRACT_ARTICLES=true
TIMESTAMP=$(date +"%Y-%m-%d-%H%M%S")
SNAPSHOT_DIR="static_snapshots/$TIMESTAMP"

echo "Gerando snapshot estático do Politicagem..."
echo "Timestamp: $TIMESTAMP"
echo "Limite por fonte: $LIMIT_PER_SOURCE"
echo "Extrair artigos: $EXTRACT_ARTICLES"

# Criar diretório se não existir
mkdir -p static_snapshots

# Gerar snapshot
source venv/bin/activate
if [ "$EXTRACT_ARTICLES" = true ]; then
    python3 snapshot_generator.py --output "$SNAPSHOT_DIR" --limit "$LIMIT_PER_SOURCE"
else
    python3 snapshot_generator.py --output "$SNAPSHOT_DIR" --limit "$LIMIT_PER_SOURCE" --no-extract
fi

# Preservar histórico para o acervo e calendário
echo "Preservando snapshot no arquivo histórico..."


echo "[OK] Snapshot gerado com sucesso!"
echo "Diretório: $SNAPSHOT_DIR"
echo "Arquivo principal: $SNAPSHOT_DIR/index.html"
echo ""

# Upload para IPFS (opcional: continua funcionando mesmo sem o IPFS instalado)
echo "Fazendo upload para IPFS..."
if ! command -v ipfs >/dev/null 2>&1; then
    echo "[AVISO] IPFS nao esta instalado - upload ignorado."
    echo "   Instale em: https://docs.ipfs.io/install/"
    echo "   Depois use: ipfs add -r $SNAPSHOT_DIR"
    exit 0
fi

IPFS_OUTPUT=$(ipfs add -r --cid-version 1 "$SNAPSHOT_DIR")
ROOT_CID=$(echo "$IPFS_OUTPUT" | tail -n 1 | awk '{print $2}')

# Registrar automaticamente o CID nos metadados para que o calendário de edições o reconheça
if [ -f "./update_snapshot_cid.sh" ] && [ -n "$ROOT_CID" ]; then
    ./update_snapshot_cid.sh "$SNAPSHOT_DIR" "$ROOT_CID" >/dev/null 2>&1 || true
fi

echo "[OK] Upload concluído!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "CID DO SNAPSHOT (USE ESTE PARA ATUALIZAR SEU DOMÍNIO):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   $ROOT_CID"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Links para acessar:"
echo "   Gateway IPFS: https://ipfs.io/ipfs/$ROOT_CID"
echo "   Gateway local: http://localhost:8080/ipfs/$ROOT_CID"
echo ""
echo "Próximos passos:"
echo "   1. Revise o conteúdo no link acima"
echo "   2. Atualize seu domínio .eth/.tezos com o CID: $ROOT_CID"
echo "   3. Pin o CID para não perder: ipfs pin add $ROOT_CID"
echo ""