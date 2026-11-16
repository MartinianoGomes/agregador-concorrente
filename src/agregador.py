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
    estado: str,
    combustivel: str,
    cidade: str,
    id_req: str | None = None,
) -> dict:
    """Abre conexão TCP com o posto, envia a consulta, aguarda e devolve a resposta.

    Erros e timeouts são capturados e devolvidos como dicts com o status
    apropriado, para não quebrar o loop de consolidação. `id_req` é o id de
    rastreio da consulta, repassado ao posto.
    """
    par = f"posto {posto.nome}"
    requisicao = {
        "operacao": p.OP_CONSULTAR,
        "estado": estado,
        "combustivel": combustivel,
        "cidade": cidade,
    }
    if id_req:
        requisicao["id"] = id_req
    t0 = time.perf_counter()
    decorrido = lambda: (time.perf_counter() - t0) * 1000  # noqa: E731
    try:
        with socket.create_connection((posto.host, posto.porta), timeout=p.TIMEOUT_POSTO_S) as conn:
            conn.settimeout(p.TIMEOUT_POSTO_S)
            p.enviar_json(conn, requisicao, par=par)
            resposta = p.receber_json(conn, par=par)
            p.rastrear_evento(f"{par} respondeu em {decorrido():.1f} ms | id={id_req or '-'}")
            return resposta
    except socket.timeout:
        p.rastrear_evento(f"✕ {par} sem resposta: timeout após {decorrido():.0f} ms "
                          f"(limite {p.TIMEOUT_POSTO_S:.0f} s) | id={id_req or '-'}")
        return {"posto": posto.nome, "status": p.STATUS_TIMEOUT}
    except (ConnectionRefusedError, ConnectionError, OSError) as e:
        log.warning("Posto %s indisponível: %s", posto.nome, e)
        p.rastrear_evento(f"✕ {par} indisponível após {decorrido():.1f} ms: {e} | id={id_req or '-'}")
        return {"posto": posto.nome, "status": p.STATUS_INDISPONIVEL, "mensagem": str(e)}
    except ValueError as e:
        p.rastrear_evento(f"✕ {par} enviou resposta inválida: {e} | id={id_req or '-'}")
        return {"posto": posto.nome, "status": p.STATUS_ERRO, "mensagem": str(e)}


# ---------- Estratégias ----------
def consultar_sequencial(
    postos: list[PostoEndereco],
    estado: str,
    combustivel: str,
    cidade: str,
    id_req: str | None = None,
) -> list[dict]:
    return [consultar_posto(p_, estado, combustivel, cidade, id_req) for p_ in postos]


def consultar_concorrente(
    postos: list[PostoEndereco],
    estado: str,
    combustivel: str,
    cidade: str,
    id_req: str | None = None,
) -> list[dict]:
    resultados: list[dict] = []
    with ThreadPoolExecutor(max_workers=len(postos), thread_name_prefix="consulta-posto") as pool:
        futures = {
            pool.submit(consultar_posto, p_, estado, combustivel, cidade, id_req): p_
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
            req = p.receber_json(conn, par="cliente")
        except (ConnectionError, ValueError) as e:
            log.warning("Erro ao ler cliente %s: %s", addr, e)
            return

        ok, erro = p.validar_requisicao_consulta(req)
        if not ok or "estrategia" not in req:
            resposta_erro = {"status": p.STATUS_ERRO, "mensagem": erro or "estrategia obrigatória"}
            if isinstance(req, dict) and isinstance(req.get("id"), str):
                resposta_erro["id"] = req["id"]
            p.enviar_json(conn, resposta_erro, par="cliente")
            return

        # o cliente manda o id de rastreio; se não mandar, o agregador cria um
        id_req = req.get("id") or p.novo_id()

        estado = p.normalizar_estado(req["estado"])
        combustivel = req["combustivel"]
        cidade = req["cidade"]
        estrategia = req["estrategia"]

        t0 = time.perf_counter()
        if estrategia == p.ESTRATEGIA_SEQUENCIAL:
            brutas = consultar_sequencial(postos, estado, combustivel, cidade, id_req)
        else:
            brutas = consultar_concorrente(postos, estado, combustivel, cidade, id_req)
        tempo_ms = round((time.perf_counter() - t0) * 1000, 1)

        sucessos, indisponiveis, menor = consolidar(brutas)
        resposta = {
            "id": id_req,
            "consulta": {
                "combustivel": combustivel,
                "estado": estado,
                "cidade": cidade,
                "estrategia": estrategia,
            },
            "resultados": sucessos,
            "indisponiveis": indisponiveis,
            "menor_preco": menor,
            "tempo_ms": tempo_ms,
        }
        p.enviar_json(conn, resposta, par="cliente")
        log.info(
            "id=%s cliente=%s estado=%s cidade=%s combustivel=%s estrategia=%s tempo_ms=%.1f sucessos=%d",
            id_req, addr, estado, cidade, combustivel, estrategia, tempo_ms, len(sucessos),
        )


# ---------- Server loop ----------
def rodar(host: str, porta: int, postos: list[PostoEndereco]) -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
        servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        servidor.bind((host, porta))
        servidor.listen(p.BACKLOG)
        log.info("Agregador no ar em %s:%d — %d postos configurados", host, porta, len(postos))
        for po in postos:
            log.info("  • %s em %s:%d", po.nome, po.host, po.porta)
        while True:
            conn, addr = servidor.accept()
            t = threading.Thread(
                target=tratar_cliente,
                args=(conn, addr, postos),
                name=f"cliente-{addr[1]}",
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
    parser.add_argument(
        "--rastreio", action="store_true",
        help="Mostra em stderr cada mensagem enviada e recebida, com o JSON completo.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=args.log,
        format="%(asctime)s %(levelname)s %(name)s | %(message)s",
    )
    if args.rastreio:
        p.configurar_rastreio("agregador")
    try:
        rodar(args.host, args.porta, args.postos)
    except KeyboardInterrupt:
        log.info("Encerrando por Ctrl+C")


if __name__ == "__main__":
    main()
