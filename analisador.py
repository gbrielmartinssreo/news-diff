"""
analisador.py — Agrupa notícias similares e identifica as mais republicadas
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set

from coletor import Noticia
from lcs import similarity

LIMIAR_SIMILARIDADE = 0.35
STOPWORDS = {
    "de",
    "da",
    "do",
    "das",
    "dos",
    "em",
    "no",
    "na",
    "nos",
    "nas",
    "um",
    "uma",
    "uns",
    "umas",
    "o",
    "a",
    "os",
    "as",
    "e",
    "é",
    "que",
    "se",
    "com",
    "por",
    "para",
    "ao",
    "aos",
    "à",
    "às",
    "ou",
    "mas",
    "como",
    "mais",
    "seu",
    "sua",
    "seus",
    "suas",
    "este",
    "esta",
    "isso",
    "ele",
    "ela",
    "eles",
    "elas",
    "não",
    "foi",
    "são",
    "ser",
    "ter",
}

# Prefixos de títulos que são templates editoriais do G1, não notícias reais
_PREFIXOS_TEMPLATE = (
    "vídeos:",
    "videos:",
    "assista aos telejornais",
)

_SUFIXOS_TEMPLATE = (
    "assista aos telejornais",
    "ao vivo: assista aos telejornais",
)


class Cores:
    BOLD = "\033[1m"
    GRAY = "\033[90m"
    GREEN = "\033[92m"
    RESET = "\033[0m"


def _e_template_editorial(titulo: str) -> bool:
    """Retorna True para títulos que são templates do G1 (telejornais, playlists de vídeo)."""
    t = titulo.strip().lower()
    return any(t.startswith(p) for p in _PREFIXOS_TEMPLATE) or any(
        t.endswith(p) for p in _SUFIXOS_TEMPLATE
    )


def palavras_chave(texto: str) -> List[str]:
    if not texto:
        return []
    texto_limpo = re.sub(r"[^\w\s]", " ", texto.lower())
    palavras = [p for p in texto_limpo.split() if len(p) > 3 and p not in STOPWORDS]
    return sorted(set(palavras))


@dataclass
class Grupo:
    noticias: List[Noticia] = field(default_factory=list)

    @property
    def representante(self) -> Noticia:
        # Primeiro elemento adicionado ao grupo — fixo, evita drift de cluster
        return self.noticias[0]

    @property
    def portais(self) -> List[str]:
        vistos: Set[str] = set()
        portais_unicos = []
        for n in self.noticias:
            if n.portal not in vistos:
                vistos.add(n.portal)
                portais_unicos.append(n.portal)
        return portais_unicos

    @property
    def titulo(self) -> str:
        return self.representante.titulo

    @property
    def tamanho(self) -> int:
        return len(self.noticias)


def agrupar(
    noticias: List[Noticia],
    limiar: float = LIMIAR_SIMILARIDADE,
) -> List[Grupo]:
    if not noticias:
        return []

    # Deduplica por URL antes de qualquer processamento
    vistas: Set[str] = set()
    unicas = []
    for n in noticias:
        if n.url and n.url not in vistas:
            vistas.add(n.url)
            unicas.append(n)
        elif not n.url:
            unicas.append(n)
    duplicadas = len(noticias) - len(unicas)
    noticias = unicas

    # Remove templates editoriais
    total_antes = len(noticias)
    noticias = [n for n in noticias if not _e_template_editorial(n.titulo)]
    descartadas = total_antes - len(noticias)

    grupos: List[Grupo] = []
    stats = {
        "lcs_chamadas": 0,
        "pre_filtro_bloqueados": 0,
        "comparacoes_totais": 0,
        "duplicadas_url": duplicadas,
        "templates_descartados": descartadas,
    }
    cache: Dict[int, List[str]] = {}

    for noticia in noticias:
        if id(noticia) not in cache:
            cache[id(noticia)] = palavras_chave(noticia.titulo)
        chaves_noticia = cache[id(noticia)]

        encontrou = False

        for grupo in grupos:
            rep = grupo.representante
            if id(rep) not in cache:
                cache[id(rep)] = palavras_chave(rep.titulo)
            chaves_rep = cache[id(rep)]

            interseccao = len(set(chaves_noticia) & set(chaves_rep))
            stats["comparacoes_totais"] += 1

            if interseccao < 2:
                stats["pre_filtro_bloqueados"] += 1
                continue

            stats["lcs_chamadas"] += 1
            sim = similarity(chaves_noticia, chaves_rep, ja_processado=True)

            if sim >= limiar:
                grupo.noticias.append(noticia)
                encontrou = True
                break

        if not encontrou:
            grupos.append(Grupo(noticias=[noticia]))

    grupos.sort(key=lambda g: g.tamanho, reverse=True)

    # Imprime estatísticas de processamento
    linhas = []
    if stats["duplicadas_url"]:
        linhas.append(f"  URLs duplicadas removidas: {stats['duplicadas_url']}")
    if stats["templates_descartados"]:
        linhas.append(
            f"  Templates editoriais descartados: {stats['templates_descartados']}"
        )
    linhas.append(f"  Pré-filtro bloqueou {stats['pre_filtro_bloqueados']} comparações")
    linhas.append(f"  LCS executado {stats['lcs_chamadas']} vezes")
    linhas.append(f"  Total de comparações: {stats['comparacoes_totais']}")
    print(Cores.GRAY + "\n".join(linhas) + Cores.RESET + "\n")

    return grupos


def imprimir_ranking(grupos: List[Grupo], top: int = 10) -> None:
    print(f"\n{Cores.BOLD}{'═' * 60}{Cores.RESET}")
    print(f"{Cores.BOLD}  NOTÍCIAS DO MOMENTO — TOP {top}{Cores.RESET}")
    print(f"{'═' * 60}\n")

    if not grupos:
        print("  Nenhuma notícia encontrada.\n")
        return

    grupos_com_repeticao = [g for g in grupos if g.tamanho > 1]
    exibir = grupos_com_repeticao[:top]

    if not exibir:
        print("  Nenhuma notícia republicada encontrada no período.\n")
        return

    for i, grupo in enumerate(exibir, 1):
        portais_str = ", ".join(grupo.portais)
        print(f"{Cores.BOLD}{i:>2}. {grupo.titulo}{Cores.RESET}")
        print(
            f"    {Cores.GREEN}Republicada {grupo.tamanho}x{Cores.RESET}  "
            f"{Cores.GRAY}({portais_str}){Cores.RESET}"
        )
        print(f"    {Cores.GRAY}{grupo.representante.url}{Cores.RESET}")
        print(f"    {Cores.GRAY}Títulos por portal (amostra):{Cores.RESET}")
        for n in grupo.noticias[:3]:
            print(f"      • {n.portal} — {n.titulo}")
        if grupo.tamanho > 3:
            print(
                f"      • {Cores.GRAY}... e mais {grupo.tamanho - 3} ocorrências{Cores.RESET}"
            )
        print()

    total_noticias = sum(g.tamanho for g in grupos)
    total_copias = sum(g.tamanho - 1 for g in grupos_com_repeticao)
    topicos_unicos = len(grupos) - len(grupos_com_repeticao)
    print(
        f"{Cores.GRAY}{total_noticias} notícias coletadas · "
        f"{topicos_unicos} tópicos únicos · "
        f"{total_copias} repetições de tópicos{Cores.RESET}\n"
    )
