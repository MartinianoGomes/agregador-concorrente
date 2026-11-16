"""Infraestrutura compartilhada pelos experimentos.

- `Ambiente`: sobe 4 postos + agregador como processos independentes (em portas
  alternativas, para não colidir com um `run_all` aberto) e derruba tudo ao sair.
- `AmbienteExterno`: usa um agregador já em execução (ex.: o do `run_all`).
- Estatísticas, tabelas em texto, gravação de JSON e helpers de gráfico.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable

from src import protocolo as p
from src.cliente import consultar as _consultar
from src.posto import carregar_base_precos

RAIZ = Path(__file__).resolve().parent.parent
DATA = RAIZ / "data"
RESULTADOS = RAIZ / "resultados"
LOGS = RESULTADOS / "logs"

HOST = "127.0.0.1"
PORTA_AGREGADOR = 7000
NOMES_POSTOS = ("A", "B", "C", "D")
PORTAS_POSTOS = {"A": 7001, "B": 7002, "C": 7003, "D": 7004}

CIDADE_PADRAO = "Belém"
COMBUSTIVEL_PADRAO = "gasolina_comum"

COR = {
    p.ESTRATEGIA_SEQUENCIAL: "#D55E00",
    p.ESTRATEGIA_CONCORRENTE: "#0072B2",
}
ROTULO = {
    p.ESTRATEGIA_SEQUENCIAL: "Sequencial",
    p.ESTRATEGIA_CONCORRENTE: "Concorrente",
}


# ---------------------------------------------------------------- argumentos
def parser_base(descricao: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=descricao)
    ap.add_argument("--cidade", default=CIDADE_PADRAO)
    ap.add_argument("--combustivel", default=COMBUSTIVEL_PADRAO, choices=p.COMBUSTIVEIS)
    return ap


def validar_dados(cidade: str, combustivel: str) -> None:
    """Garante que os 4 recortes existem e que todos atendem (cidade, combustível).

    Sem isso um `nao_atendida` falsearia as medições.
    """
    chave = (p.normalizar_cidade(cidade), combustivel)
    for nome in NOMES_POSTOS:
        csv_path = DATA / f"anp_posto_{nome.lower()}.csv"
        if not csv_path.exists():
            raise SystemExit(
                f"CSV ausente: {csv_path}\nRode antes: python scripts/preparar_csvs.py "
                "--entrada data/anp_bruto.csv --saida data/"
            )
        if chave not in carregar_base_precos(csv_path):
            raise SystemExit(
                f"O posto {nome} não atende {cidade!r}/{combustivel}. "
                "Escolha outra combinação com --cidade/--combustivel."
            )


# ------------------------------------------------------------------ ambiente
def _porta_aberta(porta: int) -> bool:
    try:
        with socket.create_connection((HOST, porta), timeout=0.3):
            return True
    except OSError:
        return False


class Ambiente:
    """Postos + agregador como subprocessos. Use como context manager."""

    def __init__(
        self,
        latencia_ms: int | dict[str, int] = 0,
        ativos: Iterable[str] = NOMES_POSTOS,
        tag: str = "amb",
    ) -> None:
        if isinstance(latencia_ms, dict):
            self.latencias = {n: latencia_ms.get(n, 0) for n in NOMES_POSTOS}
        else:
            self.latencias = {n: latencia_ms for n in NOMES_POSTOS}
        self.ativos = list(ativos)
        self.tag = tag
        self.procs: dict[str, subprocess.Popen] = {}
        self._logs: list[Any] = []
        self.host = HOST
        self.porta = PORTA_AGREGADOR

    # -- ciclo de vida
    def __enter__(self) -> "Ambiente":
        LOGS.mkdir(parents=True, exist_ok=True)
        try:
            for porta in (PORTA_AGREGADOR, *PORTAS_POSTOS.values()):
                if _porta_aberta(porta):
                    raise RuntimeError(
                        f"Porta {porta} já em uso — há processos de um experimento anterior?"
                    )
            for nome in self.ativos:
                self._subir(
                    nome,
                    [
                        "-m", "src.posto", "--nome", nome, "--host", HOST,
                        "--porta", str(PORTAS_POSTOS[nome]),
                        "--anp", str(DATA / f"anp_posto_{nome.lower()}.csv"),
                        "--latencia-ms", str(self.latencias[nome]),
                    ],
                )
            args = ["-m", "src.agregador", "--host", HOST, "--porta", str(PORTA_AGREGADOR)]
            for nome in NOMES_POSTOS:  # o agregador conhece os 4, mesmo se algum estiver fora
                args += ["--posto", f"{nome}:{HOST}:{PORTAS_POSTOS[nome]}"]
            self._subir("AGREGADOR", args)
            for nome in self.ativos:
                self._esperar(nome, PORTAS_POSTOS[nome])
            self._esperar("AGREGADOR", PORTA_AGREGADOR)
        except BaseException:
            self.parar()
            raise
        return self

    def __exit__(self, *exc: Any) -> None:
        self.parar()

    def _subir(self, nome: str, args: list[str]) -> None:
        log = open(LOGS / f"{self.tag}_{nome}.log", "w", encoding="utf-8")
        self._logs.append(log)
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        self.procs[nome] = subprocess.Popen(
            [sys.executable, "-u", *args], cwd=RAIZ, stdout=log, stderr=subprocess.STDOUT, env=env
        )

    def _esperar(self, nome: str, porta: int, timeout: float = 20.0) -> None:
        limite = time.monotonic() + timeout
        while time.monotonic() < limite:
            if self.procs[nome].poll() is not None:
                raise RuntimeError(
                    f"{nome} encerrou ao iniciar (veja {LOGS / f'{self.tag}_{nome}.log'})"
                )
            if _porta_aberta(porta):
                return
            time.sleep(0.1)
        raise RuntimeError(f"{nome} não abriu a porta {porta} em {timeout}s")

    def matar_posto(self, nome: str) -> None:
        proc = self.procs[nome]
        proc.terminate()
        proc.wait(timeout=5)

    def parar(self) -> None:
        for proc in self.procs.values():
            if proc.poll() is None:
                proc.terminate()
        for proc in self.procs.values():
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        for log in self._logs:
            log.close()
        self.procs.clear()
        self._logs.clear()

    # -- consulta
    def consultar(self, cidade: str, combustivel: str, estrategia: str) -> dict:
        return _consultar(self.host, self.porta, cidade, combustivel, estrategia)


class AmbienteExterno:
    """Aponta para um agregador já em execução (não sobe nem derruba nada)."""

    def __init__(self, host: str = "localhost", porta: int = 5000) -> None:
        self.host, self.porta = host, porta

    def __enter__(self) -> "AmbienteExterno":
        return self

    def __exit__(self, *exc: Any) -> None:
        pass

    def consultar(self, cidade: str, combustivel: str, estrategia: str) -> dict:
        return _consultar(self.host, self.porta, cidade, combustivel, estrategia)


# -------------------------------------------------------------- estatísticas
def estatisticas(valores: list[float]) -> dict[str, float]:
    n = len(valores)
    if n == 0:
        return {"n": 0, "media": 0.0, "desvio": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}
    ordenado = sorted(valores)
    return {
        "n": n,
        "media": round(statistics.fmean(valores), 2),
        "desvio": round(statistics.stdev(valores), 2) if n > 1 else 0.0,
        "min": round(ordenado[0], 2),
        "max": round(ordenado[-1], 2),
        "p95": round(ordenado[min(n - 1, math.ceil(0.95 * n) - 1)], 2),
    }


def tabela(cabecalho: list[str], linhas: list[list[Any]]) -> str:
    cols = [cabecalho, *[[str(c) for c in l] for l in linhas]]
    larg = [max(len(l[i]) for l in cols) for i in range(len(cabecalho))]
    fmt = lambda l: " | ".join(c.rjust(larg[i]) for i, c in enumerate(l))
    sep = "-+-".join("-" * w for w in larg)
    return "\n".join([fmt(cabecalho), sep, *[fmt(l) for l in cols[1:]]])


def salvar_json(nome: str, dados: dict[str, Any]) -> Path:
    RESULTADOS.mkdir(exist_ok=True)
    caminho = RESULTADOS / f"{nome}.json"
    dados = {"experimento": nome, "timestamp": int(time.time()), **dados}
    caminho.write_text(json.dumps(dados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"→ dados: {caminho.relative_to(RAIZ)}")
    return caminho


def rodar_rodadas(
    amb: Any, cidade: str, combustivel: str, estrategia: str, rodadas: int
) -> list[float]:
    """Uma rodada de aquecimento (descartada) + `rodadas` medições de tempo_ms."""
    amb.consultar(cidade, combustivel, estrategia)
    tempos = []
    for _ in range(rodadas):
        resp = amb.consultar(cidade, combustivel, estrategia)
        tempos.append(float(resp["tempo_ms"]))
    return tempos


# ------------------------------------------------------------------- gráficos
def pyplot():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.dpi": 110,
            "savefig.dpi": 300,
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 10,
        }
    )
    return plt


def salvar_fig(fig: Any, nome: str) -> Path:
    RESULTADOS.mkdir(exist_ok=True)
    caminho = RESULTADOS / f"{nome}.png"
    fig.tight_layout()
    fig.savefig(caminho)
    pyplot().close(fig)
    print(f"→ gráfico: {caminho.relative_to(RAIZ)}")
    return caminho
