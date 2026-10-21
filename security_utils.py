import ipaddress
import socket
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse


def parse_published_date(raw_value):
    if not raw_value:
        return None

    text = str(raw_value).strip()
    if not text:
        return None

    parsers = [
        lambda value: parsedate_to_datetime(value),
    ]

    def parse_iso(value):
        normalized = value.replace('Z', '+00:00')
        return datetime.fromisoformat(normalized)

    parsers.append(parse_iso)

    known_formats = [
        '%Y-%m-%d %H:%M:%S',
        '%d/%m/%Y %H:%M',
        '%d/%m/%Y',
        '%Y-%m-%d',
    ]

    for date_format in known_formats:
        parsers.append(lambda value, fmt=date_format: datetime.strptime(value, fmt))

    try:
        from dateutil import parser as date_parser

        parsers.append(lambda value: date_parser.parse(value))
    except Exception:
        pass

    for parser in parsers:
        try:
            parsed = parser(text)
            if not parsed:
                continue
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except Exception:
            continue

    return None


def is_safe_embed_url(url):
    """
    URLs seguras para embutir em iframe/anchor do visualizador.

    Diferente de is_public_http_url, aqui nao resolvemos DNS: a URL pode
    ser de um veiculo temporariamente inacessivel, mas o ponto e bloquear
    esquemas executaveis (javascript:, data:, vbscript:) e credenciais embutidas.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme.lower() not in {'http', 'https'}:
        return False
    if not parsed.hostname:
        return False
    if parsed.username or parsed.password:
        return False

    return True


def is_public_http_url(url, resolver=socket.getaddrinfo):
    try:
        parsed = urlparse(url)
    except Exception:
        return False

    if parsed.scheme not in {'http', 'https'}:
        return False
    if not parsed.hostname:
        return False
    if parsed.username or parsed.password:
        return False
    if parsed.hostname.lower() == 'localhost':
        return False

    try:
        port = parsed.port or (443 if parsed.scheme == 'https' else 80)
    except ValueError:
        return False

    try:
        addresses = resolver(parsed.hostname, port, proto=socket.IPPROTO_TCP)
    except Exception:
        return False

    if not addresses:
        return False

    for _, _, _, _, sockaddr in addresses:
        host_ip = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(host_ip)
        except ValueError:
            return False

        if (
            ip_obj.is_private
            or ip_obj.is_loopback
            or ip_obj.is_link_local
            or ip_obj.is_multicast
            or ip_obj.is_reserved
            or ip_obj.is_unspecified
        ):
            return False

    return True
