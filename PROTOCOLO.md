# Protocolo de Aplicação — Agregador de Combustíveis

Protocolo JSON sobre TCP utilizado entre cliente ↔ agregador e entre agregador ↔ postos.

## Codificação e enquadramento

- **Encoding:** UTF-8.
- **Enquadramento:** uma mensagem por linha. Cada mensagem é um objeto JSON válido terminado em `\n` (LF, `0x0A`).
- **Tamanho máximo recomendado:** 64 KiB por mensagem.

## Operações

Apenas a operação `consultar` é definida nesta versão.

### Requisição cliente → agregador

```json
{
  "operacao": "consultar",
  "estado": "PA",
  "combustivel": "gasolina_comum",
  "cidade": "Belém",
  "estrategia": "concorrente"
}
```

| Campo | Tipo | Valores aceitos |
| --- | --- | --- |
| `operacao` | string | `"consultar"` |
| `estado` | string | Sigla da UF na Região Norte: `"AC"`, `"AM"`, `"AP"`, `"PA"`, `"RO"`, `"RR"`, `"TO"` (normalizada no servidor: caixa alta, sem espaços) |
| `combustivel` | string | `"gasolina_comum"`, `"gasolina_aditivada"`, `"etanol"`, `"diesel_s10"` |
| `cidade` | string | Nome livre (normalizado no servidor: sem acentos, caixa baixa). A busca é feita pelo par (`estado`, `cidade`), então municípios homônimos em estados diferentes não se misturam. |
| `estrategia` | string | `"sequencial"` ou `"concorrente"` |

### Requisição agregador → posto

```json
{
  "operacao": "consultar",
  "estado": "PA",
  "combustivel": "gasolina_comum",
  "cidade": "Belém"
}
```

Não há campo `estrategia` aqui — a estratégia é responsabilidade do agregador.

### Resposta posto → agregador

Sucesso:
```json
{
  "posto": "A",
  "estado": "PA",
  "cidade": "Belém",
  "combustivel": "gasolina_comum",
  "preco": 6.19,
  "status": "sucesso"
}
```

Cidade não atendida por esse posto (no estado informado):
```json
{
  "posto": "C",
  "estado": "PA",
  "cidade": "Belém",
  "status": "nao_atendida"
}
```

Erro na requisição (estado ou combustível inválido, etc.):
```json
{
  "posto": "A",
  "status": "erro",
  "mensagem": "combustível inválido"
}
```

### Resposta agregador → cliente

```json
{
  "consulta": {
    "combustivel": "gasolina_comum",
    "estado": "PA",
    "cidade": "Belém",
    "estrategia": "concorrente"
  },
  "resultados": [
    {"posto": "B", "estado": "PA", "cidade": "Belém", "combustivel": "gasolina_comum",
     "preco": 6.09, "status": "sucesso"},
    {"posto": "A", "estado": "PA", "cidade": "Belém", "combustivel": "gasolina_comum",
     "preco": 6.19, "status": "sucesso"}
  ],
  "indisponiveis": [
    {"posto": "C", "estado": "PA", "cidade": "Belém", "status": "nao_atendida"},
    {"posto": "D", "status": "timeout"}
  ],
  "menor_preco": {"posto": "B", "preco": 6.09},
  "tempo_ms": 612.4
}
```

- `resultados` sempre vem ordenado em ordem crescente de preço. Cada item é a resposta do posto repassada sem alteração.
- `tempo_ms` é um número decimal (milissegundos, uma casa), medido pelo agregador do início ao fim da consulta aos postos.
- `indisponiveis` lista postos que não participam do ranking (não atendem à cidade, estão fora do ar, excederam o timeout ou responderam com erro).
- `menor_preco` é `null` se nenhum posto responder com sucesso.

Se a requisição for inválida (estado, combustível, cidade ou estratégia), o agregador responde só com o erro, sem consultar os postos:

```json
{"status": "erro", "mensagem": "estado inválido: 'SP' (aceitos: AC, AM, AP, PA, RO, RR, TO)"}
```

## Tratamento de falhas

| Situação | Detectada por | Resposta do agregador ao cliente |
| --- | --- | --- |
| Posto não aceita conexão TCP ou fecha a conexão sem responder | `ConnectionRefusedError` / `ConnectionError` | entrada em `indisponiveis` com `status: "indisponivel"` |
| Posto demora mais de 5 s (na conexão ou na leitura da resposta) | `socket.timeout` | `indisponiveis` com `status: "timeout"` |
| Posto responde `status: "erro"` ou JSON inválido | resposta do posto | `indisponiveis` com `status: "erro"` |
| JSON mal formado vindo do cliente | `json.JSONDecodeError` | fecha a conexão; log no servidor |
| Estado, combustível, cidade ou estratégia inválidos | validação na entrada | retorna `{"status": "erro", "mensagem": "..."}` ao cliente |

## Encerramento de conexão

Conexão **curta** (um pedido, uma resposta, fechamento): o lado que terminou de ler/escrever fecha o socket. Não há `KEEPALIVE` nem reutilização de conexão nesta versão.

## Versão

`v2` — 16/11/2026. Mudanças devem ser documentadas neste arquivo e refletidas em `src/protocolo.py` (`PROTOCOLO_VERSAO`).

| Versão | Mudança |
| --- | --- |
| `v2` (16/11/2026) | Campo obrigatório `estado` (UF da Região Norte) nas requisições cliente → agregador e agregador → posto; `estado` nas respostas e em `consulta`. |
| `v1` (14/11/2026) | Versão inicial. |
