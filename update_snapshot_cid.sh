#!/bin/bash
# Script para atualizar o metadata do snapshot com o CID correto após upload IPFS

if [ -z "$1" ]; then
    echo "Uso: $0 <snapshot_dir> <ipfs_cid>"
    echo "Exemplo: $0 static_snapshots/2026-09-07-141559 QmdtRGChqC8pYjQuTD1ea5GyWm5n6udGRBwqfdJq4TatoP"
    exit 1
fi

SNAPSHOT_DIR="$1"
IPFS_CID="$2"

if [ ! -d "$SNAPSHOT_DIR" ]; then
    echo "❌ Erro: Diretório $SNAPSHOT_DIR não encontrado"
    exit 1
fi

METADATA_FILE="$SNAPSHOT_DIR/snapshot_metadata.json"

if [ ! -f "$METADATA_FILE" ]; then
    echo "❌ Erro: Arquivo $METADATA_FILE não encontrado"
    exit 1
fi

echo "📝 Atualizando metadata do snapshot..."
echo "📁 Diretório: $SNAPSHOT_DIR"
echo "🌐 CID: $IPFS_CID"

# Atualizar o metadata com o CID correto usando Python
python3 << EOF
import json
from pathlib import Path

metadata_file = Path("$METADATA_FILE")
with open(metadata_file, 'r', encoding='utf-8') as f:
    metadata = json.load(f)

metadata['correct_cid'] = "$IPFS_CID"
metadata['ipfs_gateway_url'] = f"https://ipfs.io/ipfs/$IPFS_CID"
metadata['local_gateway_url'] = f"http://localhost:8080/ipfs/$IPFS_CID"
metadata['cid_updated_at'] = json.dumps({"timestamp": "$(date -Iseconds)"})

with open(metadata_file, 'w', encoding='utf-8') as f:
    json.dump(metadata, f, indent=2, ensure_ascii=False)

print("✅ Metadata atualizado com sucesso!")
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🌐 CID REGISTRADO NO SNAPSHOT: $IPFS_CID"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Links:"
echo "   Gateway IPFS: https://ipfs.io/ipfs/$IPFS_CID"
echo "   Gateway local: http://localhost:8080/ipfs/$IPFS_CID"
echo ""
echo "💡 Dica: Faça upload novamente para IPFS para incluir o metadata atualizado:"
echo "   ipfs add -r $SNAPSHOT_DIR"
