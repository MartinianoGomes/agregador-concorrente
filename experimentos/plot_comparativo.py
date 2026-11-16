"""Gráficos comparativos dos Experimentos 1 (sequencial) × 2 (concorrente).

Lê resultados/exp_1_sequencial.json e resultados/exp_2_concorrente.json e gera:
  - exp_12_barras.png   (média ± desvio padrão)
  - exp_12_rodadas.png  (tempo por rodada)
  - exp_12_boxplot.png  (distribuição)

    python -m experimentos.plot_comparativo
"""

from __future__ import annotations

import json

from experimentos import _comum as c
from src import protocolo as p

ARQUIVOS = {
    p.ESTRATEGIA_SEQUENCIAL: "exp_1_sequencial",
    p.ESTRATEGIA_CONCORRENTE: "exp_2_concorrente",
}


def main() -> None:
    dados = {}
    for estrategia, nome in ARQUIVOS.items():
        caminho = c.RESULTADOS / f"{nome}.json"
        if not caminho.exists():
            raise SystemExit(f"Falta {caminho.name}. Rode o experimento correspondente antes.")
        dados[estrategia] = json.loads(caminho.read_text(encoding="utf-8"))

    plt = c.pyplot()
    ests = list(ARQUIVOS)
    ref = dados[ests[0]]
    sub = f"{ref['combustivel']} em {ref['cidade']}, latência {ref.get('latencia_ms')} ms/posto"

    # 1) barras média ± desvio
    fig, ax = plt.subplots(figsize=(5.5, 4))
    medias = [dados[e]["estatisticas"]["media"] for e in ests]
    desvios = [dados[e]["estatisticas"]["desvio"] for e in ests]
    barras = ax.bar([c.ROTULO[e] for e in ests], medias, yerr=desvios, capsize=6,
                    color=[c.COR[e] for e in ests])
    ax.bar_label(barras, fmt="%.1f ms", padding=3)
    ax.set_ylabel("Tempo total (ms)")
    ax.set_title(f"Experimentos 1 × 2 — tempo médio\n{sub}", fontsize=10)
    c.salvar_fig(fig, "exp_12_barras")

    # 2) tempo por rodada
    fig, ax = plt.subplots(figsize=(7, 4))
    for e in ests:
        t = dados[e]["tempos_ms"]
        ax.plot(range(1, len(t) + 1), t, marker="o", color=c.COR[e], label=c.ROTULO[e])
    ax.set_xlabel("Rodada")
    ax.set_ylabel("Tempo total (ms)")
    ax.set_title(f"Experimentos 1 × 2 — tempo por rodada\n{sub}", fontsize=10)
    ax.legend()
    c.salvar_fig(fig, "exp_12_rodadas")

    # 3) boxplot
    fig, ax = plt.subplots(figsize=(5.5, 4))
    caixas = ax.boxplot([dados[e]["tempos_ms"] for e in ests], patch_artist=True,
                        tick_labels=[c.ROTULO[e] for e in ests])
    for caixa, e in zip(caixas["boxes"], ests):
        caixa.set_facecolor(c.COR[e])
        caixa.set_alpha(0.6)
    ax.set_ylabel("Tempo total (ms)")
    ax.set_title(f"Experimentos 1 × 2 — distribuição\n{sub}", fontsize=10)
    c.salvar_fig(fig, "exp_12_boxplot")


if __name__ == "__main__":
    main()
