"""Protocolo de aplicação do Agregador de Combustíveis.

Constantes, serialização, rastreamento de mensagens e helpers de socket.
Documentação completa do protocolo em `PROTOCOLO.md` na raiz do repositório.
"""

from __future__ import annotations

import json
import logging
import socket
import sys
import threading
import unicodedata
import uuid
from typing import Any

# ---------- Constantes ----------
PROTOCOLO_VERSAO = "v2.1"

ENCODING = "utf-8"
BUFFER_SIZE = 4096
TIMEOUT_POSTO_S = 5.0  # timeout (segundos) de consulta a um posto
TIMEOUT_CLIENTE_S = 30.0  # timeout do cliente esperando o agregador
# Conexões que podem esperar na fila do accept(). Com um valor baixo (ex.: 16),
# rajadas de dezenas de clientes simultâneos têm conexões recusadas pelo SO.
BACKLOG = 128

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

# Identificador de rastreio (campo opcional "id" em todas as mensagens)
ID_TAMANHO_MAX = 64

# Status possíveis
STATUS_SUCESSO = "sucesso"
STATUS_NAO_ATENDIDA = "nao_atendida"
STATUS_INDISPONIVEL = "indisponivel"
STATUS_TIMEOUT = "timeout"
STATUS_ERRO = "erro"


# ---------- Rastreamento ----------
# Quando ativado, cada envio e recebimento de mensagem é registrado no logger
# "rastreio" com: horário (ms), parte, thread, sentido, outro lado da conexão,
# id de rastreio, tamanho em bytes e o JSON completo.
log_rastreio = logging.getLogger("rastreio")
_parte_rastreada: str | None = None


def novo_id() -> str:
    """Gera um id curto de rastreio para correlacionar as mensagens de uma consulta."""
    return uuid.uuid4().hex[:8]


def ativar_rastreio(parte: str) -> None:
    """Liga o rastreamento neste processo; `parte` identifica quem registra (ex.: "posto A")."""
    global _parte_rastreada
    _parte_rastreada = parte


def desativar_rastreio() -> None:
    global _parte_rastreada
    _parte_rastreada = None


def rastreio_ativo() -> bool:
    return _parte_rastreada is not None


def configurar_rastreio(parte: str) -> None:
    """Ativa o rastreamento e envia as linhas para stderr, separadas dos logs comuns."""
    ativar_rastreio(parte)
    if not log_rastreio.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(
            "%(asctime)s.%(msecs)03d %(message)s", datefmt="%H:%M:%S"))
        log_rastreio.addHandler(handler)
    log_rastreio.setLevel(logging.INFO)
    log_rastreio.propagate = False


def _descrever_par(conn: socket.socket, par: str | None) -> str:
    try:
        remoto = conn.getpeername()
        endereco = f"{remoto[0]}:{remoto[1]}" if isinstance(remoto, tuple) else str(remoto or "local")
    except OSError:
        endereco = "desconectado"
    return f"{par} ({endereco})" if par else endereco


def _cabecalho() -> str:
    return f"[{_parte_rastreada} | {threading.current_thread().name}]"


def rastrear_evento(texto: str) -> None:
    """Registra um evento que não é mensagem (timeout, conexão recusada, tempo de resposta)."""
    if _parte_rastreada is not None:
        log_rastreio.info("%s %s", _cabecalho(), texto)


def _rastrear_mensagem(sentido: str, conn: socket.socket, bruto: bytes, par: str | None,
                       msg: Any = None) -> None:
    id_msg = msg.get("id") if isinstance(msg, dict) else None
    seta = "→ ENVIA para " if sentido == "envio" else "← RECEBE de "
    conteudo = bruto.decode(ENCODING, errors="replace").rstrip("\r\n") or "(vazio)"
    if sentido == "recebimento" and msg is None:
        conteudo += "   (JSON inválido)"
    log_rastreio.info(
        "%s %s%s | id=%s | %d bytes | %s",
        _cabecalho(), seta, _descrever_par(conn, par), id_msg or "-", len(bruto), conteudo,
    )


# ---------- Serialização por linha ----------
def enviar_json(conn: socket.socket, msg: dict[str, Any], par: str | None = None) -> None:
    """Envia um dict como JSON terminado em \\n.

    `par` é um nome legível para o outro lado (ex.: "posto A"), usado só no rastreio.
    """
    payload = (json.dumps(msg, ensure_ascii=False) + "\n").encode(ENCODING)
    conn.sendall(payload)
    if _parte_rastreada is not None:
        _rastrear_mensagem("envio", conn, payload, par, msg)


def receber_json(conn: socket.socket, par: str | None = None) -> dict[str, Any]:
    """Recebe uma mensagem JSON até o próximo \\n e devolve dict.

    Levanta `ConnectionError` se o outro lado fechar sem enviar nada e
    `json.JSONDecodeError` se o conteúdo não for JSON válido. Com o rastreio
    ativo, a mensagem é registrada mesmo quando o JSON é inválido.
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
    bruto = b"".join(chunks)
    try:
        msg = json.loads(bruto.decode(ENCODING).strip())
    except ValueError:
        if _parte_rastreada is not None:
            _rastrear_mensagem("recebimento", conn, bruto, par)
        raise
    if _parte_rastreada is not None:
        _rastrear_mensagem("recebimento", conn, bruto, par, msg)
    return msg


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
    if not isinstance(msg, dict):
        return False, "a mensagem deve ser um objeto JSON"
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
    id_msg = msg.get("id")
    if id_msg is not None and (not isinstance(id_msg, str) or not 0 < len(id_msg) <= ID_TAMANHO_MAX):
        return False, f"id de rastreio inválido: {id_msg!r}"
    estrategia = msg.get("estrategia")
    if estrategia is not None and estrategia not in ESTRATEGIAS:
        return False, f"estratégia inválida: {estrategia!r}"
    return True, ""
