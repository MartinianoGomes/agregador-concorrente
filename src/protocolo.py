"""Protocolo de aplicação do Agregador de Combustíveis.

Constantes, serialização e helpers de socket. Documentação completa do
protocolo em `PROTOCOLO.md` na raiz do repositório.
"""

from __future__ import annotations

import json
import socket
import unicodedata
from typing import Any

# ---------- Constantes ----------
PROTOCOLO_VERSAO = "v2"

ENCODING = "utf-8"
BUFFER_SIZE = 4096
TIMEOUT_POSTO_S = 5.0  # timeout (segundos) de consulta a um posto
TIMEOUT_CLIENTE_S = 30.0  # timeout do cliente esperando o agregador

# Operações
OP_CONSULTAR = "consultar"

# Estados (UF) da Região Norte atendidos
ESTADOS = ("AC", "AM", "AP", "PA", "RO", "RR", "TO")

# Combustíveis aceitos
COMBUSTIVEIS = ("gasolina_comum", "gasolina_aditivada", "etanol", "diesel_s10")

# Estratégias
ESTRATEGIA_SEQUENCIAL = "sequencial"
ESTRATEGIA_CONCORRENTE = "concorrente"
ESTRATEGIAS = (ESTRATEGIA_SEQUENCIAL, ESTRATEGIA_CONCORRENTE)

# Status possíveis
STATUS_SUCESSO = "sucesso"
STATUS_NAO_ATENDIDA = "nao_atendida"
STATUS_INDISPONIVEL = "indisponivel"
STATUS_TIMEOUT = "timeout"
STATUS_ERRO = "erro"


# ---------- Serialização por linha ----------
def enviar_json(conn: socket.socket, msg: dict[str, Any]) -> None:
    """Envia um dict como JSON terminado em \\n."""
    payload = (json.dumps(msg, ensure_ascii=False) + "\n").encode(ENCODING)
    conn.sendall(payload)


def receber_json(conn: socket.socket) -> dict[str, Any]:
    """Recebe uma mensagem JSON até o próximo \\n e devolve dict.

    Levanta `ConnectionError` se o outro lado fechar sem enviar nada e
    `json.JSONDecodeError` se o conteúdo não for JSON válido.
    """
    chunks: list[bytes] = []
    while True:
        chunk = conn.recv(BUFFER_SIZE)
        if not chunk:
            break
        chunks.append(chunk)
        if chunk.endswith(b"\n"):
            break
    if not chunks:
        raise ConnectionError("Conexão encerrada sem dados")
    data = b"".join(chunks).decode(ENCODING).strip()
    return json.loads(data)


# ---------- Normalização ----------
def normalizar_cidade(nome: str) -> str:
    """Normaliza o nome de uma cidade para busca.

    - Remove acentos (NFD + drop combining marks).
    - Converte para caixa baixa.
    - Remove espaços nas pontas.

    >>> normalizar_cidade(" Belém ")
    'belem'
    >>> normalizar_cidade("BOA VISTA")
    'boa vista'
    """
    s = unicodedata.normalize("NFD", nome)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower().strip()


def normalizar_estado(sigla: str) -> str:
    """Normaliza a sigla de um estado (UF): sem espaços nas pontas e em caixa alta.

    >>> normalizar_estado(" pa ")
    'PA'
    """
    return sigla.strip().upper()


# ---------- Validação ----------
def validar_requisicao_consulta(msg: dict[str, Any]) -> tuple[bool, str]:
    """Verifica se uma requisição `consultar` é válida.

    Retorna (True, "") se OK, ou (False, mensagem_de_erro) caso contrário.
    """
    if msg.get("operacao") != OP_CONSULTAR:
        return False, f"operação desconhecida: {msg.get('operacao')!r}"
    estado = msg.get("estado")
    if not isinstance(estado, str) or normalizar_estado(estado) not in ESTADOS:
        return False, f"estado inválido: {estado!r} (aceitos: {', '.join(ESTADOS)})"
    if msg.get("combustivel") not in COMBUSTIVEIS:
        return False, f"combustível inválido: {msg.get('combustivel')!r}"
    if not isinstance(msg.get("cidade"), str) or not msg["cidade"].strip():
        return False, "cidade ausente ou inválida"
    # estratégia só é exigida na requisição cliente→agregador;
    # na requisição agregador→posto ela não aparece.
    estrategia = msg.get("estrategia")
    if estrategia is not None and estrategia not in ESTRATEGIAS:
        return False, f"estratégia inválida: {estrategia!r}"
    return True, ""
