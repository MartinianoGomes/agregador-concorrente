"""Servidor TCP de um Posto de Combustíveis.

Cada instância representa uma rede com pontos de venda em cidades da Região
Norte. A base de preços é carregada no startup do processo e indexada por
(estado, cidade_normalizada, combustível) para resposta em tempo constante.

Uso:
    python -m src.posto --nome A --porta 6001 --anp data/anp_posto_a.csv
    python -m src.posto --nome B --porta 6002 --anp data/anp_posto_b.csv
    python -m src.posto --nome C --porta 6003 --anp data/anp_posto_c.csv
    python -m src.posto --nome D --porta 6004 --anp data/anp_posto_d.csv

Opcional: `--latencia-ms N` injeta um atraso artificial em cada resposta,
usado no Experimento 3 (comparação sequencial × concorrente com latência).
"""

from __future__ import annotations

import argparse
import csv
import logging
import socket
import threading
import time
from datetime import datetime
from pathlib import Path

from src import protocolo as p

log = logging.getLogger("posto")


# ---------- Carregamento da base ----------
def carregar_base_precos(csv_path: Path) -> dict[tuple[str, str, str], float]:
    """Carrega os preços mais recentes de cada estabelecimento.

    Devolve um dict `(estado, cidade_normalizada, combustível) → preço`, em que o
    preço é o menor entre as últimas coletas dos estabelecimentos daquela cidade.
    """

    mapa_combustiveis = {
        "GASOLINA": "gasolina_comum",
        "GASOLINA ADITIVADA": "gasolina_aditivada",
        "ETANOL": "etanol",
        "DIESEL S10": "diesel_s10",
    }

    # Última coleta de cada estabelecimento, estado, cidade e combustível.
    ultimas_coletas = {}

    with csv_path.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, delimiter=";")

        for linha in leitor:
            estado = p.normalizar_estado(linha["Estado - Sigla"])
            cidade = p.normalizar_cidade(linha["Municipio"])
            produto = linha["Produto"].strip().upper()
            combustivel = mapa_combustiveis.get(produto)

            if combustivel is None:
                continue

            cnpj = "".join(c for c in linha["CNPJ da Revenda"] if c.isdigit())

            try:
                preco = float(linha["Valor de Venda"].replace(",", "."))
                data = datetime.strptime(linha["Data da Coleta"], "%d/%m/%Y").date()
            except (ValueError, TypeError) as erro:
                log.warning(
                    "Registro ignorado na linha %d de %s: %s",
                    leitor.line_num, csv_path.name, erro,
                )
                continue

            chave = (cnpj, estado, cidade, combustivel)

            if chave not in ultimas_coletas:
                ultimas_coletas[chave] = (data, preco)
            else:
                data_anterior, _ = ultimas_coletas[chave]

                if data > data_anterior:
                    ultimas_coletas[chave] = (data, preco)

    # Menor preço entre as últimas coletas dos estabelecimentos.
    base: dict[tuple[str, str, str], float] = {}

    for (_, estado, cidade, combustivel), (_, preco) in ultimas_coletas.items():
        chave = (estado, cidade, combustivel)

        if chave not in base or preco < base[chave]:
            base[chave] = preco

    return base


# ---------- Handler de cada conexão ----------
def tratar_conexao(
    conn: socket.socket,
    addr: tuple[str, int],
    *,
    nome_posto: str,
    base: dict[tuple[str, str, str], float],
    latencia_ms: int,
) -> None:
    """Lê uma requisição, consulta a base e responde."""
    with conn:
        try:
            msg = p.receber_json(conn)
        except (ConnectionError, ValueError) as e:
            log.warning("[%s] erro ao ler requisição de %s: %s", nome_posto, addr, e)
            return

        ok, erro = p.validar_requisicao_consulta(msg)
        if not ok:
            resposta = {"posto": nome_posto, "status": p.STATUS_ERRO, "mensagem": erro}
            p.enviar_json(conn, resposta)
            return

        estado = p.normalizar_estado(msg["estado"])
        cidade_norm = p.normalizar_cidade(msg["cidade"])
        combustivel = msg["combustivel"]

        if latencia_ms > 0:
            time.sleep(latencia_ms / 1000.0)

        preco = base.get((estado, cidade_norm, combustivel))
        if preco is None:
            resposta = {
                "posto": nome_posto,
                "estado": estado,
                "cidade": msg["cidade"],
                "status": p.STATUS_NAO_ATENDIDA,
            }
        else:
            resposta = {
                "posto": nome_posto,
                "estado": estado,
                "cidade": msg["cidade"],
                "combustivel": combustivel,
                "preco": preco,
                "status": p.STATUS_SUCESSO,
            }
        p.enviar_json(conn, resposta)
        log.info(
            "[%s] %s/%s %s -> %s", nome_posto, cidade_norm, estado, combustivel, resposta["status"]
        )


# ---------- Server loop ----------
def rodar(host: str, porta: int, nome_posto: str, anp_csv: Path, latencia_ms: int) -> None:
    base = carregar_base_precos(anp_csv)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((host, porta))
        servidor.listen(16)
        log.info(
            "[%s] Posto no ar em %s:%d — %d entradas na base",
            nome_posto, host, porta, len(base),
        )
        while True:
            conn, addr = servidor.accept()
            t = threading.Thread(
                target=tratar_conexao,
                args=(conn, addr),
                kwargs={"nome_posto": nome_posto, "base": base, "latencia_ms": latencia_ms},
                daemon=True,
            )
            t.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor TCP de um posto de combustíveis.")
    parser.add_argument("--nome", required=True, help="Nome do posto (ex.: A, B, C, D)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--porta", type=int, required=True)
    parser.add_argument("--anp", type=Path, required=True, help="Caminho do CSV com o recorte da ANP")
    parser.add_argument("--latencia-ms", type=int, default=0, help="Atraso artificial por consulta (ms)")
    parser.add_argument("--log", default="INFO", help="Nível de log: DEBUG, INFO, WARNING, ERROR")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )
    try:
        rodar(args.host, args.porta, args.nome, args.anp, args.latencia_ms)
    except KeyboardInterrupt:
        log.info("[%s] Encerrando por Ctrl+C", args.nome)


if __name__ == "__main__":
    main()
