"""Script auxiliar: fatia o CSV bruto da ANP em 4 recortes (um por posto).

Fluxo:
1. Lê `data/anp_bruto.csv` (CSV da série histórica semanal da ANP).
2. Filtra pelos estados da Região Norte (AC, AM, AP, PA, RO, RR, TO).
3. Divide as linhas em 4 subconjuntos distintos (um por rede: A, B, C, D).
4. Grava `data/anp_posto_a.csv`, `..._b.csv`, `..._c.csv`, `..._d.csv`.

TODO (Gustavo): adaptar após verificar o layout real do CSV.
  - Confirmar nome das colunas (podem variar entre semestres).
  - Decidir o critério de particionamento: aleatório, por município, por
    razão social (bandeira), etc.
  - Validar que cada arquivo tenha pelo menos as 4 principais capitais.

Uso:
    python scripts/preparar_csvs.py --entrada data/anp_bruto.csv --saida data/
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ESTADOS_NORTE = {"AC", "AM", "AP", "PA", "RO", "RR", "TO"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fatia o CSV bruto da ANP em recortes por posto.")
    parser.add_argument("--entrada", type=Path, required=True)
    parser.add_argument("--saida", type=Path, required=True, help="Diretório de saída.")
    parser.add_argument("--n-postos", type=int, default=4)
    parser.add_argument(
        "--separador",
        default=";",
        help="Separador de colunas do CSV (ANP usa ';' por padrão).",
    )
    args = parser.parse_args()

    args.saida.mkdir(parents=True, exist_ok=True)

    # TODO: trocar nome das colunas de Estado/Município/Produto/Valor quando
    # confirmado o layout real do CSV.
    with args.entrada.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f, delimiter=args.separador)
        colunas_originais = reader.fieldnames or []
        linhas_norte = [row for row in reader if row.get("Estado - Sigla", "").strip() in ESTADOS_NORTE]

    print(f"Linhas totais da Região Norte: {len(linhas_norte)}")

    # Particionamento simples: cada posto fica com uma fatia do arquivo.
    # TODO: trocar por particionamento por bandeira (razão social) se preferirem.
    nomes = ["a", "b", "c", "d"][: args.n_postos]
    for i, nome in enumerate(nomes):
        fatia = [row for j, row in enumerate(linhas_norte) if j % args.n_postos == i]
        saida = args.saida / f"anp_posto_{nome}.csv"
        with saida.open("w", encoding="utf-8", newline="") as out:
            writer = csv.DictWriter(out, fieldnames=colunas_originais, delimiter=args.separador)
            writer.writeheader()
            writer.writerows(fatia)
        print(f"  {saida} — {len(fatia)} linhas")


if __name__ == "__main__":
    main()
