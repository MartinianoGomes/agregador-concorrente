# Documentação

Materiais auxiliares do projeto.

## Diagramas

Os PNGs (250 dpi) são gerados com matplotlib pelo script `gerar_diagramas.py`:

```bash
python docs/gerar_diagramas.py
```

- `diagrama_casos_de_uso.png`: atores (Usuário, Posto de combustível, Operador) e casos de uso. Consultar preços inclui informar estado e município, escolher combustível e estratégia e consultar os 4 postos. Rejeitar consulta inválida e Tratar falha de posto são extensões.
- `diagrama_componentes.png`: Clientes (linha de comando e interface gráfica), Agregador (com recepção, despacho e consolidação), as 4 instâncias de Posto, as interfaces `IConsulta` e `IPosto` (JSON sobre TCP), a biblioteca `protocolo.py`, os Experimentos e o caminho dos dados da ANP até os postos.
- `diagrama_sequencia.png`: uma consulta completa com o `id` de rastreio. Um `alt` separa a requisição inválida da válida; dentro da válida, outro `alt` mostra o modo concorrente (`par`) e o sequencial (`loop`). Uma nota resume os status de falha.

Os PNGs ficam versionados.
