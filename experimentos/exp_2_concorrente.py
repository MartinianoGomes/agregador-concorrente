"""Experimento 2 — Consulta concorrente.

Mesmo formato do Experimento 1, em modo concorrente (uma thread por posto).
Gráficos comparativos 1 × 2: `python -m experimentos.plot_comparativo`.

    python -m experimentos.exp_2_concorrente [--rodadas 10] [--latencia-ms 0]
"""

from __future__ import annotations

from experimentos import _simples
from src.protocolo import ESTRATEGIA_CONCORRENTE


def main() -> None:
    _simples.executar(2, "exp_2_concorrente", ESTRATEGIA_CONCORRENTE)


if __name__ == "__main__":
    main()
