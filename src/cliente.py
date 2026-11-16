"""Cliente CLI do Agregador de Combustíveis.

Interface interativa em linha de comando: pergunta estado, cidade, combustível
e estratégia; envia a consulta ao agregador; imprime o ranking e o tempo total.

Uso:
    python -m src.cliente --host localhost --porta 5000
    python -m src.cliente --estado PA --cidade Belém --combustivel gasolina_comum
"""

from __future__ import annotations

import argparse
import logging
import socket
import sys

from src import protocolo as p

log = logging.getLogger("cliente")


def pedir_estado() -> str:
    """Pergunta a UF; aceita o número da lista ou a sigla (ex.: 2 ou AM)."""
    print("\nEstados da Região Norte:")
    for i, uf in enumerate(p.ESTADOS, 1):
        print(f"  {i}) {uf}")
    while True:
        escolha = input(f"Estado (1-{len(p.ESTADOS)} ou sigla): ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(p.ESTADOS):
            return p.ESTADOS[int(escolha) - 1]
        if p.normalizar_estado(escolha) in p.ESTADOS:
            return p.normalizar_estado(escolha)
        print("  → opção inválida.")


def pedir_cidade() -> str:
    while True:
        cidade = input("Cidade: ").strip()
        if cidade:
            return cidade
        print("  → cidade obrigatória.")


def pedir_combustivel() -> str:
    print("\nCombustíveis disponíveis:")
    for i, c in enumerate(p.COMBUSTIVEIS, 1):
        print(f"  {i}) {c}")
    while True:
        escolha = input("Escolha (1-{n}): ".format(n=len(p.COMBUSTIVEIS))).strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(p.COMBUSTIVEIS):
            return p.COMBUSTIVEIS[int(escolha) - 1]
        print("  → opção inválida.")


def pedir_estrategia() -> str:
    print("\nEstratégia:")
    print("  1) sequencial")
    print("  2) concorrente")
    while True:
        escolha = input("Escolha (1-2): ").strip()
        if escolha == "1":
            return p.ESTRATEGIA_SEQUENCIAL
        if escolha == "2":
            return p.ESTRATEGIA_CONCORRENTE
        print("  → opção inválida.")


def imprimir_resultado(resp: dict) -> None:
    if resp.get("status") == p.STATUS_ERRO:
        print(f"\n[erro do agregador] {resp.get('mensagem') or 'requisição rejeitada'}")
        return

    consulta = resp.get("consulta", {})
    print()
    print(f"→ {consulta.get('combustivel')} em {consulta.get('cidade')}/{consulta.get('estado')} "
          f"(modo {consulta.get('estrategia')}) — {resp.get('tempo_ms')} ms  [id {resp.get('id', '-')}]")
    print()

    resultados = resp.get("resultados", []) or []
    if not resultados:
        print("  Nenhum posto atende essa cidade nesse estado.")
    else:
        menor = (resp.get("menor_preco") or {}).get("posto")
        print("  Ranking (ordenado por preço):")
        for i, r in enumerate(resultados, 1):
            marcador = "★" if r.get("posto") == menor else " "
            print(f"   {marcador} {i}. Posto {r['posto']}  R$ {r['preco']:.2f}")

    indisp = resp.get("indisponiveis") or []
    if indisp:
        print("\n  Sem resposta:")
        for r in indisp:
            print(f"     Posto {r.get('posto', '?')}: {r.get('status')}")


def consultar(
    host: str, porta: int, estado: str, cidade: str, combustivel: str, estrategia: str
) -> dict:
    with socket.create_connection((host, porta), timeout=p.TIMEOUT_CLIENTE_S) as conn:
        conn.settimeout(p.TIMEOUT_CLIENTE_S)
        p.enviar_json(conn, {
            "id": p.novo_id(),
            "operacao": p.OP_CONSULTAR,
            "estado": estado,
            "combustivel": combustivel,
            "cidade": cidade,
            "estrategia": estrategia,
        }, par="agregador")
        return p.receber_json(conn, par="agregador")


def loop_interativo(host: str, porta: int) -> None:
    print(f"=== Agregador de Preços de Combustíveis — Região Norte ===")
    print(f"Agregador em {host}:{porta}. Digite Ctrl+C para sair.")
    while True:
        try:
            estado = pedir_estado()
            cidade = pedir_cidade()
            combustivel = pedir_combustivel()
            estrategia = pedir_estrategia()
            resp = consultar(host, porta, estado, cidade, combustivel, estrategia)
            imprimir_resultado(resp)
        except (KeyboardInterrupt, EOFError):
            print("\nAté mais.")
            return
        except (socket.timeout, ConnectionError, OSError) as e:
            print(f"\n[erro de rede] {e}")
        except ValueError as e:
            print(f"\n[resposta inválida] {e}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cliente CLI do Agregador de Combustíveis.")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--porta", type=int, default=5000)
    parser.add_argument(
        "--estado", type=p.normalizar_estado, choices=p.ESTADOS,
        help="UF da Região Norte. Com --cidade e --combustivel, roda uma consulta única.",
    )
    parser.add_argument("--cidade", help="Com --estado e --combustivel, roda uma consulta única.")
    parser.add_argument("--combustivel", choices=p.COMBUSTIVEIS)
    parser.add_argument("--estrategia", choices=p.ESTRATEGIAS, default=p.ESTRATEGIA_CONCORRENTE)
    parser.add_argument("--log", default="WARNING")
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
        p.configurar_rastreio("cliente")

    nao_interativo = (args.estado, args.cidade, args.combustivel)
    if any(nao_interativo) and not all(nao_interativo):
        parser.error("para a consulta única informe --estado, --cidade e --combustivel juntos")
    if all(nao_interativo):
        try:
            resp = consultar(
                args.host, args.porta, args.estado, args.cidade, args.combustivel, args.estrategia
            )
        except (socket.timeout, ConnectionError, OSError) as e:
            sys.exit(f"[erro de rede] {e}")
        except ValueError as e:
            sys.exit(f"[resposta inválida] {e}")
        imprimir_resultado(resp)
    else:
        loop_interativo(args.host, args.porta)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        sys.exit(0)
