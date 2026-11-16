"""Experimento 1 — Consulta sequencial.

Sobe 4 postos + agregador, executa N consultas em modo sequencial para uma
mesma (cidade, combustível) e grava os tempos em resultados/exp_1_sequencial.json.

    python -m experimentos.exp_1_sequencial [--rodadas 10] [--latencia-ms 0]
"""

from __future__ import annotations

from experimentos import _simples
from src.protocolo import ESTRATEGIA_SEQUENCIAL


def main() -> None:
    _simples.executar(1, "exp_1_sequencial", ESTRATEGIA_SEQUENCIAL)


if __name__ == "__main__":
    main()
