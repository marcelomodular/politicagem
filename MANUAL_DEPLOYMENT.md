# Deployment Manual do Politicagem para IPFS

## Geração Automática de Snapshot

O snapshot estático é gerado automaticamente pelo script:

```bash
./generate_snapshot.sh
```

Ou manualmente:
```bash
python3 snapshot_generator.py --output static_snapshots/2026-09-02-120000 --limit 5
```

**Opções:**
- `--limit N`: Limite de notícias por fonte (default: 5)
- `--no-extract`: Não extrair conteúdo dos artigos (gera apenas index.html)

**O que é gerado:**
- `index.html`: Página principal com todas as notícias
- `visualizar/artigo-X.html`: Páginas estáticas individuais para cada artigo
- `snapshot_metadata.json`: Metadata do snapshot

## Upload Manual para IPFS

### 1. Iniciar daemon IPFS
```bash
ipfs daemon
```

### 2. Upload do snapshot
```bash
cd static_snapshots/2026-09-02-120000
ipfs add -r .
```

Você receberá um CID como: `QmXyZ...`

### 3. Fazer pin local (opcional mas recomendado)
```bash
ipfs pin add QmXyZ...
```

### 4. Verificar no gateway
Acesse: `https://ipfs.io/ipfs/QmXyZ...`

## Atualização Manual de Domínios Descentralizados

PARTE 1: P2P Direto no Browser (WebRTC-Direct + WebTransport)

O navegador precisa conseguir estabelecer handshake UDP diretamente com a sua máquina, ou via relay com AutoTLS.

1. Configurar listeners de Swarm no Kubo

Adicione suporte a WebRTC-Direct, WebTransport e WebSocket seguro no seu Kubo:

bash
ipfs config --json Addresses.Swarm '[
  "/ip4/0.0.0.0/tcp/4001",
  "/ip4/0.0.0.0/udp/4001/quic-v1",
  "/ip4/0.0.0.0/udp/4001/quic-v1/webtransport",
  "/ip4/0.0.0.0/udp/4001/webrtc-direct",
  "/ip6/::/tcp/4001",
  "/ip6/::/udp/4001/quic-v1",
  "/ip6/::/udp/4001/quic-v1/webtransport",
  "/ip6/::/udp/4001/webrtc-direct",
  "/ip4/0.0.0.0/tcp/4002/ws",
  "/ip6/::/tcp/4002/ws"
]'
2. Liberar portas no Firewall e Roteador (Crucial para resolver o timeout)

No diagnóstico inicial, o endereço WebRTC era IPv6 e deu timeout (peerconnection opening timed out). O WebRTC e o WebTransport operam em UDP:

No roteador / Firewall local (UFW / iptables):
bash
# Se usar UFW:
sudo ufw allow 4001/udp comment 'IPFS Swarm (QUIC/WebTransport/WebRTC)'
sudo ufw allow 4001/tcp comment 'IPFS Swarm (TCP)'
sudo ufw allow 4002/tcp comment 'IPFS WebSocket'
No roteador (NAT / Port Forwarding para IPv4):
Redirecione a porta 4001 (UDP e TCP) para o IP local da sua máquina.
No roteador (IPv6 Firewall):
Garanta que o firewall de entrada IPv6 não esteja descartando pacotes UDP na porta 4001 para o endereço do host (2804:2664:...).
3. Habilitar AutoTLS e Relay Nativo (Kubo 0.26+)

Para que conexões WebSocket tenham certificado TLS público válido (*.libp2p.direct gerado automaticamente):

bash
ipfs config --json AutoTLS.Enabled true
PARTE 2: Trustless HTTP Gateway com CORS

Este caminho permite que qualquer aplicação web (via fetch ou Helia HTTP retriever) baixe blocos e dados via HTTP/HTTPS sem restrições de browser.

1. Ativar Gateway e CORS no Kubo
bash
# 1. Escutar na porta 8080 (em todas as interfaces ou localmente)
ipfs config Addresses.Gateway "/ip4/0.0.0.0/tcp/8080"
# 2. Habilitar cabeçalhos CORS no Gateway
ipfs config --json Gateway.HTTPHeaders.Access-Control-Allow-Origin '["*"]'
ipfs config --json Gateway.HTTPHeaders.Access-Control-Allow-Methods '["GET", "HEAD", "OPTIONS"]'
ipfs config --json Gateway.HTTPHeaders.Access-Control-Allow-Headers '["Content-Type", "Range", "User-Agent", "X-Requested-With"]'
# 3. Habilitar suporte a Trustless Gateway (caso não esteja no default)
ipfs config --json Gateway.PublicGateways '{
  "localhost": {
    "UseSubdomains": false,
    "Paths": ["/ipfs", "/ipns"]
  }
}'
2. Expor com HTTPS (Obrigatório para browsers em produção)

Como browsers modernos bloqueiam requisições HTTP puro vindas de páginas HTTPS (Mixed Content), você precisará de HTTPS no seu gateway.

Opção Caddy (mais simples, gera SSL automático):
caddy
ipfs.seu-dominio.com {
    reverse_proxy localhost:8080
}
Opção Nginx:
nginx
server {
    server_name ipfs.seu-dominio.com;
    listen 443 ssl;
    # certificados ssl aqui...
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
    }
}
Ou Cloudflare Tunnel: Se você estiver em rede doméstica sem IP público estático/portas 80/443 abertas, pode rodar o cloudflared apontando para http://localhost:8080.
Reiniciando o daemon

Após aplicar as alterações no arquivo de configuração do Kubo:

bash
# Reinicie o daemon para carregar a nova configuração:
ipfs daemon

Para testar se os anúncios multiaddr do seu nó já estão propagando os protocolos WebRTC e WebTransport corretamente:

bash
ipfs id | grep -E "webrtc|webtransport"

(Se o seu daemon estiver rodando como serviço do sistema, em Docker ou com uma variável IPFS_PATH customizada, ajuste o comando ipfs config passando o -c /caminho/do/repo correspondente).

### Para domínio .eth (ENS)

#### Opção 1: Via ENS Manager (Web)
1. Acesse https://manager.ens.domains/
2. Conecte sua carteira Ethereum
3. Selecione seu domínio .eth
4. Vá em "Records" → "Content Hash"
5. Cole o CID no formato: `ipfs://QmXyZ...`
6. Confirme a transação (paga gas em ETH)

#### Opção 2: Via CLI (avançado)
```bash
# Exemplo conceitual - requer configuração web3.py
# Não implementado por segurança
```

### Para domínio .tezos

#### Via Tezos Domains (Web)
1. Acesse https://tezos.domains/
2. Conecte sua carteira Tezos
3. Selecione seu domínio .tezos
4. Edite o registro IPFS
5. Cole o CID no formato: `ipfs://QmXyZ...`
6. Confirme a operação (paga gas em XTZ)

## Agendamento Automático (Cron)

Para gerar snapshots automaticamente a cada 24h:

```bash
# Adicionar ao crontab
crontab -e

# Linha para executar à meia-noite todos os dias
0 0 * * * cd /home/mnlm/Público/politicagem && ./generate_snapshot.sh >> snapshots.log 2>&1
```

## Verificação

### 1. Verificar snapshot gerado
```bash
ls -la static_snapshots/
cat static_snapshots/último/snapshot_metadata.json
```

### 2. Verificar upload IPFS
```bash
ipfs ls QmXyZ...
ipfs cat QmXyZ.../index.html
```

### 3. Verificar domínio
```bash
# Para ENS
dig +short TXT _ens.seudominio.eth

# Acesse no navegador
https://seudominio.eth
```

## Segurança

- Nunca commit chaves privadas
- Use variáveis de ambiente para credenciais
- Revise o conteúdo antes do upload
- Teste em ambiente de desenvolvimento primeiro
- Mantenha backup dos snapshots importantes

## Troubleshooting

### Snapshot não gera
- Verifique dependências: `pip install -r requirements.txt`
- Verifique conexão com fontes RSS
- Verifique permissões de escrita

### Upload IPFS falha
- Verifique se daemon está rodando: `ipfs swarm peers`
- Verifique espaço em disco
- Verifique conectividade de rede

### Domínio não atualiza
- Verifique saldo de gas (ETH/XTZ)
- Verifique se você é o owner do domínio
- Verifique se a transação foi confirmada na blockchain
