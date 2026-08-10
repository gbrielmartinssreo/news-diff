"""
lcs.py — Núcleo do algoritmo LCS via Programação Dinâmica
"""

import re
from functools import lru_cache


def lcs_table(A: list, B: list) -> list:

    m, n = len(A), len(B)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(1, m + 1):
        a_i = A[i - 1]
        for j in range(1, n + 1):
            if a_i == B[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp


def backtrack(dp: list, A: list, B: list, i: int, j: int) -> list:
    common = []
    while i > 0 and j > 0:
        if A[i - 1] == B[j - 1]:
            common.append(A[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return list(reversed(common))


@lru_cache(maxsize=128)
def _preprocess_text(text: str) -> tuple:

    if not text:
        return ()
    clean = re.sub(r"[^\w\s]", " ", text.lower())
    return tuple(w for w in clean.split() if w)


def similarity(A, B, ja_processado: bool = False) -> float:

    if not ja_processado:
        A = _preprocess_text(A)
        B = _preprocess_text(B)

    if not A or not B:
        return 0.0

    dp = lcs_table(A, B)
    lcs_len = dp[len(A)][len(B)]

    return lcs_len / max(len(A), len(B), 1)
