"""Roda os 5 experimentos em sequência e gera todos os gráficos.

    python -m experimentos.executar_todos
"""

from __future__ import annotations

import sys
import time

from experimentos import (
    exp_1_sequencial, exp_2_concorrente, exp_3_latencia,
    exp_4_multiplos_clientes, exp_5_indisponibilidade, plot_comparativo,
)

ETAPAS = (
    ("Experimento 1", exp_1_sequencial.main),
    ("Experimento 2", exp_2_concorrente.main),
    ("Comparativo 1 × 2", plot_comparativo.main),
    ("Experimento 3", exp_3_latencia.main),
    ("Experimento 4", exp_4_multiplos_clientes.main),
    ("Experimento 5", exp_5_indisponibilidade.main),
)


def main() -> None:
    argv0 = sys.argv[:]
    sys.argv = sys.argv[:1]  # cada experimento usa seus próprios padrões
    try:
        for nome, fn in ETAPAS:
            print(f"\n{'=' * 70}\n{nome}\n{'=' * 70}")
            t0 = time.perf_counter()
            fn()
            print(f"({nome} concluído em {time.perf_counter() - t0:.0f} s)")
    finally:
        sys.argv = argv0


if __name__ == "__main__":
    main()
