"""
Arquivo de snapshots do Politicagem.

Le o diretorio de snapshots estaticos e expoe os metadados de cada edicao
para que a interface possa montar uma linha do tempo (calendario) das
edicoes ja publicadas.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SNAPSHOTS_DIRNAME = "static_snapshots"
SLUG_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}$")
MONTHS_PT = [
    "Janeiro",
    "Fevereiro",
    "Marco",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def get_snapshots_dir(base_dir=None) -> Path:
    if base_dir:
        return Path(base_dir)
    return ROOT_DIR / SNAPSHOTS_DIRNAME


def _parse_slug(slug: str):
    """Converte '2026-10-20-164236' em datetime. Retorna None se invalido."""
    if not SLUG_PATTERN.match(slug):
        return None

    try:
        return datetime.strptime(slug, "%Y-%m-%d-%H%M%S")
    except ValueError:
        return None


def _read_metadata(snapshot_dir: Path) -> dict:
    metadata_path = snapshot_dir / "snapshot_metadata.json"
    if not metadata_path.is_file():
        return {}

    try:
        parsed = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

    return parsed if isinstance(parsed, dict) else {}


def _count_articles(snapshot_dir: Path) -> int:
    articles_dir = snapshot_dir / "visualizar"
    if not articles_dir.is_dir():
        return 0

    return sum(1 for item in articles_dir.iterdir() if item.suffix == ".html")


# CIDs do IPFS: base32 (Qm...) ou base36 (bafy...). O placeholder de
# "update_snapshot_cid.sh" nao casa com nenhum dos dois.
CID_PATTERN = re.compile(r"^(Qm[1-9A-HJ-NP-Za-km-z]{44}|b[a-z2-7]{58})$")


def _extract_cid(raw_value) -> str | None:
    """Retorna o CID apenas se ele tiver o formato valido de um CID do IPFS."""
    if not isinstance(raw_value, str):
        return None

    candidate = raw_value.strip()
    if not CID_PATTERN.match(candidate):
        return None

    return candidate


def format_label(moment: datetime) -> str:
    """'20 de Outubro de 2026, 16h42' - rotulo editorial em portugues."""
    if not moment:
        return "Data desconhecida"

    return (
        f"{moment.day} de {MONTHS_PT[moment.month - 1]} de {moment.year}, "
        f"{moment.hour:02d}h{moment.minute:02d}"
    )


def list_snapshots(base_dir=None) -> list:
    """
    Retorna as edicoes ja geradas, da mais recente para a mais antiga.

    Cada item traz: slug, data (datetime), rotulo formatado, contagem de
    noticias, contagem de artigos e o cid do IPFS quando ja foi registrado.
    """
    snapshots_dir = get_snapshots_dir(base_dir)
    if not snapshots_dir.is_dir():
        return []

    items = []

    for entry in sorted(snapshots_dir.iterdir(), reverse=True):
        if not entry.is_dir():
            continue

        moment = _parse_slug(entry.name)
        if not moment:
            continue

        metadata = _read_metadata(entry)
        articles = metadata.get("articles_generated")
        if not isinstance(articles, int):
            articles = _count_articles(entry)

        news_count = metadata.get("news_count")
        if not isinstance(news_count, int):
            news_count = 0

        cid = _extract_cid(metadata.get("correct_cid"))

        items.append(
            {
                "slug": entry.name,
                "data": moment,
                "rotulo": format_label(moment),
                "data_curta": moment.strftime("%d/%m/%Y"),
                "hora": moment.strftime("%H:%M"),
                "ano": moment.year,
                "mes": moment.month,
                "dia": moment.day,
                "data_iso": moment.strftime("%Y-%m-%d"),
                "noticias": news_count,
                "artigos": articles,
                "cid": cid,
                "tem_indice": (entry / "index.html").is_file(),
            }
        )

    return items


def build_calendar_data(snapshots: list) -> dict:
    """
    Agrupa os snapshots em formato propicio para montagem de calendario.
    Retorna mapa de datas ISO -> lista de edicoes, anos e meses disponiveis.
    """
    days_map: dict[str, list[dict]] = {}
    years_set: set[int] = set()
    months_by_year: dict[int, set[int]] = {}

    for item in snapshots:
        iso = item["data_iso"]
        if iso not in days_map:
            days_map[iso] = []
        days_map[iso].append(item)

        ano = item["ano"]
        mes = item["mes"]
        years_set.add(ano)
        if ano not in months_by_year:
            months_by_year[ano] = set()
        months_by_year[ano].add(mes)

    years_sorted = sorted(years_set, reverse=True)
    months_map_sorted = {
        ano: sorted(months_by_year[ano])
        for ano in years_sorted
    }

    latest_date = snapshots[0]["data_iso"] if snapshots else None

    return {
        "days_map": days_map,
        "years": years_sorted,
        "months_by_year": months_map_sorted,
        "latest_date": latest_date,
        "months_pt": MONTHS_PT,
    }


def resolve_snapshot_path(slug: str, base_dir=None) -> Path:
    """
    Resolve o diretorio de um snapshot garantindo que o slug nao escape do
    diretorio de snapshots (path traversal).
    """
    if not slug or not SLUG_PATTERN.match(slug):
        raise ValueError("Identificador de snapshot invalido.")

    snapshots_dir = get_snapshots_dir(base_dir).resolve()
    target = (snapshots_dir / slug).resolve()

    if snapshots_dir not in target.parents:
        raise ValueError("Identificador de snapshot invalido.")

    if not target.is_dir():
        raise FileNotFoundError("Snapshot nao encontrado.")

    return target


def resolve_snapshot_file(slug: str, relative_path: str = "index.html", base_dir=None) -> tuple[Path, str]:
    """
    Resolve com seguranca um arquivo interno de um snapshot (ex: index.html ou
    visualizar/artigo-1.html), prevenindo path traversal.
    Retorna a tupla (caminho_absoluto_diretorio, nome_arquivo_relativo).
    """
    snapshot_dir = resolve_snapshot_path(slug, base_dir)

    clean_rel = Path(relative_path).as_posix().lstrip("/")
    if not clean_rel:
        clean_rel = "index.html"

    target_file = (snapshot_dir / clean_rel).resolve()

    if target_file != snapshot_dir and snapshot_dir not in target_file.parents:
        raise ValueError("Acesso a arquivo fora do snapshot bloqueado.")

    if not target_file.is_file():
        raise FileNotFoundError("Arquivo nao encontrado no snapshot.")

    return snapshot_dir, clean_rel


def build_archive_payload(base_dir=None) -> dict:
    """Payload JSON com as edicoes e calendario, usado pela API e pela interface."""
    snapshots = list_snapshots(base_dir)
    calendar = build_calendar_data(snapshots)

    serializable_days_map = {
        date_iso: [
            {
                "slug": item["slug"],
                "rotulo": item["rotulo"],
                "data_curta": item["data_curta"],
                "hora": item["hora"],
                "ano": item["ano"],
                "mes": item["mes"],
                "dia": item["dia"],
                "data_iso": item["data_iso"],
                "noticias": item["noticias"],
                "artigos": item["artigos"],
                "cid": item["cid"],
                "tem_indice": item["tem_indice"],
            }
            for item in items
        ]
        for date_iso, items in calendar["days_map"].items()
    }

    return {
        "total": len(snapshots),
        "snapshots": [
            {
                "slug": item["slug"],
                "rotulo": item["rotulo"],
                "data_curta": item["data_curta"],
                "hora": item["hora"],
                "ano": item["ano"],
                "mes": item["mes"],
                "dia": item["dia"],
                "data_iso": item["data_iso"],
                "noticias": item["noticias"],
                "artigos": item["artigos"],
                "cid": item["cid"],
                "tem_indice": item["tem_indice"],
            }
            for item in snapshots
        ],
        "calendar": {
            "days_map": serializable_days_map,
            "years": calendar["years"],
            "months_by_year": calendar["months_by_year"],
            "latest_date": calendar["latest_date"],
            "months_pt": calendar["months_pt"],
        },
    }

