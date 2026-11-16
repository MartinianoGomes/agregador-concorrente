"""Testes do rastreamento de mensagens (envio/recebimento com detalhes completos)."""

from __future__ import annotations

import logging
import socket

import pytest

from src import protocolo as p


@pytest.fixture
def par_de_sockets():
    a, b = socket.socketpair()
    yield a, b
    a.close()
    b.close()


@pytest.fixture
def rastreio(caplog):
    p.ativar_rastreio("teste")
    caplog.set_level(logging.INFO, logger="rastreio")
    yield caplog
    p.desativar_rastreio()


def test_registra_envio_e_recebimento_com_json_completo(par_de_sockets, rastreio):
    a, b = par_de_sockets
    msg = {"id": "abc12345", "operacao": "consultar", "estado": "PA", "cidade": "Belém"}

    p.enviar_json(a, msg, par="posto A")
    recebida = p.receber_json(b, par="agregador")

    assert recebida == msg
    envio, recebimento = [r.getMessage() for r in rastreio.records]
    assert "[teste | MainThread]" in envio
    assert "→ ENVIA para posto A" in envio
    assert "← RECEBE de agregador" in recebimento
    for linha in (envio, recebimento):
        assert "id=abc12345" in linha
        assert '"cidade": "Belém"' in linha  # conteúdo completo, sem escapar acentos
        assert f"| {len(p.json.dumps(msg, ensure_ascii=False).encode()) + 1} bytes |" in linha


def test_registra_json_invalido_antes_do_erro(par_de_sockets, rastreio):
    a, b = par_de_sockets
    a.sendall(b"{isto nao e json\n")

    with pytest.raises(ValueError):
        p.receber_json(b, par="cliente")

    (linha,) = [r.getMessage() for r in rastreio.records]
    assert "{isto nao e json" in linha
    assert "(JSON inválido)" in linha


def test_sem_rastreio_nada_e_registrado(par_de_sockets, caplog):
    a, b = par_de_sockets
    caplog.set_level(logging.INFO, logger="rastreio")

    p.enviar_json(a, {"operacao": "consultar"})
    p.receber_json(b)

    assert not caplog.records


def test_evento_so_aparece_com_rastreio_ativo(rastreio):
    p.rastrear_evento("posto D sem resposta")
    p.desativar_rastreio()
    p.rastrear_evento("não deve aparecer")

    assert [r.getMessage() for r in rastreio.records] == ["[teste | MainThread] posto D sem resposta"]


def test_novo_id_e_curto_e_unico():
    ids = {p.novo_id() for _ in range(100)}
    assert len(ids) == 100
    assert all(len(i) == 8 for i in ids)


class TestValidacaoDoId:
    base = {"operacao": "consultar", "estado": "PA", "combustivel": "etanol", "cidade": "Belém"}

    def test_id_opcional(self):
        assert p.validar_requisicao_consulta(dict(self.base))[0]

    def test_id_texto_aceito(self):
        assert p.validar_requisicao_consulta({**self.base, "id": "a1b2c3d4"})[0]

    @pytest.mark.parametrize("id_ruim", [123, "", "x" * 65])
    def test_id_invalido(self, id_ruim):
        ok, erro = p.validar_requisicao_consulta({**self.base, "id": id_ruim})
        assert not ok
        assert "id" in erro


def test_mensagem_que_nao_e_objeto_e_rejeitada():
    ok, erro = p.validar_requisicao_consulta([1, 2])
    assert not ok
    assert "objeto" in erro
