"""Servidor TCP de um Posto de Combustíveis.

Cada instância representa uma rede com pontos de venda em cidades da Região
Norte. A base de preços é carregada no startup do processo e indexada por
(cidade_normalizada, combustível) para resposta em tempo constante.

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
import logging
import random
import socket
import threading
import time
from pathlib import Path

from src import protocolo as p

log = logging.getLogger("posto")


# ---------- Carregamento da base ----------
def carregar_base_precos(csv_path: Path) -> dict[tuple[str, str], float]:
    """Lê o CSV da ANP e devolve um dicionário {(cidade_norm, combustível): preço}.

    TODO (Gustavo): implementar a leitura real do CSV da ANP.
      - Formato do CSV: ver metadados em
        https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis
      - Colunas esperadas: Municipio, Produto, Valor_de_Venda (ou equivalentes).
      - Mapear os valores de `Produto` para os identificadores do protocolo
        (gasolina_comum, gasolina_aditivada, etanol, diesel_s10).
      - Se houver várias linhas para a mesma (cidade, produto), usar o preço
        médio (ou mínimo — definir com o grupo).

    Enquanto o CSV real não está em mãos, esta versão devolve uma base
    sintética para que o agregador e o cliente possam ser desenvolvidos
    em paralelo.
    """
    if csv_path.exists():
        log.warning("Carregamento do CSV ainda não implementado — usando base sintética.")
    else:
        log.warning("CSV %s não encontrado — usando base sintética.", csv_path)

    # Base sintética: algumas cidades da Região Norte com preços fictícios.
    cidades_norte = ["belem", "manaus", "porto velho", "macapa", "rio branco", "palmas", "boa vista", "santarem"]
    base: dict[tuple[str, str], float] = {}
    rng = random.Random(csv_path.name)  # determinístico pelo nome do arquivo
    for cidade in cidades_norte:
        # cada posto cobre um subconjunto aleatório das cidades
        if rng.random() < 0.7:
            for combustivel in p.COMBUSTIVEIS:
                base[(cidade, combustivel)] = round(rng.uniform(4.0, 7.5), 2)
    return base


# ---------- Handler de cada conexão ----------
def tratar_conexao(
    conn: socket.socket,
    addr: tuple[str, int],
    *,
    nome_posto: str,
    base: dict[tuple[str, str], float],
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

        cidade_norm = p.normalizar_cidade(msg["cidade"])
        combustivel = msg["combustivel"]

        if latencia_ms > 0:
            time.sleep(latencia_ms / 1000.0)

        preco = base.get((cidade_norm, combustivel))
        if preco is None:
            resposta = {
                "posto": nome_posto,
                "cidade": msg["cidade"],
                "status": p.STATUS_NAO_ATENDIDA,
            }
        else:
            resposta = {
                "posto": nome_posto,
                "cidade": msg["cidade"],
                "combustivel": combustivel,
                "preco": preco,
                "status": p.STATUS_SUCESSO,
            }
        p.enviar_json(conn, resposta)
        log.info("[%s] %s %s -> %s", nome_posto, cidade_norm, combustivel, resposta["status"])


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
