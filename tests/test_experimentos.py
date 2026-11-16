"""Testes da infraestrutura dos experimentos (sem subir processos)."""

from __future__ import annotations

import socket

import pytest

from experimentos import _comum as c
from experimentos import executar_todos, plot_comparativo


def test_porta_livre_pode_ser_usada():
    porta = c._porta_livre()
    with socket.socket() as s:
        s.bind((c.HOST, porta))  # não levanta: a porta estava livre


def test_ambientes_diferentes_usam_portas_diferentes():
    a, b = c.Ambiente(), c.Ambiente()
    portas_a = {a.porta, *a.portas_postos.values()}
    portas_b = {b.porta, *b.portas_postos.values()}
    assert len(portas_a) == 5
    assert not portas_a & portas_b


def test_metadados_registram_versao_e_maquina():
    meta = c.metadados()
    assert meta["protocolo_versao"]
    assert meta["cpus"]
    assert "commit" in meta


def _exp(**kw):
    base = {"estado": "PA", "cidade": "Belém", "combustivel": "etanol", "latencia_ms": 200,
            "n_rodadas": 10}
    return {**base, **kw}


def test_comparativo_aceita_parametros_iguais():
    plot_comparativo.verificar_compatibilidade({"sequencial": _exp(), "concorrente": _exp()})


def test_comparativo_recusa_parametros_diferentes():
    with pytest.raises(SystemExit, match="latencia_ms"):
        plot_comparativo.verificar_compatibilidade(
            {"sequencial": _exp(), "concorrente": _exp(latencia_ms=0)})


def test_executar_todos_registra_falha_e_continua():
    def falha():
        raise RuntimeError("quebrou")

    def ok():
        pass

    assert executar_todos._executar(ok, []) is None
    assert "quebrou" in executar_todos._executar(falha, [])
    assert executar_todos._executar(lambda: (_ for _ in ()).throw(SystemExit("motivo")), []) == "motivo"
