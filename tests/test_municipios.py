"""Testes da lista de municípios usada pela interface gráfica."""

from __future__ import annotations

import pytest

from src import municipios as mun


@pytest.fixture
def pasta(tmp_path):
    cab = "Estado - Sigla;Municipio;Produto\n"
    (tmp_path / "anp_posto_a.csv").write_text(
        cab + "PA;BELEM;GASOLINA\nAM;MANAUS;ETANOL\nPA;BELEM;ETANOL\n", encoding="utf-8-sig")
    (tmp_path / "anp_posto_b.csv").write_text(
        cab + "RO;JI-PARANA;GASOLINA\nSP;SANTOS;GASOLINA\n", encoding="utf-8")
    return tmp_path


def test_carrega_municipios_unicos_com_uf_e_ignora_fora_do_norte(pasta):
    assert mun.carregar_municipios(pasta) == ["BELEM - PA", "JI-PARANA - RO", "MANAUS - AM"]


@pytest.mark.parametrize("texto, esperado", [
    ("Belém - PA", ("PA", "Belém")),
    ("BELEM - pa", ("PA", "BELEM")),
    ("JI-PARANA - RO", ("RO", "JI-PARANA")),
    ("Manaus-AM", ("AM", "Manaus")),
])
def test_separa_uf_e_cidade(texto, esperado):
    assert mun.separar_municipio(texto) == esperado


@pytest.mark.parametrize("texto", ["Belém", "Santos - SP", " - PA", ""])
def test_rejeita_sem_uf_do_norte(texto):
    with pytest.raises(ValueError):
        mun.separar_municipio(texto)


def test_localiza_ignorando_acentos_e_maiusculas(pasta):
    lista = mun.carregar_municipios(pasta)
    assert mun.localizar("Belém - PA", lista) == "BELEM - PA"
    assert mun.localizar("Belém - AM", lista) is None


def test_filtra_por_trecho_sem_acento(pasta):
    lista = mun.carregar_municipios(pasta)
    assert mun.filtrar("belém", lista) == ["BELEM - PA"]
    assert mun.filtrar("", lista) == lista
