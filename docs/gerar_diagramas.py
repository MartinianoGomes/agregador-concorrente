"""Gera os 3 diagramas de modelagem em PNG (300 dpi) na pasta docs/.

  diagrama_casos_de_uso.png
  diagrama_arquitetura.png
  diagrama_sequencia.png

    python docs/gerar_diagramas.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch, Rectangle

SAIDA = Path(__file__).resolve().parent
AZUL, LARANJA, VERDE, CINZA = "#0072B2", "#D55E00", "#009E73", "#555555"
plt.rcParams.update({"font.size": 10, "savefig.dpi": 300})


def novo(w: float, h: float, xlim: tuple[float, float], ylim: tuple[float, float]):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


def caixa(ax, x, y, w, h, texto, fc="#FFFFFF", ec="#222222", lw=1.3, fs=9.5, bold=False, z=2):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fc, ec=ec, lw=lw, zorder=z))
    ax.text(x + w / 2, y + h / 2, texto, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=z + 1)


def seta(ax, p1, p2, texto="", estilo="-|>", ls="-", cor="#222222", patchA=None, patchB=None,
         dy=0.12, fs=8.5, lw=1.3, rad=0.0, ha="center"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=estilo, mutation_scale=12, lw=lw, ls=ls,
                                 color=cor, patchA=patchA, patchB=patchB, shrinkA=0, shrinkB=0,
                                 connectionstyle=f"arc3,rad={rad}", zorder=1))
    if texto:
        ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2 + dy, texto, ha=ha, va="bottom",
                fontsize=fs, color=cor, zorder=5,
                bbox=dict(fc="white", ec="none", pad=0.6, alpha=0.9))


def ator(ax, x, y, nome):
    ax.add_patch(plt.Circle((x, y + 0.75), 0.17, fc="white", ec="#222222", lw=1.4, zorder=3))
    for (a, b) in [((x, y + 0.58), (x, y + 0.1)), ((x - 0.3, y + 0.42), (x + 0.3, y + 0.42)),
                   ((x, y + 0.1), (x - 0.25, y - 0.3)), ((x, y + 0.1), (x + 0.25, y - 0.3))]:
        ax.plot([a[0], b[0]], [a[1], b[1]], color="#222222", lw=1.4, zorder=3)
    ax.text(x, y - 0.5, nome, ha="center", va="top", fontsize=9.5, fontweight="bold")
    return (x, y + 0.3)


# --------------------------------------------------------------- casos de uso
def casos_de_uso() -> None:
    fig, ax = novo(11, 7.2, (0, 12.2), (0, 8))
    ax.add_patch(Rectangle((3.0, 0.25), 6.6, 7.5, fc="#F7F9FB", ec="#222222", lw=1.3, zorder=0))
    ax.text(6.3, 7.45, "Sistema Agregador de Preços de Combustíveis", ha="center", va="center",
            fontsize=10.5, fontweight="bold")

    def uc(x, y, texto):
        e = Ellipse((x, y), 2.5, 1.05, fc="white", ec=AZUL, lw=1.5, zorder=2)
        ax.add_patch(e)
        ax.text(x, y, texto, ha="center", va="center", fontsize=8.8, zorder=3)
        return e

    u1 = uc(4.4, 6.4, "Consultar preços\n(modo sequencial)")
    u2 = uc(4.4, 4.9, "Consultar preços\n(modo concorrente)")
    u4 = uc(4.4, 3.4, "Visualizar ranking e\nmenor preço")
    u5 = uc(4.4, 1.9, "Visualizar tempo\nde execução")
    u3 = uc(8.0, 5.65, "Consultar postos\nindependentes")
    u6 = uc(8.0, 3.85, "Tratar falhas de posto\n(timeout / indisponível)")
    u7 = uc(8.0, 2.3, "Executar\nexperimentos")
    u8 = uc(8.0, 0.95, "Gerar gráficos\ne tabelas")

    usuario = ator(ax, 1.3, 3.4, "Usuário")
    posto = ator(ax, 11.0, 5.3, "Posto de\ncombustível")
    operador = ator(ax, 11.0, 1.7, "Operador\n(experimentos)")

    for e, y in [(u1, 6.4), (u2, 4.9), (u4, 3.4), (u5, 1.9)]:
        seta(ax, usuario, (e.center[0], y), estilo="-", patchB=e)
    seta(ax, posto, (8.0, 5.65), estilo="-", patchB=u3)
    seta(ax, operador, (8.0, 2.3), estilo="-", patchB=u7)

    seta(ax, (4.4, 6.4), (8.0, 5.65), "«include»", ls="--", patchA=u1, patchB=u3, cor=CINZA, dy=0.1, fs=7.8)
    seta(ax, (4.4, 4.9), (8.0, 5.65), "«include»", ls="--", patchA=u2, patchB=u3, cor=CINZA, dy=-0.35, fs=7.8)
    seta(ax, (8.0, 3.85), (8.0, 5.65), "«extend»", ls="--", patchA=u6, patchB=u3, cor=CINZA, dy=-0.15)
    seta(ax, (8.0, 2.3), (8.0, 0.95), "«include»", ls="--", patchA=u7, patchB=u8, cor=CINZA, dy=-0.05)

    fig.tight_layout()
    fig.savefig(SAIDA / "diagrama_casos_de_uso.png")
    plt.close(fig)


# ------------------------------------------------------------------ arquitetura
def arquitetura() -> None:
    fig, ax = novo(11.5, 6.6, (0, 15), (0, 8.6))

    # Clientes
    for i, y in enumerate([5.6, 4.0, 2.4]):
        caixa(ax, 0.3, y, 2.6, 1.0, "Cliente CLI\n(src/cliente.py)" if i == 0 else
              ("Cliente CLI" if i == 1 else "Cliente CLI (N)"), fc="#E8F1FA", ec=AZUL)
    ax.text(1.6, 7.0, "Clientes", ha="center", fontweight="bold", color=AZUL)

    # Agregador
    ax.add_patch(FancyBboxPatch((4.6, 1.5), 4.6, 5.9, boxstyle="round,pad=0.02,rounding_size=0.15",
                                fc="#FDF1E7", ec=LARANJA, lw=1.8, zorder=1))
    ax.text(6.9, 7.1, "Agregador — porta 5000 (src/agregador.py)", ha="center", fontweight="bold",
            color=LARANJA, fontsize=9.5)
    caixa(ax, 4.9, 5.4, 4.0, 1.2, "Receptor\n1 thread por cliente\nvalida a requisição", fs=9)
    caixa(ax, 4.9, 3.5, 4.0, 1.5, "Despachante\nsequencial: um posto após o outro\n"
          "concorrente: ThreadPoolExecutor\n(1 thread por posto, timeout 5 s)", fs=8.6)
    caixa(ax, 4.9, 1.8, 4.0, 1.2, "Consolidador\nranking por preço, menor preço,\ntempo_ms, indisponíveis", fs=8.8)

    # Postos
    ax.text(12.6, 7.55, "Postos independentes\n(processos separados)", ha="center", fontweight="bold",
            color=VERDE)
    for i, (nome, porta, y) in enumerate([("A", 6001, 5.85), ("B", 6002, 4.45), ("C", 6003, 3.05),
                                           ("D", 6004, 1.65)]):
        caixa(ax, 10.6, y, 4.0, 1.15, f"Posto {nome} — porta {porta}\nbase em memória\n(CSV ANP recorte {nome})",
              fc="#E6F5EF", ec=VERDE, fs=8.8)

    # Setas cliente -> agregador
    for y in (6.1, 4.5, 2.9):
        seta(ax, (2.9, y), (4.9 if y == 6.1 else 4.6, 6.0 if y == 6.1 else y), estilo="<|-|>", cor="#222222")
    ax.text(3.75, 6.75, "TCP / JSON\n(1 requisição, 1 resposta)", ha="center", fontsize=8, color=CINZA)

    # Setas agregador -> postos
    for y in (6.425, 5.025, 3.625, 2.225):
        seta(ax, (9.2, y), (10.6, y), estilo="<|-|>", cor="#222222")
    ax.text(9.9, 6.7, "TCP / JSON", ha="center", fontsize=8, color=CINZA)

    # Pipeline de dados
    caixa(ax, 0.3, 0.1, 3.4, 0.9, "data/anp_bruto.csv\n(1º sem. 2026, 422 mil linhas)", fc="#F2F2F2", fs=8.2)
    caixa(ax, 4.3, 0.1, 3.9, 0.9, "scripts/preparar_csvs.py\nfiltro Norte + hash(CNPJ) mod 4", fc="#F2F2F2", fs=8.2)
    caixa(ax, 8.8, 0.1, 3.4, 0.9, "data/anp_posto_{a..d}.csv", fc="#F2F2F2", fs=8.2)
    seta(ax, (3.7, 0.55), (4.3, 0.55), cor=CINZA)
    seta(ax, (8.2, 0.55), (8.8, 0.55), cor=CINZA)
    seta(ax, (12.2, 0.55), (13.5, 1.65), "carregados na\ninicialização", cor=CINZA, dy=0.0, fs=7.8, rad=-0.15)

    fig.tight_layout()
    fig.savefig(SAIDA / "diagrama_arquitetura.png")
    plt.close(fig)


# -------------------------------------------------------------------- sequência
def sequencia() -> None:
    fig, ax = novo(11.5, 9.2, (0, 15.5), (0, 12.4))
    vidas = [("Usuário", 1.0), ("Cliente", 3.1), ("Agregador", 6.2), ("Posto A", 9.2),
             ("Posto B", 11.0), ("Posto C", 12.8), ("Posto D", 14.6)]
    topo, base = 11.6, 0.4
    for nome, x in vidas:
        caixa(ax, x - 0.8, topo, 1.6, 0.6, nome, fc="#E8F1FA", ec=AZUL, fs=9, bold=True)
        ax.plot([x, x], [topo, base], color="#999999", lw=1, ls=(0, (5, 4)), zorder=0)
    X = dict(vidas)

    def msg(x1, x2, y, texto, ls="-", cor="#222222", dy=0.08):
        seta(ax, (X[x1], y), (X[x2], y), texto, ls=ls, cor=cor, dy=dy, fs=8.3)

    def auto(x, y, texto):
        ax.add_patch(Rectangle((X[x] - 0.12, y - 0.55), 0.24, 0.55, fc="#FDF1E7", ec=LARANJA, zorder=2))
        ax.text(X[x] + 0.28, y - 0.27, texto, fontsize=8.3, va="center", color=LARANJA)

    msg("Usuário", "Cliente", 10.9, "informa cidade, combustível\ne estratégia", dy=0.05)
    msg("Cliente", "Agregador", 10.0, "consultar {combustivel, cidade, estrategia}", dy=0.05)
    auto("Agregador", 9.6, "valida requisição e inicia cronômetro")

    # fragmento par (concorrente)
    ax.add_patch(Rectangle((5.0, 3.6), 10.2, 5.4, fc="none", ec="#222222", lw=1.2, zorder=3))
    ax.add_patch(Rectangle((5.0, 8.6), 3.4, 0.4, fc="#EEEEEE", ec="#222222", lw=1.2, zorder=3))
    ax.text(5.1, 8.8, "par  [estratégia = concorrente]", fontsize=8.5, va="center", fontweight="bold", zorder=4)
    ax.text(5.15, 8.25, "uma thread por posto; no modo sequencial, um posto após o outro",
            fontsize=7.8, style="italic", color=CINZA)

    ys = {"Posto A": 7.6, "Posto B": 7.2, "Posto C": 6.8, "Posto D": 6.4}
    for p_, y in ys.items():
        msg("Agregador", p_, y, "consultar" if p_ == "Posto A" else "", dy=0.04)
    ax.text(X["Posto A"] + 0.15, 7.95, "", fontsize=8)
    for p_, y in {"Posto A": 5.5, "Posto B": 5.1, "Posto C": 4.7, "Posto D": 4.3}.items():
        msg(p_, "Agregador", y, "{preço, status}" if p_ == "Posto A" else "", ls="--", dy=0.04)

    ax.add_patch(Rectangle((7.0, 3.75), 5.2, 0.45, fc="#FFF8E1", ec="#E69F00", zorder=4))
    ax.text(9.6, 3.975, "falha / timeout de 5 s  →  status indisponivel ou timeout",
            ha="center", va="center", fontsize=7.8, zorder=5)

    auto("Agregador", 3.2, "consolida: ordena por preço, define menor_preco,\nmede tempo_ms")
    msg("Agregador", "Cliente", 1.9, "{resultados, indisponiveis, menor_preco, tempo_ms}", ls="--", dy=0.05)
    msg("Cliente", "Usuário", 1.0, "exibe ranking, menor preço e tempo", ls="--", dy=0.05)

    fig.tight_layout()
    fig.savefig(SAIDA / "diagrama_sequencia.png")
    plt.close(fig)


if __name__ == "__main__":
    casos_de_uso()
    arquitetura()
    sequencia()
    print("diagramas gerados em", SAIDA)
