"""Experimento 5 — Indisponibilidade de um posto.

Desliga um dos postos no meio de uma consulta e verifica se o agregador
responde corretamente com `status: "indisponivel"` para o posto caído,
sem bloquear os demais.

TODO (João Paulo):
  - Automatizar com subprocess.Popen: subir o posto, iniciar a consulta,
    matar o posto, verificar a resposta.
  - Registrar o tempo total e confirmar que respeita o timeout de 5 s.
"""

from __future__ import annotations

print(__doc__)
print("Ainda não implementado. Esqueleto pronto para o João Paulo preencher.")


def main() -> None:
    raise NotImplementedError("TODO: João Paulo")


if __name__ == "__main__":
    main()
