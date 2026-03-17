"""
coletor.py — Coleta notícias de portais brasileiros via RSS
"""

import json
import os
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

PORTAIS_PADRAO: Dict[str, str] = {}

FORMATOS_DATA = [
    "%a, %d %b %Y %H:%M:%S %z",
    "%a, %d %b %Y %H:%M:%S GMT",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
]


@dataclass
class Noticia:
    titulo: str
    resumo: str
    portal: str
    url: str
    data: datetime

    def to_dict(self) -> dict:
        dados = asdict(self)
        dados["data"] = self.data.isoformat()
        return dados

    @staticmethod
    def from_dict(d: dict) -> "Noticia":
        dt = datetime.fromisoformat(d["data"])
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return Noticia(
            titulo=d.get("titulo", ""),
            resumo=d.get("resumo", ""),
            portal=d.get("portal", ""),
            url=d.get("url", ""),
            data=dt,
        )

    @property
    def texto(self) -> str:
        return f"{self.titulo}\n{self.resumo}"


def parse_data(raw: str) -> datetime:
    if not raw:
        return datetime.now(timezone.utc)

    raw = raw.strip()
    for sufixo in (
        " UT",
        " EST",
        " EDT",
        " PST",
        " PDT",
        " CST",
        " CDT",
        " MST",
        " MDT",
    ):
        raw = raw.replace(sufixo, " +0000")

    for fmt in FORMATOS_DATA:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return datetime.now(timezone.utc)


def limpar_html(texto: str) -> str:
    if not texto:
        return ""
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def load_portais_extra(arquivo: Optional[str] = None) -> Dict[str, str]:
    if arquivo is None:
        arquivo = os.path.join(os.path.dirname(__file__), "portais_extra.txt")

    portais = {}

    if not os.path.exists(arquivo):
        return portais

    try:
        with open(arquivo, encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                if "|" in linha:
                    nome, url = linha.split("|", 1)
                    portais[nome.strip()] = url.strip()
    except Exception:
        pass

    return portais


def salvar_json(caminho: str, noticias: List[Noticia]) -> None:
    try:
        dados = [n.to_dict() for n in noticias]
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        print(f"  [i] Salvas {len(noticias)} notícias em {caminho}")
    except Exception as e:
        print(f"  [!] Falha ao salvar {caminho}: {e}")


def carregar_json(caminho: str) -> List[Noticia]:
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        return [Noticia.from_dict(d) for d in dados]
    except FileNotFoundError:
        print(f"  [i] Arquivo {caminho} não encontrado")
        return []
    except Exception as e:
        print(f"  [!] Erro ao ler {caminho}: {e}")
        return []


def buscar_feed(portal: str, url: str, limite_dt: datetime) -> List[Noticia]:
    noticias = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            xml_bytes = resp.read()

        root = ET.fromstring(xml_bytes)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []

        for item in items:
            titulo_el = item.find("title")
            titulo = (
                titulo_el.text.strip()
                if titulo_el is not None and titulo_el.text
                else ""
            )

            if not titulo:
                continue

            resumo = ""
            desc = item.find("description")
            if desc is not None and desc.text:
                resumo = limpar_html(desc.text)

            url_noticia = ""
            link_el = item.find("link")
            if link_el is not None:
                url_noticia = link_el.text or link_el.get("href") or ""
                url_noticia = url_noticia.strip()

            data_raw = ""
            pubdate = item.find("pubDate")
            if pubdate is not None and pubdate.text:
                data_raw = pubdate.text

            data = parse_data(data_raw) if data_raw else datetime.now(timezone.utc)

            if data >= limite_dt:
                noticias.append(Noticia(titulo, resumo, portal, url_noticia, data))

    except Exception:
        pass

    return noticias


def coletar(
    horas: int = 5,
    offline_db: Optional[str] = None,
    download_db: Optional[str] = None,
    only_extra: bool = False,
) -> List[Noticia]:
    if offline_db:
        return carregar_json(offline_db)

    if only_extra:
        portais = load_portais_extra()
        if not portais:
            print("  [!] Nenhum portal extra encontrado")
            return []
    else:
        portais = PORTAIS_PADRAO.copy()
        portais.update(load_portais_extra())

    limite = datetime.now(timezone.utc) - timedelta(hours=horas)

    print(f"\nColetando notícias das últimas {horas}h...")
    print(f"Período: {limite.strftime('%d/%m %H:%M')} → agora\n")

    todas: List[Noticia] = []

    for portal, url in portais.items():
        print(f"  → {portal}...", end=" ", flush=True)
        noticias = buscar_feed(portal, url, limite)
        print(f"{len(noticias)} notícias")
        todas.extend(noticias)
        time.sleep(0.25)

    todas.sort(key=lambda n: n.data, reverse=True)
    print(f"\nTotal coletado: {len(todas)} notícias\n")

    if download_db:
        salvar_json(download_db, todas)

    return todas
