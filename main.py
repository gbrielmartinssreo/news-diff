"""
main.py — Interface interativa do News Diff
"""

import sys

_BOLD = "\033[1m"
_CYAN = "\033[96m"
_GRAY = "\033[90m"
_RESET = "\033[0m"


def perguntar_int(prompt: str, padrao: int, minimo: int = 1) -> int:
    entrada = input(prompt).strip()
    if not entrada:
        return padrao
    try:
        valor = int(entrada)
        if valor < minimo:
            print(f"  Valor mínimo é {minimo}. Usando {padrao}.")
            return padrao
        return valor
    except ValueError:
        print(f"  Entrada inválida. Usando {padrao}.")
        return padrao


def menu_principal() -> dict:
    print(f"\n{_BOLD}{'═' * 60}{_RESET}")
    print(f"{_BOLD}  NEWS DIFF{_RESET}")
    print(f"{'═' * 60}\n")
    print(f"  {_CYAN}1.{_RESET} Coletar notícias agora")
    print(f"  {_CYAN}2.{_RESET} Usar snapshot salvo (offline)")
    print(f"  {_CYAN}3.{_RESET} Coletar e salvar snapshot")
    print(f"\n  {_GRAY}0. Sair{_RESET}\n")

    escolha = input("  Escolha uma opção: ").strip()

    if escolha == "0":
        print("  Saindo.\n")
        sys.exit(0)

    if escolha not in ("1", "2", "3"):
        print("  Opção inválida.")
        return menu_principal()

    config = {
        "offline_db": None,
        "download_db": None,
        "only_extra": False,
        "horas": 5,
        "top": 10,
    }

    if escolha == "2":
        arquivo = input("  Caminho do snapshot JSON: ").strip()
        if not arquivo:
            print("  Caminho não informado.")
            return menu_principal()
        config["offline_db"] = arquivo

    elif escolha == "3":
        arquivo = input("  Nome do arquivo para salvar (ex: snap.json): ").strip()
        if not arquivo:
            print("  Nome não informado.")
            return menu_principal()
        config["download_db"] = arquivo

    if escolha in ("1", "3"):
        config["horas"] = perguntar_int(
            f"  Janela de tempo em horas [{_GRAY}padrão 5{_RESET}]: ", padrao=5
        )

    config["top"] = perguntar_int(
        f"  Quantas notícias no ranking [{_GRAY}padrão 10{_RESET}]: ", padrao=10
    )

    return config


def main():
    config = menu_principal()

    from analisador import agrupar, imprimir_ranking
    from coletor import coletar

    print(f"\n{_BOLD}{'═' * 60}{_RESET}")
    print(f"{_BOLD}  NEWS DIFF — Notícias do Momento{_RESET}")
    print(f"{'═' * 60}")

    noticias = coletar(
        horas=config["horas"],
        offline_db=config["offline_db"],
        download_db=config["download_db"],
        only_extra=config["only_extra"],
    )

    if not noticias:
        print("Nenhuma notícia coletada. Verifique sua conexão ou o arquivo offline.")
        sys.exit(1)

    print(f"Agrupando {len(noticias)} notícias via LCS...")
    grupos = agrupar(noticias)
    imprimir_ranking(grupos, top=config["top"])


if __name__ == "__main__":
    main()
