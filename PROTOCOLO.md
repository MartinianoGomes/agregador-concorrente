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
  "combustivel": "gasolina_comum",
  "cidade": "Belém",
  "estrategia": "concorrente"
}
```

| Campo | Tipo | Valores aceitos |
| --- | --- | --- |
| `operacao` | string | `"consultar"` |
| `combustivel` | string | `"gasolina_comum"`, `"gasolina_aditivada"`, `"etanol"`, `"diesel_s10"` |
| `cidade` | string | Nome livre (normalizado no servidor: sem acentos, caixa baixa) |
| `estrategia` | string | `"sequencial"` ou `"concorrente"` |

### Requisição agregador → posto

```json
{
  "operacao": "consultar",
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
  "cidade": "Belém",
  "combustivel": "gasolina_comum",
  "preco": 6.19,
  "status": "sucesso"
}
```

Cidade não atendida por esse posto:
```json
{
  "posto": "C",
  "cidade": "Belém",
  "status": "nao_atendida"
}
```

Erro na requisição (JSON inválido, combustível desconhecido, etc.):
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
    "cidade": "Belém",
    "estrategia": "concorrente"
  },
  "resultados": [
    {"posto": "B", "preco": 6.09, "status": "sucesso"},
    {"posto": "A", "preco": 6.19, "status": "sucesso"}
  ],
  "indisponiveis": [
    {"posto": "C", "status": "nao_atendida"},
    {"posto": "D", "status": "timeout"}
  ],
  "menor_preco": {"posto": "B", "preco": 6.09},
  "tempo_ms": 612
}
```

- `resultados` sempre vem ordenado em ordem crescente de preço.
- `indisponiveis` lista postos que não participam do ranking (não atendem à cidade, estão fora do ar ou excederam o timeout).
- `menor_preco` é `null` se nenhum posto responder com sucesso.

## Tratamento de falhas

| Situação | Detectada por | Resposta do agregador ao cliente |
| --- | --- | --- |
| Posto não aceita conexão TCP | `ConnectionRefusedError` | entrada em `indisponiveis` com `status: "indisponivel"` |
| Posto demora mais de 5 s | `socket.timeout` | `indisponiveis` com `status: "timeout"` |
| JSON mal formado vindo do cliente | `json.JSONDecodeError` | fecha a conexão; log no servidor |
| Combustível desconhecido | validação na entrada | retorna `{"status": "erro", "mensagem": "..."}` ao cliente |

## Encerramento de conexão

Conexão **curta** (um pedido, uma resposta, fechamento): o lado que terminou de ler/escrever fecha o socket. Não há `KEEPALIVE` nem reutilização de conexão nesta versão.

## Versão

`v1` — publicada em 14/11/2026. Mudanças devem ser documentadas neste arquivo e refletidas em `src/protocolo.py`.
