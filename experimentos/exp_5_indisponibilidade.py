"""Experimento 5 — Indisponibilidade de um posto.

Cenários (cada um nas duas estratégias, com ambiente novo e verificação automática):

  0. Referência         — 4 postos saudáveis (latência 500 ms).
  A. Fora do ar antes   — o posto D nunca sobe; esperado `indisponivel`.
  B. Cai durante        — o posto A é encerrado 0,5 s depois de a consulta começar
                          (latência 2 s); esperado `indisponivel` (conexão encerrada).
  C. Pendurado          — o posto D demora 6 s (> timeout de 5 s); esperado `timeout`.

Em todos, os demais postos devem aparecer com `sucesso` e `menor_preco` deve
considerar só quem respondeu.

Saídas (resultados/):
  exp_5_indisponibilidade.json
  exp_5_tempos.png     tempo total por cenário e estratégia (com o timeout de 5 s)
  exp_5_status.png     respostas por status em cada cenário (estratégia concorrente)

    python -m experimentos.exp_5_indisponibilidade
"""

from __future__ import annotations

import threading
import time
from collections import Counter

from experimentos import _comum as c
from src import protocolo as p

ESTRATEGIAS = (p.ESTRATEGIA_SEQUENCIAL, p.ESTRATEGIA_CONCORRENTE)
ATRASO_KILL_S = 0.5

# nome -> (título, kwargs do Ambiente, posto afetado, status esperado, descrição)
CENARIOS = {
    "0_referencia": ("0. Referência", dict(latencia_ms=500), None, None),
    "A_fora_do_ar": ("A. Fora do ar antes", dict(latencia_ms=500, ativos="ABC"), "D",
                     p.STATUS_INDISPONIVEL),
    "B_cai_durante": ("B. Cai durante a consulta", dict(latencia_ms=2000), "A",
                      p.STATUS_INDISPONIVEL),
    "C_pendurado": ("C. Pendurado (timeout)", dict(latencia_ms={"A": 500, "B": 500, "C": 500,
                                                                   "D": 6000}), "D",
                    p.STATUS_TIMEOUT),
}


def verificar(resp: dict, afetado: str | None, esperado: str | None, ms: float, cen: str) -> list[str]:
    problemas = []
    sucessos = {r["posto"] for r in resp["resultados"]}
    indisp = {r["posto"]: r["status"] for r in resp["indisponiveis"]}
    saudaveis = {n for n in c.NOMES_POSTOS if n != afetado}
    if sucessos != saudaveis:
        problemas.append(f"sucessos={sorted(sucessos)} (esperado {sorted(saudaveis)})")
    if afetado is None:
        if indisp:
            problemas.append(f"indisponíveis inesperados: {indisp}")
    elif indisp.get(afetado) != esperado:
        problemas.append(f"posto {afetado}: status {indisp.get(afetado)!r} (esperado {esperado!r})")
    menor = resp["menor_preco"]
    if resp["resultados"] and (menor is None or menor["preco"] != min(r["preco"] for r in resp["resultados"])):
        problemas.append("menor_preco inconsistente com os resultados")
    if cen == "C_pendurado" and ms > (p.TIMEOUT_POSTO_S + 3) * 1000:
        problemas.append(f"tempo {ms:.0f} ms não respeita o timeout de {p.TIMEOUT_POSTO_S}s")
    return problemas


def executar(cen: str, estrategia: str, cidade: str, combustivel: str) -> dict:
    titulo, kw, afetado, esperado = CENARIOS[cen]
    with c.Ambiente(tag=f"exp5_{cen}_{estrategia}", **kw) as amb:
        caixa: dict = {}

        def consulta() -> None:
            caixa["resp"] = amb.consultar(cidade, combustivel, estrategia)

        t0 = time.perf_counter()
        th = threading.Thread(target=consulta)
        th.start()
        if cen == "B_cai_durante":
            time.sleep(ATRASO_KILL_S)
            amb.matar_posto(afetado)
        th.join()
        ms = (time.perf_counter() - t0) * 1000
    resp = caixa["resp"]
    problemas = verificar(resp, afetado, esperado, ms, cen)
    return {"cenario": cen, "titulo": titulo, "estrategia": estrategia, "tempo_cliente_ms": round(ms, 1),
            "tempo_agregador_ms": resp["tempo_ms"], "resposta": resp, "problemas": problemas,
            "aprovado": not problemas}


def graficos(resultados: list[dict]) -> None:
    plt = c.pyplot()
    cens = list(CENARIOS)
    titulos = [CENARIOS[k][0].replace(". ", ".\n", 1) for k in cens]
    por = {(r["cenario"], r["estrategia"]): r for r in resultados}

    fig, ax = plt.subplots(figsize=(9, 4.8))
    largura, xs = 0.38, range(len(cens))
    for k, e in enumerate(ESTRATEGIAS):
        vals = [por[(cn, e)]["tempo_cliente_ms"] / 1000 for cn in cens]
        barras = ax.bar([x + (k - 0.5) * largura for x in xs], vals, largura, color=c.COR[e],
                        label=c.ROTULO[e])
        ax.bar_label(barras, fmt="%.1f s", padding=2, fontsize=8)
    ax.axhline(p.TIMEOUT_POSTO_S, ls="--", color="gray", label=f"Timeout do posto ({p.TIMEOUT_POSTO_S:.0f} s)")
    ax.set_xticks(list(xs), titulos)
    ax.set_ylabel("Tempo total da consulta (s)")
    ax.set_title("Experimento 5 — tempo de resposta sob falha")
    ax.legend()
    c.salvar_fig(fig, "exp_5_tempos")

    cores = {p.STATUS_SUCESSO: "#009E73", p.STATUS_INDISPONIVEL: "#D55E00", p.STATUS_TIMEOUT: "#E69F00",
             p.STATUS_NAO_ATENDIDA: "#999999", p.STATUS_ERRO: "#CC79A7"}
    fig, ax = plt.subplots(figsize=(9, 4.8))
    base = [0] * len(cens)
    contagens = []
    for cn in cens:
        resp = por[(cn, p.ESTRATEGIA_CONCORRENTE)]["resposta"]
        ct = Counter(r["status"] for r in resp["resultados"]) + Counter(r["status"] for r in resp["indisponiveis"])
        contagens.append(ct)
    for status, cor in cores.items():
        vals = [ct.get(status, 0) for ct in contagens]
        if not any(vals):
            continue
        ax.bar(titulos, vals, bottom=base, color=cor, label=status)
        base = [b + v for b, v in zip(base, vals)]
    ax.set_ylabel("Postos (de 4)")
    ax.set_yticks(range(0, 5))
    ax.set_title("Experimento 5 — resposta dos postos por status (concorrente)")
    ax.legend()
    c.salvar_fig(fig, "exp_5_status")


def main() -> None:
    ap = c.parser_base("Experimento 5 — indisponibilidade de um posto.")
    args = ap.parse_args()
    c.validar_dados(args.cidade, args.combustivel)

    resultados = []
    for cen in CENARIOS:
        for e in ESTRATEGIAS:
            print(f">>> {CENARIOS[cen][0]} — {e} …")
            r = executar(cen, e, args.cidade, args.combustivel)
            resultados.append(r)
            print(f"    {r['tempo_cliente_ms']} ms — {'OK' if r['aprovado'] else 'FALHOU: ' + '; '.join(r['problemas'])}")

    linhas = []
    for r in resultados:
        ind = ", ".join(f"{i['posto']}={i['status']}" for i in r["resposta"]["indisponiveis"]) or "—"
        linhas.append([r["titulo"], r["estrategia"], r["tempo_cliente_ms"], ind,
                       r["resposta"]["menor_preco"] and r["resposta"]["menor_preco"]["posto"],
                       "PASS" if r["aprovado"] else "FAIL"])
    print("\n" + c.tabela(["cenário", "estratégia", "tempo (ms)", "indisponíveis", "menor", "resultado"], linhas))

    c.salvar_json("exp_5_indisponibilidade", {"cidade": args.cidade, "combustivel": args.combustivel,
                                              "resultados": resultados})
    graficos(resultados)
    if not all(r["aprovado"] for r in resultados):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
