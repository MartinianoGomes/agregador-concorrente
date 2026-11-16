"""Experimento 4 — Múltiplos clientes simultâneos.

Dispara N clientes (threads, liberadas juntas por uma Barrier) contra o agregador
e mede o tempo observado por cada cliente, a vazão e as falhas, para as duas
estratégias. Os postos têm latência fixa para a diferença ser visível.

Saídas (resultados/):
  exp_4_multiplos_clientes.json
  exp_4_tempo_medio.png      tempo médio por cliente × N
  exp_4_p95.png              p95 (e máximo) × N
  exp_4_vazao.png            consultas/s × N
  exp_4_falhas.png           falhas e respostas degradadas × N
  exp_4_cliente_vs_agregador.png  tempo no cliente × tempo_ms do agregador (fila)

    python -m experimentos.exp_4_multiplos_clientes [--clientes 1 2 5 10 20 50] [--latencia-ms 200]
"""

from __future__ import annotations

import threading
import time

from experimentos import _comum as c
from src import protocolo as p

ESTRATEGIAS = (p.ESTRATEGIA_SEQUENCIAL, p.ESTRATEGIA_CONCORRENTE)


def _cliente(amb, cidade, combustivel, estrategia, barreira, saida: list) -> None:
    barreira.wait()
    t0 = time.perf_counter()
    reg = {"t0": t0, "t1": t0, "ms": 0.0, "agregador_ms": None, "falha": None, "degradada": False}
    try:
        resp = amb.consultar(cidade, combustivel, estrategia)
        reg["t1"] = time.perf_counter()
        if "resultados" not in resp:
            reg["falha"] = f"resposta inesperada: {resp.get('mensagem') or resp.get('status')}"
        else:
            reg["agregador_ms"] = float(resp["tempo_ms"])
            reg["degradada"] = bool(resp["indisponiveis"])
    except Exception as e:  # noqa: BLE001 — queremos contar qualquer falha de rede
        reg["t1"] = time.perf_counter()
        reg["falha"] = f"{type(e).__name__}: {e}"
    reg["ms"] = (reg["t1"] - reg["t0"]) * 1000
    saida.append(reg)


def lote(amb, n: int, cidade: str, combustivel: str, estrategia: str) -> dict:
    barreira = threading.Barrier(n)
    saida: list[dict] = []
    ths = [threading.Thread(target=_cliente, args=(amb, cidade, combustivel, estrategia, barreira, saida))
           for _ in range(n)]
    for t in ths:
        t.start()
    for t in ths:
        t.join()
    duracao = max(r["t1"] for r in saida) - min(r["t0"] for r in saida)
    return {"regs": saida, "duracao_s": duracao}


def graficos(ns: list[int], resumo: dict) -> None:
    plt = c.pyplot()

    def serie(e, chave):
        return [resumo[n][e][chave] for n in ns]

    def linha(nome, titulo, ylabel, chaves, logx=True):
        fig, ax = plt.subplots(figsize=(7, 4.5))
        for e in ESTRATEGIAS:
            for chave, estilo, sufixo in chaves:
                ax.plot(ns, serie(e, chave), estilo, marker="o", color=c.COR[e],
                        label=f"{c.ROTULO[e]}{sufixo}")
        ax.set_xscale("log" if logx else "linear")
        ax.set_xticks(ns, [str(n) for n in ns])
        ax.set_xlabel("Clientes simultâneos (N)")
        ax.set_ylabel(ylabel)
        ax.set_title(titulo)
        ax.legend()
        c.salvar_fig(fig, nome)

    # 1) tempo médio ± desvio
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for e in ESTRATEGIAS:
        ax.errorbar(ns, serie(e, "media"), yerr=serie(e, "desvio"), marker="o", capsize=3,
                    color=c.COR[e], label=c.ROTULO[e])
    ax.set_xscale("log")
    ax.set_xticks(ns, [str(n) for n in ns])
    ax.set_xlabel("Clientes simultâneos (N)")
    ax.set_ylabel("Tempo médio por cliente (ms)")
    ax.set_title("Experimento 4 — tempo médio × nº de clientes")
    ax.legend()
    c.salvar_fig(fig, "exp_4_tempo_medio")

    # 2) p95 e máximo
    linha("exp_4_p95", "Experimento 4 — cauda de latência", "Tempo (ms)",
          [("p95", "-", " (p95)"), ("max", ":", " (máx.)")])

    # 3) vazão
    linha("exp_4_vazao", "Experimento 4 — vazão do agregador", "Consultas por segundo",
          [("vazao", "-", "")])

    # 4) falhas
    fig, ax = plt.subplots(figsize=(7, 4.5))
    largura, xs = 0.2, range(len(ns))
    desloc = {(ESTRATEGIAS[0], "falhas"): -1.5, (ESTRATEGIAS[0], "degradadas"): -0.5,
              (ESTRATEGIAS[1], "falhas"): 0.5, (ESTRATEGIAS[1], "degradadas"): 1.5}
    for (e, chave), d in desloc.items():
        ax.bar([x + d * largura for x in xs], serie(e, chave), largura, color=c.COR[e],
               alpha=1.0 if chave == "falhas" else 0.45,
               label=f"{c.ROTULO[e]} — {'falhas' if chave == 'falhas' else 'degradadas'}")
    ax.set_xticks(list(xs), [str(n) for n in ns])
    if not any(serie(e, k) and max(serie(e, k)) for e in ESTRATEGIAS for k in ("falhas", "degradadas")):
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 1])
        ax.text(0.5, 0.5, "Nenhuma falha nem resposta degradada em todos os pontos medidos",
                transform=ax.transAxes, ha="center", va="center", fontsize=11, color="#009E73")
    ax.set_xlabel("Clientes simultâneos (N)")
    ax.set_ylabel("Ocorrências (soma das repetições)")
    ax.set_title("Experimento 4 — falhas × nº de clientes")
    ax.legend(fontsize=8)
    c.salvar_fig(fig, "exp_4_falhas")

    # 5) tempo no cliente × tempo no agregador
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for e in ESTRATEGIAS:
        ax.plot(ns, serie(e, "media"), "-", marker="o", color=c.COR[e], label=f"{c.ROTULO[e]} — cliente")
        ax.plot(ns, serie(e, "agregador_media"), "--", marker="s", color=c.COR[e],
                label=f"{c.ROTULO[e]} — agregador (tempo_ms)")
    ax.set_xscale("log")
    ax.set_xticks(ns, [str(n) for n in ns])
    ax.set_xlabel("Clientes simultâneos (N)")
    ax.set_ylabel("Tempo médio (ms)")
    ax.set_title("Experimento 4 — tempo visto pelo cliente × medido pelo agregador")
    ax.legend(fontsize=8)
    c.salvar_fig(fig, "exp_4_cliente_vs_agregador")


def main() -> None:
    ap = c.parser_base("Experimento 4 — múltiplos clientes simultâneos.")
    ap.add_argument("--clientes", type=int, nargs="+", default=[1, 2, 5, 10, 20, 50])
    ap.add_argument("--repeticoes", type=int, default=3)
    ap.add_argument("--latencia-ms", type=int, default=200)
    args = ap.parse_args()
    c.validar_dados(args.cidade, args.combustivel)

    resumo: dict[int, dict] = {}
    brutos: dict[str, dict] = {}
    with c.Ambiente(args.latencia_ms, tag="exp4") as amb:
        for e in ESTRATEGIAS:  # aquecimento
            amb.consultar(args.cidade, args.combustivel, e)
        for n in args.clientes:
            resumo[n] = {}
            for e in ESTRATEGIAS:
                regs, vazoes = [], []
                for _ in range(args.repeticoes):
                    r = lote(amb, n, args.cidade, args.combustivel, e)
                    regs += r["regs"]
                    vazoes.append(n / r["duracao_s"])
                tempos = [r["ms"] for r in regs if r["falha"] is None]
                ag = [r["agregador_ms"] for r in regs if r["agregador_ms"] is not None]
                est = c.estatisticas(tempos)
                resumo[n][e] = {
                    **est,
                    "vazao": round(sum(vazoes) / len(vazoes), 2),
                    "falhas": sum(1 for r in regs if r["falha"]),
                    "degradadas": sum(1 for r in regs if r["degradada"]),
                    "agregador_media": c.estatisticas(ag)["media"],
                }
                brutos[f"{n}/{e}"] = {
                    "tempos_ms": [round(r["ms"], 2) for r in regs],
                    "erros": sorted({r["falha"] for r in regs if r["falha"]}),
                }
                print(f"N={n:>3} {e:<11} média={est['media']:>8} ms  p95={est['p95']:>8}  "
                      f"vazão={resumo[n][e]['vazao']:>6}/s  falhas={resumo[n][e]['falhas']}")

    linhas = []
    for n in args.clientes:
        for e in ESTRATEGIAS:
            r = resumo[n][e]
            linhas.append([n, c.ROTULO[e], r["media"], r["desvio"], r["p95"], r["max"],
                           r["vazao"], r["falhas"], r["degradadas"]])
    print("\n" + c.tabela(["N", "estratégia", "média", "desvio", "p95", "máx", "vazão/s", "falhas",
                           "degradadas"], linhas))

    c.salvar_json("exp_4_multiplos_clientes", {
        "cidade": args.cidade, "combustivel": args.combustivel,
        "latencia_ms": args.latencia_ms, "repeticoes": args.repeticoes,
        "clientes": args.clientes,
        "resumo": {str(n): resumo[n] for n in args.clientes},
        "brutos": brutos,
    })
    graficos(args.clientes, resumo)


if __name__ == "__main__":
    main()
