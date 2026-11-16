# Protocolo de Aplicação — Agregador de Combustíveis

Protocolo JSON sobre TCP utilizado entre cliente ↔ agregador e entre agregador ↔ postos.

## Codificação e enquadramento

- **Encoding:** UTF-8.
- **Enquadramento:** uma mensagem por linha. Cada mensagem é um objeto JSON válido terminado em `\n` (LF, `0x0A`).
- **Tamanho máximo recomendado:** 64 KiB por mensagem.

## Rastreamento (`id`)

Todas as mensagens aceitam o campo opcional `id` (texto, 1 a 64 caracteres), usado para seguir uma consulta pelos três tipos de processo:

- o **cliente** gera um `id` curto (8 caracteres hexadecimais) em cada consulta;
- o **agregador** repassa o mesmo `id` a todos os postos e o devolve na resposta ao cliente (se o cliente não mandar, o agregador cria um);
- cada **posto** devolve o `id` que recebeu.

Com a opção `--rastreio` (cliente, agregador e postos), cada processo escreve em stderr uma linha por mensagem enviada ou recebida:

```
11:48:31.997 [agregador | consulta-posto_0] → ENVIA para posto A (127.0.0.1:6001) | id=81e284c6 | 105 bytes | {"operacao": "consultar", ...}
11:48:31.997 [posto A | conexao-42662] ← RECEBE de agregador (127.0.0.1:42662) | id=81e284c6 | 105 bytes | {"operacao": "consultar", ...}
11:48:37.000 [agregador | consulta-posto_2] ✕ posto C sem resposta: timeout após 5005 ms (limite 5 s) | id=81e284c6
```

Campos: horário com milissegundos, parte e thread, sentido (`→ ENVIA` / `← RECEBE`), outro lado da conexão (nome e `host:porta`), `id`, tamanho em bytes e o JSON completo como trafegou. Mensagens com JSON inválido também são registradas. Além das mensagens, o agregador registra o tempo de resposta de cada posto, timeouts e conexões recusadas. O posto registra o atraso artificial (`--latencia-ms`).

## Operações

Apenas a operação `consultar` é definida nesta versão.

### Requisição cliente → agregador

```json
{
  "id": "81e284c6",
  "operacao": "consultar",
  "estado": "PA",
  "combustivel": "gasolina_comum",
  "cidade": "Belém",
  "estrategia": "concorrente"
}
```

| Campo | Tipo | Valores aceitos |
| --- | --- | --- |
| `id` | string (opcional) | Id de rastreio, 1 a 64 caracteres |
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
  "cidade": "Belém",
  "id": "81e284c6"
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
  "status": "sucesso",
  "id": "81e284c6"
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
  "id": "81e284c6",
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
{"status": "erro", "mensagem": "estado inválido: 'SP' (aceitos: AC, AM, AP, PA, RO, RR, TO)", "id": "81e284c6"}
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

`v2.1` — 16/11/2026. Mudanças devem ser documentadas neste arquivo e refletidas em `src/protocolo.py` (`PROTOCOLO_VERSAO`).

| Versão | Mudança |
| --- | --- |
| `v2.1` (16/11/2026) | Campo opcional `id` de rastreio em todas as mensagens, ecoado nas respostas; mensagem que não é objeto JSON é rejeitada com `erro`. |
| `v2` (16/11/2026) | Campo obrigatório `estado` (UF da Região Norte) nas requisições cliente → agregador e agregador → posto; `estado` nas respostas e em `consulta`. |
| `v1` (14/11/2026) | Versão inicial. |
