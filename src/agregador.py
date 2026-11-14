"""Servidor Agregador.

Recebe consultas do cliente, despacha para os postos configurados nos modos
sequencial ou concorrente, consolida e ordena, e devolve ao cliente.

Uso:
    python -m src.agregador --porta 5000 \
        --posto A:127.0.0.1:6001 \
        --posto B:127.0.0.1:6002 \
        --posto C:127.0.0.1:6003 \
        --posto D:127.0.0.1:6004
"""

from __future__ import annotations

import argparse
import logging
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

from src import protocolo as p

log = logging.getLogger("agregador")


@dataclass(frozen=True)
class PostoEndereco:
    nome: str
    host: str
    porta: int

    @classmethod
    def de_string(cls, s: str) -> "PostoEndereco":
        """Aceita formato 'nome:host:porta', ex.: 'A:127.0.0.1:6001'."""
        try:
            nome, host, porta = s.split(":")
            return cls(nome=nome, host=host, porta=int(porta))
        except ValueError as e:
            raise argparse.ArgumentTypeError(f"formato inválido {s!r}: esperado nome:host:porta") from e


# ---------- Consulta a um único posto ----------
def consultar_posto(
    posto: PostoEndereco,
    combustivel: str,
    cidade: str,
) -> dict:
    """Abre conexão TCP com o posto, envia a consulta, aguarda e devolve a resposta.

    Erros e timeouts são capturados e devolvidos como dicts com o status
    apropriado, para não quebrar o loop de consolidação.
    """
    try:
        with socket.create_connection((posto.host, posto.porta), timeout=p.TIMEOUT_POSTO_S) as conn:
            conn.settimeout(p.TIMEOUT_POSTO_S)
            p.enviar_json(conn, {
                "operacao": p.OP_CONSULTAR,
                "combustivel": combustivel,
                "cidade": cidade,
            })
            return p.receber_json(conn)
    except socket.timeout:
        return {"posto": posto.nome, "status": p.STATUS_TIMEOUT}
    except (ConnectionRefusedError, ConnectionError, OSError) as e:
        log.warning("Posto %s indisponível: %s", posto.nome, e)
        return {"posto": posto.nome, "status": p.STATUS_INDISPONIVEL, "mensagem": str(e)}
    except ValueError as e:
        return {"posto": posto.nome, "status": p.STATUS_ERRO, "mensagem": str(e)}


# ---------- Estratégias ----------
def consultar_sequencial(
    postos: list[PostoEndereco],
    combustivel: str,
    cidade: str,
) -> list[dict]:
    return [consultar_posto(p_, combustivel, cidade) for p_ in postos]


def consultar_concorrente(
    postos: list[PostoEndereco],
    combustivel: str,
    cidade: str,
) -> list[dict]:
    resultados: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(postos)) as pool:
        futures = {
            pool.submit(consultar_posto, p_, combustivel, cidade): p_
            for p_ in postos
        }
        for fut in as_completed(futures):
            resultados.append(fut.result())
    # ordena de volta pela ordem original dos postos para a saída ser previsível
    ordem = {po.nome: i for i, po in enumerate(postos)}
    resultados.sort(key=lambda r: ordem.get(r.get("posto", ""), 999))
    return resultados


# ---------- Consolidação ----------
def consolidar(respostas_brutas: list[dict]) -> tuple[list[dict], list[dict], dict | None]:
    """Separa sucesso (ranking) de indisponíveis e identifica o menor preço."""
    sucessos = [r for r in respostas_brutas if r.get("status") == p.STATUS_SUCESSO]
    indisponiveis = [r for r in respostas_brutas if r.get("status") != p.STATUS_SUCESSO]
    sucessos.sort(key=lambda r: r["preco"])
    menor = (
        {"posto": sucessos[0]["posto"], "preco": sucessos[0]["preco"]}
        if sucessos
        else None
    )
    return sucessos, indisponiveis, menor


# ---------- Handler de cliente ----------
def tratar_cliente(conn: socket.socket, addr, postos: list[PostoEndereco]) -> None:
    with conn:
        try:
            req = p.receber_json(conn)
        except (ConnectionError, ValueError) as e:
            log.warning("Erro ao ler cliente %s: %s", addr, e)
            return

        ok, erro = p.validar_requisicao_consulta(req)
        if not ok or "estrategia" not in req:
            p.enviar_json(conn, {"status": p.STATUS_ERRO, "mensagem": erro or "estrategia obrigatória"})
            return

        combustivel = req["combustivel"]
        cidade = req["cidade"]
        estrategia = req["estrategia"]

        t0 = time.perf_counter()
        if estrategia == p.ESTRATEGIA_SEQUENCIAL:
            brutas = consultar_sequencial(postos, combustivel, cidade)
        else:
            brutas = consultar_concorrente(postos, combustivel, cidade)
        tempo_ms = round((time.perf_counter() - t0) * 1000, 1)

        sucessos, indisponiveis, menor = consolidar(brutas)
        resposta = {
            "consulta": {"combustivel": combustivel, "cidade": cidade, "estrategia": estrategia},
            "resultados": sucessos,
            "indisponiveis": indisponiveis,
            "menor_preco": menor,
            "tempo_ms": tempo_ms,
        }
        p.enviar_json(conn, resposta)
        log.info(
            "cliente=%s cidade=%s combustivel=%s estrategia=%s tempo_ms=%.1f sucessos=%d",
            addr, cidade, combustivel, estrategia, tempo_ms, len(sucessos),
        )


# ---------- Server loop ----------
def rodar(host: str, porta: int, postos: list[PostoEndereco]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((host, porta))
        servidor.listen(16)
        log.info("Agregador no ar em %s:%d — %d postos configurados", host, porta, len(postos))
        for po in postos:
            log.info("  • %s em %s:%d", po.nome, po.host, po.porta)
        while True:
            conn, addr = servidor.accept()
            t = threading.Thread(
                target=tratar_cliente,
                args=(conn, addr, postos),
                daemon=True,
            )
            t.start()


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor agregador de preços de combustíveis.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--porta", type=int, default=5000)
    parser.add_argument(
        "--posto",
        dest="postos",
        type=PostoEndereco.de_string,
        action="append",
        required=True,
        help="Repita este argumento por posto. Formato: nome:host:porta (ex.: A:127.0.0.1:6001)",
    )
    parser.add_argument("--log", default="INFO")
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )
    try:
        rodar(args.host, args.porta, args.postos)
    except KeyboardInterrupt:
        log.info("Encerrando por Ctrl+C")


if __name__ == "__main__":
    main()
