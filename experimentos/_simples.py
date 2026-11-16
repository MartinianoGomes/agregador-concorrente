"""Lógica comum dos Experimentos 1 (sequencial) e 2 (concorrente)."""

from __future__ import annotations

from experimentos import _comum as c

# Sem atraso os postos respondem em ~1 ms e a comparação mede só ruído; 200 ms
# simula uma rede real e é a mesma latência usada no Experimento 4.
LATENCIA_PADRAO_MS = 200


def executar(numero: int, nome: str, estrategia: str) -> None:
    ap = c.parser_base(f"Experimento {numero} — consulta {estrategia}.")
    ap.add_argument("--rodadas", type=int, default=10)
    ap.add_argument(
        "--latencia-ms", type=int, default=LATENCIA_PADRAO_MS,
        help=f"atraso artificial de cada posto, em ms (padrão {LATENCIA_PADRAO_MS}; 0 = sem atraso)",
    )
    ap.add_argument(
        "--externo", action="store_true",
        help="usa o agregador já em execução em localhost:5000 (ignora --latencia-ms)",
    )
    args = ap.parse_args()

    c.validar_dados(args.estado, args.cidade, args.combustivel)
    amb = c.AmbienteExterno() if args.externo else c.Ambiente(args.latencia_ms, tag=nome)
    with amb:
        tempos = c.rodar_rodadas(amb, args.estado, args.cidade, args.combustivel, estrategia, args.rodadas)

    est = c.estatisticas(tempos)
    for i, t in enumerate(tempos, 1):
        print(f"rodada {i:>2}: {t} ms")
    print(f"\nmédia {est['media']} ms | desvio {est['desvio']} ms | p95 {est['p95']} ms")

    c.salvar_json(
        nome,
        {
            "estrategia": estrategia,
            "estado": args.estado, "cidade": args.cidade,
            "combustivel": args.combustivel,
            "latencia_ms": None if args.externo else args.latencia_ms,
            "n_rodadas": args.rodadas,
            "tempos_ms": tempos,
            "media_ms": est["media"],
            "estatisticas": est,
        },
    )
