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

## Por que não versionar

- O CSV semanal da ANP ultrapassa facilmente alguns megabytes.
- Cada integrante pode preferir um recorte diferente (semestral, mensal).
- O GitHub rejeita arquivos individuais > 100 MB.
