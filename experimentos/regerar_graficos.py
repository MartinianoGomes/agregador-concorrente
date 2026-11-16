"""Regenera todos os gráficos (PNG, 300 dpi) a partir dos JSONs já gravados em
`resultados/`, sem executar os experimentos de novo.

    python -m experimentos.regerar_graficos
"""

from __future__ import annotations

import json

from experimentos import _comum as c
from experimentos import exp_3_latencia, exp_4_multiplos_clientes, exp_5_indisponibilidade, plot_comparativo


def _ler(nome: str) -> dict:
    return json.loads((c.RESULTADOS / f"{nome}.json").read_text(encoding="utf-8"))


def main() -> None:
    plot_comparativo.main()

    d3 = _ler("exp_3_latencia")
    lat = d3["latencias_ms"]
    exp_3_latencia.graficos(lat, {l: d3["resultados"][str(l)]["estatisticas"] for l in lat})

    d4 = _ler("exp_4_multiplos_clientes")
    exp_4_multiplos_clientes.graficos(d4["clientes"], {int(k): v for k, v in d4["resumo"].items()})

    exp_5_indisponibilidade.graficos(_ler("exp_5_indisponibilidade")["resultados"])


if __name__ == "__main__":
    main()
