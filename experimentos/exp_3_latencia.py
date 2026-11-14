"""Experimento 3 — Simulação de latência.

Sobe os postos com `--latencia-ms 500` (e outros valores) e compara os tempos
sequencial × concorrente. Este é o experimento que mais evidencia o ganho
da concorrência.

TODO (João Paulo):
  - Automatizar o start/stop dos postos com subprocess, variando `--latencia-ms`.
  - Varrer latências em [0, 100, 250, 500, 1000, 2000] ms.
  - Plotar curvas (tempo_total × latencia_posto) para as duas estratégias.
"""

from __future__ import annotations

print(__doc__)
print("Ainda não implementado. Esqueleto pronto para o João Paulo preencher.")


def main() -> None:
    raise NotImplementedError("TODO: João Paulo")


if __name__ == "__main__":
    main()
