"""Roda os 5 experimentos em sequência e gera todos os gráficos.

    python -m experimentos.executar_todos [--estado PA] [--cidade Belém] [--combustivel gasolina_comum]

Os parâmetros de consulta são repassados a todos os experimentos. Se um
experimento falhar, os seguintes rodam mesmo assim; no fim aparece um resumo e,
se algo falhou, o processo termina com código 1.
"""

from __future__ import annotations

import sys
import time
import traceback

from experimentos import _comum as c
from experimentos import (
    exp_1_sequencial, exp_2_concorrente, exp_3_latencia,
    exp_4_multiplos_clientes, exp_5_indisponibilidade, plot_comparativo,
)

# (nome, função, recebe os parâmetros de consulta?)
ETAPAS = (
    ("Experimento 1", exp_1_sequencial.main, True),
    ("Experimento 2", exp_2_concorrente.main, True),
    ("Comparativo 1 × 2", plot_comparativo.main, False),
    ("Experimento 3", exp_3_latencia.main, True),
    ("Experimento 4", exp_4_multiplos_clientes.main, True),
    ("Experimento 5", exp_5_indisponibilidade.main, True),
)


def _executar(fn, argv: list[str]) -> str | None:
    """Roda `fn` com `argv` como linha de comando; devolve a mensagem de erro, se houver."""
    original = sys.argv
    sys.argv = [original[0], *argv]
    try:
        fn()
    except SystemExit as e:
        if e.code not in (None, 0):
            return str(e.code) if not isinstance(e.code, int) else f"saiu com código {e.code}"
    except Exception as e:  # noqa: BLE001 — registrar e seguir para o próximo experimento
        traceback.print_exc()
        return f"{type(e).__name__}: {e}"
    finally:
        sys.argv = original
    return None


def main() -> None:
    args = c.parser_base("Roda os 5 experimentos em sequência.").parse_args()
    consulta = ["--estado", args.estado, "--cidade", args.cidade, "--combustivel", args.combustivel]

    resumo = []
    inicio = time.perf_counter()
    for nome, fn, com_consulta in ETAPAS:
        print(f"\n{'=' * 70}\n{nome}\n{'=' * 70}")
        t0 = time.perf_counter()
        erro = _executar(fn, consulta if com_consulta else [])
        resumo.append((nome, time.perf_counter() - t0, erro))

    print(f"\n{'=' * 70}\nResumo ({args.cidade}/{args.estado}, {args.combustivel})\n{'=' * 70}")
    for nome, duracao, erro in resumo:
        print(f"  {'OK   ' if erro is None else 'FALHA'} {nome:<20} {duracao:6.0f} s"
              + (f"  — {erro.splitlines()[0]}" if erro else ""))
    print(f"  total: {time.perf_counter() - inicio:.0f} s")
    if any(erro for *_, erro in resumo):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
