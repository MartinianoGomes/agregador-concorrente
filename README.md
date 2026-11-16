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

- Diagramas UML (casos de uso, componentes e sequência): [`docs/`](docs/README.md).
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
│   ├── preparar_csvs.py    # Divide o CSV da ANP (baixado à mão) em 4 recortes, um por rede
│   ├── run_all.sh          # Sobe postos + agregador em uma só execução (Linux/Mac)
│   └── run_all.bat         # Idem para Windows
├── data/                   # CSVs da ANP (gitignored, exceto o README)
├── experimentos/           # 5 experimentos obrigatórios + gráficos
│   ├── _comum.py           # Sobe/derruba postos e agregador, estatísticas, gráficos
│   ├── exp_1 … exp_5       # Um módulo por experimento
│   ├── plot_comparativo.py # Gráficos 1 × 2
│   ├── executar_todos.py   # Roda tudo em sequência
│   └── regerar_graficos.py # Refaz os PNGs a partir dos JSONs
├── resultados/             # Saída dos experimentos: JSON, PNG e logs (gitignored)
├── tests/                  # Testes (pytest)
└── docs/                   # Diagramas UML (PNG) e o script que os gera
```

## Requisitos

- Python 3.10 ou superior
- pip (a aplicação só usa a biblioteca padrão; `matplotlib` ≥ 3.9 é necessário para os gráficos e `pytest` para os testes)
- Sistema operacional: Linux, macOS ou Windows

## Instalação

```bash
git clone https://github.com/MartinianoGomes/agregador-concorrente.git
cd agregador-concorrente
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

O script gera `data/anp_posto_a.csv`, `data/anp_posto_b.csv`, `data/anp_posto_c.csv` e `data/anp_posto_d.csv`. Cada estabelecimento (CNPJ) vai para exatamente um recorte, escolhido pelo hash do CNPJ, então os 4 postos têm subconjuntos disjuntos dos pontos de venda da Região Norte.

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

Os scripts já sobem tudo com `--rastreio`: cada processo mostra, em stderr, cada mensagem que envia e recebe, com horário em ms, thread, endereço do outro lado, `id` da consulta, tamanho e o JSON completo. Para seguir uma consulta pelos processos, procure pelo `id` exibido no cliente (ex.: `[id 81e284c6]`). Detalhes em [`PROTOCOLO.md`](PROTOCOLO.md#rastreamento-id).

O cliente pergunta, nesta ordem, o **estado** (UF da Região Norte: AC, AM, AP, PA, RO, RR, TO), o **município**, o combustível e a estratégia. Para uma consulta única, sem menus:

```bash
python -m src.cliente --estado PA --cidade Belém --combustivel gasolina_comum --estrategia concorrente
```

## Experimentos

Os experimentos medem o desempenho das duas estratégias do agregador: **sequencial** (consulta um posto de cada vez) e **concorrente** (uma thread por posto, todas ao mesmo tempo).

Cada experimento **sobe e derruba sozinho** os 4 postos e o agregador, em portas livres escolhidas na hora. Por isso pode rodar junto com o `run_all` ou com outro experimento sem conflito de portas. Mesmo assim, evite rodar dois ao mesmo tempo: um disputa CPU com o outro e as medições ficam distorcidas. Basta ter os CSVs em `data/` e o `matplotlib` instalado. O rastreio de mensagens fica desligado, para não interferir nas medições.

Todos consultam a mesma combinação, por padrão **PA / Belém / gasolina_comum**. Para trocar, use `--estado`, `--cidade` e `--combustivel`. Antes de começar, o experimento confere se os 4 postos atendem essa combinação; se algum não atender, ele para e avisa, porque um `nao_atendida` distorceria as medições.

Para rodar tudo em sequência:

```bash
python -m experimentos.executar_todos
python -m experimentos.executar_todos --estado AM --cidade Manaus --combustivel etanol
```

O `executar_todos` repassa `--estado`, `--cidade` e `--combustivel` a todos os experimentos. Se um falhar, os seguintes rodam mesmo assim. No fim aparece um resumo com OK/FALHA e a duração de cada etapa; se algo falhou, o processo termina com código 1.

### Experimentos 1 e 2: tempo de uma consulta (sequencial × concorrente)

```bash
python -m experimentos.exp_1_sequencial
python -m experimentos.exp_2_concorrente
python -m experimentos.plot_comparativo
```

- **Pergunta:** quanto tempo uma consulta leva em cada estratégia, com os postos respondendo como numa rede real?
- **Como funciona:** cada posto espera 200 ms antes de responder, simulando a rede. O exp. 1 faz 10 consultas seguidas no modo sequencial; o exp. 2 faz o mesmo no modo concorrente. Antes delas há uma consulta de aquecimento, que é descartada. O tempo registrado é o `tempo_ms` medido pelo agregador.
- **Opções:** `--rodadas N` (padrão 10); `--latencia-ms L` muda o atraso de cada posto (padrão 200; com 0 os postos respondem em cerca de 1 ms e a comparação mede só ruído); `--externo` usa o agregador já em execução na porta 5000, em vez de subir um próprio.
- **Comparação:** o `plot_comparativo` lê os resultados dos dois e gera os gráficos lado a lado. Rode-o depois dos exps. 1 e 2. Se os dois tiverem rodado com parâmetros diferentes (cidade, combustível, latência ou rodadas), ele recusa a comparação e diz o que difere.
- **O que esperar:** o sequencial soma as quatro esperas (≈ 800 ms) e o concorrente espera só a mais lenta (≈ 200 ms).
- **Saídas:** `exp_1_sequencial.json`, `exp_2_concorrente.json` e os gráficos `exp_12_barras.png` (média ± desvio), `exp_12_rodadas.png` (tempo de cada rodada) e `exp_12_boxplot.png` (distribuição).

### Experimento 3: efeito da latência dos postos

```bash
python -m experimentos.exp_3_latencia
```

- **Pergunta:** como o tempo de cada estratégia cresce quando os postos demoram a responder?
- **Como funciona:** para cada latência L (padrão: 0, 100, 250, 500, 1000 e 2000 ms), sobe um ambiente novo em que **todos** os postos esperam L ms antes de responder. Faz 5 consultas em cada estratégia, alternando sequencial e concorrente para que a ordem não favoreça nenhuma.
- **Opções:** `--latencias 0 100 500 …`, `--rodadas N` (padrão 5).
- **O que esperar:** com 4 postos, o sequencial soma as esperas (≈ 4 × L) e o concorrente espera só a mais lenta (≈ L). O *speedup* (tempo sequencial ÷ tempo concorrente) se aproxima de 4 à medida que L cresce.
- **Saídas:** `exp_3_latencia.json`, `exp_3_tempo_vs_latencia.png` (curvas medidas com as retas teóricas 4·L e L), `exp_3_speedup.png` e `exp_3_barras.png`.

### Experimento 4: vários clientes ao mesmo tempo

```bash
python -m experimentos.exp_4_multiplos_clientes
```

- **Pergunta:** como o agregador se comporta quando muitos clientes consultam ao mesmo tempo?
- **Como funciona:** para cada quantidade N de clientes (padrão: 1, 2, 5, 10, 20 e 50), dispara N clientes em threads liberadas no mesmo instante e mede o tempo que cada um espera pela resposta. Repete cada ponto 3 vezes, nas duas estratégias. Os postos têm latência fixa de 200 ms para a diferença ficar visível.
- **Opções:** `--clientes 1 10 50 …`, `--repeticoes N` (padrão 3), `--latencia-ms L` (padrão 200).
- **O que mede:**
  - tempo médio, p95 e máximo por cliente;
  - **vazão** (consultas respondidas por segundo);
  - **falhas** (o cliente não recebeu resposta);
  - **respostas degradadas** (vieram com algum posto em `indisponiveis`);
  - a diferença entre o tempo visto pelo cliente e o `tempo_ms` do agregador, que mostra quanto tempo a consulta ficou na fila antes de ser atendida.
- **Observação:** o agregador e os postos aceitam até 128 conexões esperando na fila (`BACKLOG` em `src/protocolo.py`). Até esse limite, uma falha indica problema no sistema, não na fila do sistema operacional.
- **Saídas:** `exp_4_multiplos_clientes.json`, `exp_4_tempo_medio.png`, `exp_4_p95.png`, `exp_4_vazao.png`, `exp_4_falhas.png` e `exp_4_cliente_vs_agregador.png`.

### Experimento 5: tolerância a falhas de postos

```bash
python -m experimentos.exp_5_indisponibilidade
```

- **Pergunta:** o agregador continua respondendo, com os postos que restaram, quando um posto falha?
- **Como funciona:** roda 4 cenários, cada um nas duas estratégias e com um ambiente novo:

| Cenário | O que acontece | Resultado esperado |
| --- | --- | --- |
| 0. Referência | 4 postos funcionando (latência de 500 ms) | 4 respostas com `sucesso` |
| A. Fora do ar antes | O posto D nunca é iniciado | D aparece como `indisponivel` |
| B. Cai durante a consulta | O posto A é encerrado 0,5 s depois de a consulta começar (latência de 2 s) | A aparece como `indisponivel` |
| C. Pendurado | O posto D demora 6 s, mais que o timeout de 5 s | D aparece como `timeout`, e a consulta termina perto dos 5 s |

- **Verificação automática:** em cada execução o experimento confere três coisas:
  1. os postos saudáveis responderam com `sucesso`;
  2. o posto afetado recebeu o status esperado;
  3. o `menor_preco` considera só quem respondeu.
  
  Ao final imprime PASS ou FAIL por cenário. Se algum falhar, o processo termina com código 1.
- **Saídas:** `exp_5_indisponibilidade.json`, `exp_5_tempos.png` (tempo por cenário e estratégia) e `exp_5_status.png` (status de cada posto por cenário).

### Onde ficam os resultados

Tudo vai para `resultados/`:
- um JSON por experimento, com os dados brutos, as estatísticas e um bloco `ambiente` com a versão do protocolo, o commit do git (marcado como `-modificado` se havia mudanças não commitadas), as versões do Python e do sistema e o número de CPUs;
- os gráficos em PNG (300 dpi);
- em `resultados/logs/`, a saída de cada processo que o experimento iniciou.

Para refazer só os gráficos a partir dos JSONs já gravados, sem medir de novo:

```bash
python -m experimentos.regerar_graficos
```
