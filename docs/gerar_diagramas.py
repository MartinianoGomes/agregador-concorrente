"""Gera os diagramas UML do projeto em PNG na pasta docs/.

  diagrama_casos_de_uso.png
  diagrama_componentes.png
  diagrama_sequencia.png

    python docs/gerar_diagramas.py
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Ellipse, FancyArrowPatch, Polygon, Rectangle

SAIDA = Path(__file__).resolve().parent
DPI = 250

TINTA = "#1F2328"
SUAVE = "#57606A"
BORDA = "#3D4752"
FUNDO_SISTEMA = "#F6F8FA"
AZUL, AZUL_CLARO = "#0969DA", "#DDF4FF"
LARANJA, LARANJA_CLARO = "#BC4C00", "#FFF1E5"
VERDE, VERDE_CLARO = "#1A7F37", "#DAFBE1"
ROXO, ROXO_CLARO = "#8250DF", "#FBEFFF"
CINZA_CLARO = "#EAEEF2"
NOTA, NOTA_BORDA = "#FFF8C5", "#BF8700"
TRACO = (0, (5, 3.5))

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})


# =====================================================================
# Primitivas de desenho
# =====================================================================
def tela(largura: float, altura: float, polegadas: float):
    """Área de desenho em que 1 unidade vale o mesmo em x e y."""
    fig = plt.figure(figsize=(polegadas, polegadas * altura / largura))
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, largura)
    ax.set_ylim(0, altura)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax


def salvar(fig, nome: str) -> None:
    fig.savefig(SAIDA / nome, dpi=DPI, facecolor="white")
    plt.close(fig)
    print("  ", SAIDA / nome)


def texto(ax, x, y, s, tam=11, cor=TINTA, negrito=False, italico=False, ha="center", va="center",
          fundo=None, z=6):
    extra = {"bbox": dict(fc=fundo, ec="none", pad=1.5)} if fundo else {}
    ax.text(x, y, s, fontsize=tam, color=cor, ha=ha, va=va, zorder=z, linespacing=1.3,
            fontweight="bold" if negrito else "normal",
            fontstyle="italic" if italico else "normal", **extra)


def linha(ax, pontos, tracejada=False, cor=TINTA, lw=1.4, z=2):
    xs, ys = zip(*pontos)
    ax.plot(xs, ys, color=cor, lw=lw, ls=TRACO if tracejada else "-", zorder=z,
            solid_capstyle="butt")


def seta(ax, pontos, ponta="cheia", tracejada=False, cor=TINTA, lw=1.4, z=3):
    """Polilinha com ponta no último ponto. 'cheia' = mensagem síncrona; 'aberta' = retorno/dependência."""
    if len(pontos) > 2:
        linha(ax, pontos[:-1], tracejada, cor, lw, z)
    ax.add_patch(FancyArrowPatch(pontos[-2], pontos[-1], arrowstyle="-|>" if ponta == "cheia" else "->",
                                 mutation_scale=16, lw=lw, color=cor, ls=TRACO if tracejada else "-",
                                 shrinkA=0, shrinkB=0, zorder=z))


def retangulo(ax, x, y, w, h, fc="white", ec=BORDA, lw=1.5, z=2):
    ax.add_patch(Rectangle((x, y), w, h, fc=fc, ec=ec, lw=lw, zorder=z))


def nota(ax, x, y, w, h, s, tam=10.5):
    """Nota UML (canto dobrado)."""
    d = 0.3
    ax.add_patch(Polygon([(x, y), (x + w, y), (x + w, y + h - d), (x + w - d, y + h), (x, y + h)],
                         closed=True, fc=NOTA, ec=NOTA_BORDA, lw=1.3, zorder=4))
    linha(ax, [(x + w - d, y + h), (x + w - d, y + h - d), (x + w, y + h - d)], cor=NOTA_BORDA,
          lw=1.1, z=5)
    texto(ax, x + 0.25, y + h / 2, s, tam=tam, ha="left")


# =====================================================================
# 1. Casos de uso
# =====================================================================
def casos_de_uso() -> None:
    fig, ax = tela(21.4, 11.8, polegadas=12.5)
    W, H = 3.75, 1.4

    def ator(x, y, nome):
        ax.add_patch(Circle((x, y + 1.0), 0.28, fc="white", ec=TINTA, lw=1.6, zorder=4))
        for a, b in [((x, y + 0.72), (x, y - 0.1)), ((x - 0.5, y + 0.45), (x + 0.5, y + 0.45)),
                     ((x, y - 0.1), (x - 0.42, y - 0.75)), ((x, y - 0.1), (x + 0.42, y - 0.75))]:
            linha(ax, [a, b], lw=1.6, z=4)
        texto(ax, x, y - 1.05, nome, tam=12, negrito=True, va="top")
        return x, y + 0.35

    def caso(x, y, nome, cor=AZUL):
        ax.add_patch(Ellipse((x, y), W, H, fc="white", ec=cor, lw=1.8, zorder=3))
        texto(ax, x, y, nome, tam=11.5)
        return x, y

    def borda(c, alvo):
        """Ponto na borda da elipse centrada em `c`, na direção de `alvo`."""
        dx, dy = alvo[0] - c[0], alvo[1] - c[1]
        t = 1 / math.hypot(dx / (W / 2), dy / (H / 2))
        return c[0] + dx * t, c[1] + dy * t

    def associar(a, c):
        linha(ax, [a, borda(c, a)], lw=1.5, z=2)

    def relacao(origem, destino, rotulo):
        p1, p2 = borda(origem, destino), borda(destino, origem)
        seta(ax, [p1, p2], ponta="aberta", tracejada=True, cor=SUAVE)
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        if math.dist(p1, p2) >= 1.8:  # seta longa: rótulo sobre a linha
            texto(ax, mx, my, rotulo, tam=10, cor=SUAVE, fundo=FUNDO_SISTEMA)
        elif abs(p2[0] - p1[0]) > abs(p2[1] - p1[1]):  # curta e horizontal: acima
            texto(ax, mx, my + 0.12, rotulo, tam=10, cor=SUAVE, va="bottom")
        else:  # curta e vertical: à direita
            texto(ax, mx + 0.15, my, rotulo, tam=10, cor=SUAVE, ha="left")

    retangulo(ax, 3.05, 0.3, 15.25, 11.1, fc=FUNDO_SISTEMA, ec=BORDA, lw=1.5, z=0)
    texto(ax, 10.67, 10.95, "Agregador de Preços de Combustíveis", tam=13.5, negrito=True)

    L, M, R = 5.25, 10.55, 16.0
    consultar = caso(L, 7.6, "Consultar preços")
    ver = caso(L, 4.0, "Ver ranking,\nmenor preço e tempo")
    local = caso(M, 9.45, "Informar estado (UF)\ne município")
    escolher = caso(M, 7.6, "Escolher combustível\ne estratégia")
    postos = caso(M, 5.75, "Consultar os\n4 postos")
    falha = caso(M, 3.25, "Tratar falha de posto\n(timeout, fora do ar)")
    rejeitar = caso(R, 9.45, "Rejeitar consulta\ninválida")
    graficos = caso(M, 1.15, "Gerar gráficos\ne tabelas", cor=ROXO)
    experimentos = caso(R, 3.25, "Executar\nexperimentos", cor=ROXO)
    preparar = caso(R, 1.15, "Preparar dados\nda ANP", cor=ROXO)

    usuario = ator(1.4, 5.9, "Usuário")
    posto = ator(20.1, 5.4, "Posto de\ncombustível")
    operador = ator(20.1, 1.8, "Operador")

    associar(usuario, consultar)
    associar(usuario, ver)
    associar(posto, postos)
    associar(operador, experimentos)
    associar(operador, preparar)

    relacao(consultar, local, "«include»")
    relacao(consultar, escolher, "«include»")
    relacao(consultar, postos, "«include»")
    relacao(rejeitar, local, "«extend»")
    relacao(falha, postos, "«extend»")
    relacao(experimentos, graficos, "«include»")

    nota(ax, R - 1.85, 6.85, 3.7, 1.15, "UF fora da Região Norte ou\ncombustível desconhecido",
         tam=10)
    linha(ax, [(R, 6.85 + 1.15), (R, 9.45 - H / 2)], tracejada=True, cor=NOTA_BORDA, lw=1.1)
    salvar(fig, "diagrama_casos_de_uso.png")


# =====================================================================
# 2. Componentes
# =====================================================================
def componentes() -> None:
    fig, ax = tela(19.4, 12.6, polegadas=12.5)

    def icone(x, y, cor):
        """Ícone UML de componente com canto superior direito em (x, y)."""
        retangulo(ax, x - 0.42, y - 0.5, 0.36, 0.4, fc="white", ec=cor, lw=1.2, z=5)
        for dy in (0.17, 0.33):
            retangulo(ax, x - 0.5, y - dy - 0.04, 0.16, 0.09, fc="white", ec=cor, lw=1.1, z=6)

    def componente(x, y, w, h, nome, detalhe="", cor=AZUL, fc=AZUL_CLARO, tipo="component",
                   nome_no_topo=False):
        retangulo(ax, x, y, w, h, fc=fc, ec=cor, lw=1.8, z=2)
        icone(x + w - 0.12, y + h - 0.12, cor)
        if nome_no_topo:
            yt = y + h - 0.42
        else:  # centraliza o bloco estereótipo + nome + detalhe na caixa
            n = detalhe.count("\n") + 1 if detalhe else 0
            yt = y + h / 2 + (0.335 + 0.165 * n if detalhe else 0.18)
        texto(ax, x + w / 2, yt, f"«{tipo}»", tam=9.5, cor=SUAVE)
        texto(ax, x + w / 2, yt - 0.4, nome, tam=12.5, negrito=True)
        if detalhe and not nome_no_topo:
            texto(ax, x + w / 2, yt - 0.82, detalhe, tam=10.5, va="top")

    def artefato(x, y, w, h, nome, detalhe):
        d = 0.32
        ax.add_patch(Polygon([(x, y), (x + w, y), (x + w, y + h - d), (x + w - d, y + h), (x, y + h)],
                             closed=True, fc=CINZA_CLARO, ec=BORDA, lw=1.4, zorder=2))
        linha(ax, [(x + w - d, y + h), (x + w - d, y + h - d), (x + w, y + h - d)], cor=BORDA, lw=1.2)
        texto(ax, x + w / 2, y + h - 0.32, "«artifact»", tam=9.5, cor=SUAVE)
        texto(ax, x + w / 2, y + h / 2 - 0.08, nome, tam=11, negrito=True)
        texto(ax, x + w / 2, y + 0.3, detalhe, tam=10, cor=SUAVE)

    def interface(x, y, provedor_x, consumidor_x, nome, protocolo):
        """Pirulito (interface fornecida) + soquete (interface requerida)."""
        r, rs = 0.2, 0.36
        lado = 1 if provedor_x > x else -1
        linha(ax, [(x + lado * r, y), (provedor_x, y)], lw=1.5)
        ax.add_patch(Circle((x, y), r, fc="white", ec=TINTA, lw=1.6, zorder=5))
        t1, t2 = (105, 255) if lado > 0 else (-75, 75)
        ax.add_patch(Arc((x, y), 2 * rs, 2 * rs, theta1=t1, theta2=t2, color=TINTA, lw=1.6, zorder=5))
        linha(ax, [(consumidor_x, y), (x - lado * rs, y)], lw=1.5)
        texto(ax, x, y + 0.65, nome, tam=11, negrito=True)
        texto(ax, x, y - 0.62, protocolo, tam=9.5, cor=SUAVE)

    def dependencia(pontos, rotulo, pos, ha="center", va="center", fundo="white"):
        seta(ax, pontos, ponta="aberta", tracejada=True, cor=SUAVE)
        texto(ax, pos[0], pos[1], rotulo, tam=10, cor=SUAVE, ha=ha, va=va, fundo=fundo)

    # Experimentos e Cliente
    componente(0.4, 9.6, 4.3, 1.9, "Experimentos", "experimentos/ (exp. 1 a 5)", cor=ROXO,
               fc=ROXO_CLARO)
    componente(0.4, 5.2, 4.3, 2.75, "Cliente CLI",
               "src/cliente.py\npede UF, município,\ncombustível e estratégia")

    # Agregador e suas partes internas
    ax0, ay0, aw, ah = 7.1, 4.5, 5.1, 7.0
    componente(ax0, ay0, aw, ah, "Agregador", cor=LARANJA, fc=LARANJA_CLARO, nome_no_topo=True)
    texto(ax, ax0 + aw / 2, ay0 + ah - 1.2, "src/agregador.py · porta 5000", tam=10.5, cor=SUAVE)
    partes = [(8.55, "Recepção", "1 thread por cliente;\nvalida a requisição e o id"),
              (6.85, "Despacho", "sequencial ou concorrente;\ntimeout de 5 s por posto"),
              (5.15, "Consolidação", "ranking, menor preço,\nindisponíveis, tempo_ms")]
    for y, nome, desc in partes:
        retangulo(ax, ax0 + 0.35, y - 0.4, aw - 0.7, 1.35, fc="white", ec=LARANJA, lw=1.2, z=3)
        texto(ax, ax0 + aw / 2, y + 0.65, nome, tam=11, negrito=True)
        texto(ax, ax0 + aw / 2, y + 0.08, desc, tam=10)
    for y_de, y_para in ((8.55 - 0.4, 6.85 + 0.95), (6.85 - 0.4, 5.15 + 0.95)):
        seta(ax, [(ax0 + aw / 2, y_de), (ax0 + aw / 2, y_para)], cor=LARANJA, lw=1.2)

    # Posto: 4 instâncias empilhadas
    px, py, pw, ph = 14.6, 6.2, 4.3, 2.75
    for k in (2, 1):
        retangulo(ax, px + 0.18 * k, py - 0.18 * k, pw, ph, fc=VERDE_CLARO, ec=VERDE, lw=1.4, z=1)
    componente(px, py, pw, ph, "Posto", "src/posto.py\n4 processos: A, B, C, D\nportas 6001 a 6004",
               cor=VERDE, fc=VERDE_CLARO)

    # Interfaces
    interface(5.9, 6.6, ax0, 4.7, "IConsulta", "JSON / TCP")
    interface(13.4, 7.6, px, ax0 + aw, "IPosto", "JSON / TCP")

    # Biblioteca comum
    componente(ax0, 1.9, aw, 1.95, "protocolo.py", "mensagens JSON, validação\ne rastreio",
               tipo="library", cor=BORDA, fc=CINZA_CLARO)

    # Dependências
    dependencia([(2.55, 9.6), (2.55, 7.8)], "«use»", (2.55, 8.7))
    dependencia([(4.7, 10.3), (ax0, 10.3)], "«create»\ninicia os processos", (5.9, 10.45),
                va="bottom", fundo=None)
    dependencia([(ax0 + aw / 2, ay0), (ax0 + aw / 2, 3.7)], "«use»", (ax0 + aw / 2 + 0.2, 4.1),
                ha="left", fundo=None)
    dependencia([(2.55, 5.4), (2.55, 2.75), (ax0, 2.75)], "«use»", (2.55, 4.1))
    dependencia([(px + 0.8, py - 0.36), (px + 0.8, 2.75), (ax0 + aw, 2.75)], "«use»", (px + 0.8, 4.1))

    # Dados
    artefato(0.4, 0.15, 4.3, 1.4, "anp_bruto.csv", "série histórica da ANP")
    componente(ax0, 0.15, aw, 1.4, "preparar_csvs.py", "", tipo="script", cor=BORDA, fc="white")
    artefato(px, 0.15, pw, 1.4, "anp_posto_a…d.csv", "um recorte por posto")
    seta(ax, [(4.7, 0.85), (ax0, 0.85)], cor=SUAVE)
    seta(ax, [(ax0 + aw, 0.85), (px, 0.85)], cor=SUAVE)
    texto(ax, 5.9, 1.12, "lê", tam=10, cor=SUAVE)
    texto(ax, 13.4, 1.12, "gera", tam=10, cor=SUAVE)
    dependencia([(px + 3.6, 1.55), (px + 3.6, py - 0.36)], "carregado na\ninicialização",
                (px + 3.6, 4.1))

    salvar(fig, "diagrama_componentes.png")


# =====================================================================
# 3. Sequência
# =====================================================================
def sequencia() -> None:
    X = {"Usuário": 1.9, "Cliente": 5.6, "Agregador": 10.0, "Posto (A a D)": 15.3}
    LARG, TOPO = 18.0, 40.0  # desenha de cima para baixo; a altura final é recortada no fim
    fig, ax = tela(LARG, TOPO, polegadas=11.5)
    BARRA = 0.14  # meia largura das barras de ativação
    ativos = {"Agregador", "Posto (A a D)"}

    def msg(de, para, y, rotulo, retorno=False):
        x1, x2 = X[de], X[para]
        sentido = 1 if x2 > x1 else -1
        if de in ativos:
            x1 += sentido * BARRA
        if para in ativos:
            x2 -= sentido * BARRA
        seta(ax, [(x1, y), (x2, y)], ponta="aberta" if retorno else "cheia", tracejada=retorno)
        texto(ax, (x1 + x2) / 2, y + 0.12, rotulo, tam=11, va="bottom")

    def propria(quem, y, rotulo):
        x = X[quem] + BARRA
        seta(ax, [(x, y), (x + 0.8, y), (x + 0.8, y - 0.5), (x + 0.03, y - 0.5)])
        texto(ax, x + 1.0, y - 0.25, rotulo, tam=11, ha="left", fundo="white")

    def fragmento(x1, x2, y_topo, y_base, operador, guarda="", descricao=""):
        retangulo(ax, x1, y_base, x2 - x1, y_topo - y_base, fc="none", ec=TINTA, lw=1.4, z=4)
        larg = 0.35 + 0.17 * len(operador)
        ax.add_patch(Polygon([(x1, y_topo), (x1 + larg, y_topo), (x1 + larg, y_topo - 0.32),
                              (x1 + larg - 0.2, y_topo - 0.52), (x1, y_topo - 0.52)],
                             closed=True, fc=CINZA_CLARO, ec=TINTA, lw=1.4, zorder=5))
        texto(ax, x1 + 0.13, y_topo - 0.26, operador, tam=11, negrito=True, ha="left")
        if guarda:
            texto(ax, x1 + larg + 0.15, y_topo - 0.26, guarda, tam=11, ha="left", cor=SUAVE,
                  fundo="white")
        if descricao:
            texto(ax, x2 - 0.2, y_topo - 0.26, descricao, tam=10.5, ha="right", cor=SUAVE,
                  italico=True, fundo="white")

    def separador(x1, x2, y, guarda):
        linha(ax, [(x1, y), (x2, y)], tracejada=True, lw=1.2, z=4)
        texto(ax, x1 + 0.2, y - 0.32, guarda, tam=11, ha="left", cor=SUAVE, fundo="white")

    def ativacao(quem, y_topo, y_base, cor=LARANJA, fc=LARANJA_CLARO):
        retangulo(ax, X[quem] - BARRA, y_base, 2 * BARRA, y_topo - y_base, fc=fc, ec=cor, lw=1.2, z=3)

    # Cabeçalhos
    y_cab = TOPO - 0.3
    for nome, x in X.items():
        cor, fc = (VERDE, VERDE_CLARO) if nome.startswith("Posto") else (AZUL, AZUL_CLARO)
        retangulo(ax, x - 1.45, y_cab - 0.9, 2.9, 0.9, fc=fc, ec=cor, lw=1.6, z=6)
        texto(ax, x, y_cab - 0.45, nome, tam=12, negrito=True, z=7)

    y = y_cab - 0.9 - 1.3
    msg("Usuário", "Cliente", y, "estado, município,\ncombustível, estratégia")
    y -= 1.6
    y_ini_ag = y
    msg("Cliente", "Agregador", y, "consultar(id, estado, cidade,\ncombustivel, estrategia)")
    texto(ax, X["Cliente"] - 0.2, y - 0.4, "gera o id\nde rastreio", tam=9.5, cor=SUAVE,
          italico=True, ha="right")
    y -= 0.55
    propria("Agregador", y, "validar requisição")

    # alt externo: requisição inválida × válida
    a1, a2 = 0.3, LARG - 0.3
    topo_alt = y - 0.95
    y = topo_alt - 1.25
    msg("Agregador", "Cliente", y, "erro, mensagem, id", retorno=True)
    y -= 1.0
    msg("Cliente", "Usuário", y, "mostra o erro", retorno=True)
    y -= 0.6
    separador(a1, a2, y, "[requisição válida]")

    # alt interno: concorrente × sequencial
    b1, b2 = 6.4, LARG - 0.6
    topo_alt2 = y - 0.85

    def bloco(y_topo, operador, descricao):
        fragmento(b1 + 0.35, b2 - 0.35, y_topo, y_topo - 2.1, operador, descricao=descricao)
        ativacao("Posto (A a D)", y_topo - 1.0, y_topo - 1.7, VERDE, VERDE_CLARO)
        msg("Agregador", "Posto (A a D)", y_topo - 1.0, "consultar(id, estado, cidade, combustivel)")
        msg("Posto (A a D)", "Agregador", y_topo - 1.7, "status, preço, id", retorno=True)
        return y_topo - 2.1

    fim_par = bloco(topo_alt2 - 0.75, "par", "uma thread por posto, todas ao mesmo tempo")
    y_sep = fim_par - 0.35
    separador(b1, b2, y_sep, "[sequencial]")
    fim_loop = bloco(y_sep - 0.7, "loop", "um posto de cada vez")
    base_alt2 = fim_loop - 0.35
    fragmento(b1, b2, topo_alt2, base_alt2, "alt", guarda="[concorrente]")

    # nota sobre falhas, ligada à linha de vida do posto
    nw, nh = 6.3, 1.55
    nx, ny = X["Posto (A a D)"] - nw + 1.3, base_alt2 - 0.45 - nh
    nota(ax, nx, ny, nw, nh, "sem resposta em 5 s  →  timeout\nposto fora do ar  →  indisponivel\n"
         "município fora da UF  →  nao_atendida")
    linha(ax, [(nx + nw / 2, ny + nh), (X["Posto (A a D)"], base_alt2 - 0.05)], tracejada=True,
          cor=NOTA_BORDA, lw=1.1, z=3)

    y = ny - 0.45
    propria("Agregador", y, "consolidar resultados")
    y -= 1.5
    msg("Agregador", "Cliente", y, "id, ranking, indisponíveis,\nmenor preço, tempo_ms", retorno=True)
    y_fim_ag = y
    y -= 1.35
    msg("Cliente", "Usuário", y, "mostra ranking,\ntempo e id", retorno=True)
    base_alt = y - 0.45
    fragmento(a1, a2, topo_alt, base_alt, "alt", guarda="[requisição inválida]")

    ativacao("Agregador", y_ini_ag, y_fim_ag)
    y_fim = base_alt - 0.45
    for x in X.values():
        linha(ax, [(x, y_cab - 0.9), (x, y_fim)], tracejada=True, cor="#8C959F", lw=1.1, z=0)

    # recorta a altura ao conteúdo, mantendo a escala
    base = y_fim - 0.25
    ax.set_ylim(base, TOPO)
    fig.set_size_inches(11.5, 11.5 * (TOPO - base) / LARG)
    salvar(fig, "diagrama_sequencia.png")


if __name__ == "__main__":
    print("Gerando diagramas:")
    casos_de_uso()
    componentes()
    sequencia()
