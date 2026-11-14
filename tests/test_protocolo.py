"""Testes básicos do módulo de protocolo."""

from __future__ import annotations

import pytest

from src import protocolo as p


class TestNormalizarCidade:
    def test_remove_acentos(self):
        assert p.normalizar_cidade("Belém") == "belem"

    def test_caixa_baixa(self):
        assert p.normalizar_cidade("MANAUS") == "manaus"

    def test_espacos_laterais(self):
        assert p.normalizar_cidade("  Porto Velho  ") == "porto velho"

    def test_combina_tudo(self):
        assert p.normalizar_cidade(" MACAPÁ ") == "macapa"
        assert p.normalizar_cidade("Boa Vista") == "boa vista"


class TestValidarRequisicao:
    def test_requisicao_valida(self):
        msg = {
            "operacao": "consultar",
            "combustivel": "gasolina_comum",
            "cidade": "Belém",
            "estrategia": "concorrente",
        }
        ok, erro = p.validar_requisicao_consulta(msg)
        assert ok, erro

    def test_sem_estrategia_tambem_valida(self):
        """Requisições agregador→posto não têm estrategia."""
        msg = {"operacao": "consultar", "combustivel": "etanol", "cidade": "Manaus"}
        ok, erro = p.validar_requisicao_consulta(msg)
        assert ok, erro

    def test_combustivel_invalido(self):
        msg = {"operacao": "consultar", "combustivel": "querosene", "cidade": "Belém"}
        ok, erro = p.validar_requisicao_consulta(msg)
        assert not ok
        assert "combust" in erro.lower()

    def test_cidade_vazia(self):
        msg = {"operacao": "consultar", "combustivel": "etanol", "cidade": "   "}
        ok, erro = p.validar_requisicao_consulta(msg)
        assert not ok

    def test_operacao_desconhecida(self):
        msg = {"operacao": "excluir", "combustivel": "etanol", "cidade": "Belém"}
        ok, erro = p.validar_requisicao_consulta(msg)
        assert not ok

    def test_estrategia_invalida(self):
        msg = {
            "operacao": "consultar",
            "combustivel": "etanol",
            "cidade": "Belém",
            "estrategia": "aleatoria",
        }
        ok, erro = p.validar_requisicao_consulta(msg)
        assert not ok


def test_constantes_definidas():
    """Garante que todas as constantes citadas no PROTOCOLO.md existem."""
    assert p.OP_CONSULTAR == "consultar"
    assert "gasolina_comum" in p.COMBUSTIVEIS
    assert "sequencial" in p.ESTRATEGIAS
    assert "concorrente" in p.ESTRATEGIAS
    for status in ("sucesso", "nao_atendida", "indisponivel", "timeout", "erro"):
        assert hasattr(p, f"STATUS_{status.upper()}"), f"Falta STATUS_{status.upper()}"
