"""Municípios atendidos pelos postos, lidos dos recortes da ANP.

Usado pela interface gráfica para preencher o seletor de municípios. Fica fora
de `interface_grafica.py` para poder ser testado sem o Tkinter.

Os municípios aparecem no formato "CIDADE - UF" (ex.: "BELEM - PA").
"""

from __future__ import annotations

import csv
from pathlib import Path

from src import protocolo as p

SEPARADOR = " - "


def carregar_municipios(pasta: Path) -> list[str]:
    """Lê os municípios (com a UF) de todos os `anp_posto_*.csv` da pasta, sem consultar preços."""
    municipios: set[str] = set()
    for arquivo in sorted(pasta.glob("anp_posto_*.csv")):
        with arquivo.open(encoding="utf-8-sig", newline="") as dados:
            for registro in csv.DictReader(dados, delimiter=";"):
                nome = (registro.get("Municipio") or "").strip()
                uf = p.normalizar_estado(registro.get("Estado - Sigla") or "")
                if nome and uf in p.ESTADOS:
                    municipios.add(f"{nome}{SEPARADOR}{uf}")
    return sorted(municipios, key=chave_busca)


def separar_municipio(texto: str) -> tuple[str, str]:
    """Separa "Belém - PA" em ("PA", "Belém").

    Levanta `ValueError` se o texto não terminar com uma UF da Região Norte.
    """
    cidade, sep, uf = texto.strip().rpartition(SEPARADOR.strip())
    uf = p.normalizar_estado(uf)
    if not sep or not cidade.strip() or uf not in p.ESTADOS:
        raise ValueError(
            f"informe o município no formato 'Cidade - UF' (UF: {', '.join(p.ESTADOS)})"
        )
    return uf, cidade.strip()


def chave_busca(texto: str) -> str:
    """Forma normalizada (sem acento, minúscula) usada para comparar e filtrar municípios."""
    return p.normalizar_cidade(texto)


def localizar(texto: str, municipios: list[str]) -> str | None:
    """Devolve o município da lista equivalente a `texto` (ignora acentos e maiúsculas)."""
    alvo = chave_busca(texto)
    return next((m for m in municipios if chave_busca(m) == alvo), None)


def filtrar(texto: str, municipios: list[str]) -> list[str]:
    """Municípios que contêm `texto` (ignora acentos e maiúsculas); lista toda se vazio."""
    alvo = chave_busca(texto)
    return [m for m in municipios if alvo in chave_busca(m)] if alvo else list(municipios)
