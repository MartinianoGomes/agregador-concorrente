# Pasta `data/`

Esta pasta é destinada aos arquivos CSV com os preços da ANP. **Nenhum CSV é versionado**: cada integrante baixa localmente e o `.gitignore` ignora os arquivos.

## Como preencher

1. Baixe a planilha mais recente em: <https://www.gov.br/anp/pt-br/centrais-de-conteudo/dados-abertos/serie-historica-de-precos-de-combustiveis>.
   - Prefira o semestre corrente ou mensal mais recente.
2. Extraia o arquivo CSV (se vier em `.zip`).
3. Salve-o como `data/anp_bruto.csv`.
4. Rode o fatiamento:
   ```bash
   python scripts/preparar_csvs.py --entrada data/anp_bruto.csv --saida data/
   ```
5. Devem aparecer `anp_posto_a.csv`, `anp_posto_b.csv`, `anp_posto_c.csv`, `anp_posto_d.csv`.

## Formato esperado

O CSV da ANP é separado por `;` e lido como UTF-8 (com ou sem BOM). As colunas usadas são:

| Coluna | Usada por | Para quê |
| --- | --- | --- |
| `Estado - Sigla` | `preparar_csvs.py`, postos, interface gráfica | filtrar a Região Norte e buscar por UF |
| `CNPJ da Revenda` | `preparar_csvs.py`, postos | dividir os estabelecimentos entre os postos; pegar a coleta mais recente de cada um |
| `Municipio` | postos, interface gráfica | buscar o município; montar a lista da interface |
| `Produto` | postos | `GASOLINA`, `GASOLINA ADITIVADA`, `ETANOL` e `DIESEL S10` (os demais são ignorados) |
| `Valor de Venda` | postos | preço, com vírgula decimal (ex.: `6,29`) |
| `Data da Coleta` | postos | data no formato `dd/mm/aaaa` |

Se a ANP mudar o nome de alguma coluna, os postos param na inicialização com um `KeyError` que mostra o nome da coluna. O `preparar_csvs.py` só confere `Estado - Sigla`; uma coluna `CNPJ da Revenda` ausente aparece como "CNPJ não informado".

## Por que não versionar

- O CSV semanal da ANP ultrapassa facilmente alguns megabytes.
- Cada integrante pode preferir um recorte diferente (semestral, mensal).
- O GitHub rejeita arquivos individuais > 100 MB.
