"""Experimento 3 — Simulação de latência.

Para cada latência artificial L (aplicada a todos os postos), sobe um ambiente
novo e compara o tempo total das estratégias sequencial e concorrente.
Esperado: sequencial ≈ 4·L (soma), concorrente ≈ L (máximo).

Saídas (resultados/):
  exp_3_latencia.json
  exp_3_tempo_vs_latencia.png   curvas de tempo × latência (+ modelo teórico)
  exp_3_speedup.png             speedup (seq/conc) × latência
  exp_3_barras.png              barras agrupadas por latência

    python -m experimentos.exp_3_latencia [--latencias 0 100 250 500 1000 2000] [--rodadas 5]
"""

from __future__ import annotations

from experimentos import _comum as c
from src import protocolo as p

ESTRATEGIAS = (p.ESTRATEGIA_SEQUENCIAL, p.ESTRATEGIA_CONCORRENTE)


def medir(latencia: int, cidade: str, combustivel: str, rodadas: int) -> dict:
    tempos: dict[str, list[float]] = {e: [] for e in ESTRATEGIAS}
    degradadas = 0
    with c.Ambiente(latencia, tag=f"exp3_L{latencia}") as amb:
        for e in ESTRATEGIAS:  # aquecimento
            amb.consultar(cidade, combustivel, e)
        for _ in range(rodadas):  # alterna as estratégias para reduzir viés de ordem
            for e in ESTRATEGIAS:
                resp = amb.consultar(cidade, combustivel, e)
                tempos[e].append(float(resp["tempo_ms"]))
                degradadas += len(resp["indisponiveis"])
    return {"tempos": tempos, "indisponiveis_total": degradadas}


def graficos(latencias: list[int], resumo: dict, n_postos: int = 4) -> None:
    plt = c.pyplot()
    media = lambda e: [resumo[l][e]["media"] for l in latencias]
    desvio = lambda e: [resumo[l][e]["desvio"] for l in latencias]

    # 1) curvas tempo × latência
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for e in ESTRATEGIAS:
        ax.errorbar(latencias, media(e), yerr=desvio(e), marker="o", capsize=3,
                    color=c.COR[e], label=c.ROTULO[e])
    ax.plot(latencias, [n_postos * l for l in latencias], "--", color=c.COR[ESTRATEGIAS[0]],
            alpha=0.5, label=f"Teórico sequencial ({n_postos}·L)")
    ax.plot(latencias, latencias, "--", color=c.COR[ESTRATEGIAS[1]], alpha=0.5,
            label="Teórico concorrente (L)")
    ax.set_xlabel("Latência artificial por posto (ms)")
    ax.set_ylabel("Tempo total da consulta (ms)")
    ax.set_title("Experimento 3 — tempo × latência")
    ax.legend()
    c.salvar_fig(fig, "exp_3_tempo_vs_latencia")

    # 2) speedup
    fig, ax = plt.subplots(figsize=(7, 4.5))
    speedup = [media(ESTRATEGIAS[0])[i] / media(ESTRATEGIAS[1])[i] for i in range(len(latencias))]
    ax.plot(latencias, speedup, marker="o", color="#009E73", label="Speedup medido")
    ax.axhline(n_postos, ls="--", color="gray", label=f"Limite ideal ({n_postos} postos)")
    ax.set_xlabel("Latência artificial por posto (ms)")
    ax.set_ylabel("Speedup (tempo sequencial / concorrente)")
    ax.set_title("Experimento 3 — ganho da concorrência")
    ax.set_ylim(bottom=0)
    ax.legend()
    c.salvar_fig(fig, "exp_3_speedup")

    # 3) barras agrupadas
    fig, ax = plt.subplots(figsize=(8, 4.5))
    largura = 0.38
    xs = range(len(latencias))
    for k, e in enumerate(ESTRATEGIAS):
        pos = [x + (k - 0.5) * largura for x in xs]
        ax.bar(pos, media(e), largura, yerr=desvio(e), capsize=3, color=c.COR[e], label=c.ROTULO[e])
    ax.set_xticks(list(xs), [str(l) for l in latencias])
    ax.set_xlabel("Latência artificial por posto (ms)")
    ax.set_ylabel("Tempo total da consulta (ms)")
    ax.set_title("Experimento 3 — comparação por latência")
    ax.legend()
    c.salvar_fig(fig, "exp_3_barras")


def main() -> None:
    ap = c.parser_base("Experimento 3 — simulação de latência.")
    ap.add_argument("--latencias", type=int, nargs="+", default=[0, 100, 250, 500, 1000, 2000])
    ap.add_argument("--rodadas", type=int, default=5)
    args = ap.parse_args()
    c.validar_dados(args.cidade, args.combustivel)

    brutos, resumo = {}, {}
    for L in args.latencias:
        print(f"\n>>> latência {L} ms por posto …")
        r = medir(L, args.cidade, args.combustivel, args.rodadas)
        brutos[L] = r
        resumo[L] = {e: c.estatisticas(r["tempos"][e]) for e in ESTRATEGIAS}
        if r["indisponiveis_total"]:
            print(f"    ATENÇÃO: {r['indisponiveis_total']} respostas indisponíveis (rodada suspeita)")

    linhas = []
    for L in args.latencias:
        s, k = resumo[L][ESTRATEGIAS[0]], resumo[L][ESTRATEGIAS[1]]
        linhas.append([L, s["media"], s["desvio"], k["media"], k["desvio"], round(s["media"] / k["media"], 2)])
    print("\n" + c.tabela(
        ["L (ms)", "seq média", "seq desvio", "conc média", "conc desvio", "speedup"], linhas))

    c.salvar_json("exp_3_latencia", {
        "cidade": args.cidade, "combustivel": args.combustivel, "rodadas": args.rodadas,
        "latencias_ms": args.latencias,
        "resultados": {str(L): {"tempos_ms": brutos[L]["tempos"], "estatisticas": resumo[L],
                                "indisponiveis_total": brutos[L]["indisponiveis_total"]}
                       for L in args.latencias},
    })
    graficos(args.latencias, resumo)


if __name__ == "__main__":
    main()
