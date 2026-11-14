"""Experimento 1 — Consulta sequencial.

Executa N consultas em modo sequencial para uma mesma (cidade, combustível)
e grava os tempos em resultados/exp_1_sequencial.json.

TODO (João Paulo):
  - Parametrizar cidade e combustível via argparse.
  - Rodar múltiplas iterações e salvar média / desvio padrão.
  - Gerar gráfico comparativo com exp_2_concorrente.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from src.cliente import consultar
from src.protocolo import ESTRATEGIA_SEQUENCIAL

AGREGADOR_HOST = "localhost"
AGREGADOR_PORTA = 5000
CIDADE = "Belém"
COMBUSTIVEL = "gasolina_comum"
N_RODADAS = 10


def main() -> None:
    tempos: list[float] = []
    for i in range(N_RODADAS):
        resp = consultar(AGREGADOR_HOST, AGREGADOR_PORTA, CIDADE, COMBUSTIVEL, ESTRATEGIA_SEQUENCIAL)
        tempos.append(resp.get("tempo_ms", 0.0))
        print(f"rodada {i + 1}: {resp.get('tempo_ms')} ms")

    saida = Path("resultados") / "exp_1_sequencial.json"
    saida.parent.mkdir(exist_ok=True)
    saida.write_text(json.dumps({
        "experimento": "exp_1_sequencial",
        "cidade": CIDADE,
        "combustivel": COMBUSTIVEL,
        "n_rodadas": N_RODADAS,
        "tempos_ms": tempos,
        "media_ms": sum(tempos) / len(tempos) if tempos else 0,
        "timestamp": int(time.time()),
    }, indent=2))
    print(f"\n→ Resultados salvos em {saida}")


if __name__ == "__main__":
    main()
