# Agregador Concorrente de Preços de Combustíveis — Região Norte

Trabalho 1 da disciplina **Sistemas Distribuídos** (UNIFESSPA/FACSI), Prof. Gleison de Oliveira Medeiros. Grupo III — Tema 3.

> Aplicação cliente-servidor em Python que consulta, por sockets TCP, preços de combustíveis em quatro postos independentes (redes de abastecimento da Região Norte), nos modos **sequencial** e **concorrente** (threads). Os preços vêm de um recorte da série histórica semanal da ANP.

## Integrantes

- Bruno
- Gustavo
- João Paulo
- Ketly
- Marília
- Martiniano Gomes Barros Cirqueira Neto

## Documentação

- Especificação de requisitos e modelagem UML: [Google Doc do grupo](https://claude.ai/artifact/T1jSLmcGik6xKXDqK5aL2B) (editável).
- Protocolo de aplicação (JSON sobre TCP): [`PROTOCOLO.md`](PROTOCOLO.md).
- Guia de contribuição (branches, commits, PRs): [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Estrutura do repositório

```
.
├── src/                    # Código-fonte da aplicação
│   ├── protocolo.py        # Constantes e helpers do protocolo JSON
│   ├── posto.py            # Servidor TCP de um posto (4 instâncias em portas 6001-6004)
│   ├── agregador.py        # Servidor agregador (porta 5000)
│   └── cliente.py          # Cliente CLI
├── scripts/
│   ├── preparar_csvs.py    # Baixa o CSV da ANP e gera 4 recortes por rede
│   ├── run_all.sh          # Sobe postos + agregador em uma só execução (Linux/Mac)
│   └── run_all.bat         # Idem para Windows
├── data/                   # CSVs da ANP (gitignored, exceto .gitkeep e README)
├── experimentos/           # Scripts dos 5 experimentos obrigatórios
├── resultados/             # Saída bruta dos experimentos (gitignored)
├── tests/                  # Testes básicos (pytest)
└── docs/                   # Links e materiais auxiliares
```

## Requisitos

- Python 3.10 ou superior
- pip (para instalar `pandas`, opcional — se não quiser pandas, use `csv` da stdlib)
- Sistema operacional: Linux, macOS ou Windows

## Instalação

```bash
git clone https://github.com/<organizacao-ou-usuario>/agregador-combustiveis-norte.git
cd agregador-combustiveis-norte
python -m venv .venv
source .venv/bin/activate          # Linux/macOS
.venv\Scripts\activate             # Windows
pip install -r requirements.txt
```

## Preparar os dados da ANP

1. Baixe o CSV da série histórica mais recente em: <https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis>.
2. Coloque o arquivo em `data/anp_bruto.csv`.
3. Execute o script que fatia o CSV em 4 recortes (um por "posto"):

```bash
python scripts/preparar_csvs.py --entrada data/anp_bruto.csv --saida data/
```

O script gera `data/anp_posto_a.csv`, `data/anp_posto_b.csv`, `data/anp_posto_c.csv` e `data/anp_posto_d.csv`, cada um contendo um subconjunto distinto dos pontos de venda da Região Norte.

## Rodar a aplicação

**Linux/macOS** — em um terminal:

```bash
./scripts/run_all.sh
```

**Windows** — em um Prompt de Comando:

```bat
scripts\run_all.bat
```

Os scripts sobem os 4 postos (portas 6001–6004) e o agregador (porta 5000) em processos separados. Para parar tudo, Ctrl+C.

**Em outro terminal**, inicie o cliente:

```bash
python -m src.cliente --host localhost --porta 5000
```

## Rodar os experimentos

```bash
python -m experimentos.exp_1_sequencial
python -m experimentos.exp_2_concorrente
python -m experimentos.exp_3_latencia
python -m experimentos.exp_4_multiplos_clientes
python -m experimentos.exp_5_indisponibilidade
```

Os tempos e logs vão para `resultados/`.

## Divisão de responsabilidades

Ver a [issue inicial no GitHub](#) (a criar) ou a [proposta inicial no doc do grupo](https://claude.ai/artifact/T1jSLmcGik6xKXDqK5aL2B#divis%C3%A3o-de-atividades-6-integrantes).

Resumo:

| Integrante | Responsabilidade |
| --- | --- |
| Bruno | Agregador (`src/agregador.py`) + integração geral |
| Gustavo | Postos (`src/posto.py`) + `scripts/preparar_csvs.py` |
| João Paulo | Experimentos (`experimentos/`) + relatório técnico + slides |
| Ketly | Modelagem UML (imagens dos diagramas) + revisão dos slides |
| Marília | Documento de requisitos + revisão final |
| Martiniano | Cliente (`src/cliente.py`) + `PROTOCOLO.md` |

## Apresentação

- **Data:** 16/11/2026
- **Duração:** 15 a 20 minutos
- **Local:** UNIFESSPA — Campus Marabá
