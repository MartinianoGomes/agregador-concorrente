"""Script auxiliar: fatia o CSV bruto da ANP em 4 recortes (um por posto).

Fluxo:
1. Lê `data/anp_bruto.csv` (CSV da série histórica semanal da ANP).
2. Filtra pelos estados da Região Norte (AC, AM, AP, PA, RO, RR, TO).
3. Divide as linhas em 4 subconjuntos disjuntos (um por rede: A, B, C, D),
   pelo hash SHA-256 do CNPJ da revenda: um estabelecimento cai sempre no
   mesmo posto e nunca aparece em dois recortes.
4. Grava `data/anp_posto_a.csv`, `..._b.csv`, `..._c.csv`, `..._d.csv` (UTF-8).

O CSV da ANP vem em UTF-8 com BOM; a leitura usa `utf-8-sig` para descartar o
BOM sem corromper o cabeçalho nem os acentos.

Uso:
    python scripts/preparar_csvs.py --entrada data/anp_bruto.csv --saida data/
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from pathlib import Path


# Mantenha igual a `src.protocolo.ESTADOS` (o script roda isolado, sem importar `src`).
ESTADOS_NORTE = {"AC", "AM", "AP", "PA", "RO", "RR", "TO"}


def indice_posto(cnpj: str, n_postos: int = 4) -> int:
    """Calcula o índice do servidor a partir do CNPJ."""

    if n_postos <= 0:
        raise ValueError("A quantidade de postos deve ser maior que zero")

    identificador = "".join(c for c in cnpj if c.isdigit())

    if not identificador:
        raise ValueError("CNPJ não informado")

    codigo = hashlib.sha256(identificador.encode("utf-8")).digest()

    return int.from_bytes(codigo, "big") % n_postos


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Divide o CSV da ANP em arquivos para os servidores."
    )

    parser.add_argument("--entrada", type=Path, required=True)
    parser.add_argument(
        "--saida",
        type=Path,
        required=True,
        help="Diretório onde os arquivos serão salvos."
    )
    parser.add_argument("--n-postos", type=int, default=4)
    parser.add_argument(
        "--separador",
        default=";",
        help="Separador das colunas do CSV."
    )

    args = parser.parse_args()

    if not 1 <= args.n_postos <= 4:
        parser.error("--n-postos deve estar entre 1 e 4")

    args.saida.mkdir(parents=True, exist_ok=True)

    with args.entrada.open(encoding="utf-8-sig", newline="") as arquivo:
        reader = csv.DictReader(arquivo, delimiter=args.separador)

        colunas_originais = reader.fieldnames or []

        if "Estado - Sigla" not in colunas_originais:
            raise ValueError("Coluna 'Estado - Sigla' não encontrada no CSV")

        linhas_norte = [
            row
            for row in reader
            if row.get("Estado - Sigla", "").strip() in ESTADOS_NORTE
        ]

    print(f"Linhas totais da Região Norte: {len(linhas_norte)}")

    nomes = ["a", "b", "c", "d"][:args.n_postos]
    for i, nome in enumerate(nomes):
        fatia = [
            row
            for row in linhas_norte
            if indice_posto(
                row.get("CNPJ da Revenda", ""),
                args.n_postos
            ) == i
        ]

        saida = args.saida / f"anp_posto_{nome}.csv"

        with saida.open("w", encoding="utf-8", newline="") as arquivo:
            writer = csv.DictWriter(
                arquivo,
                fieldnames=colunas_originais,
                delimiter=args.separador
            )

            writer.writeheader()
            writer.writerows(fatia)

        print(f"  {saida} — {len(fatia)} linhas")


if __name__ == "__main__":
    main()