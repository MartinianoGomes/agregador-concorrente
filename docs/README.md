# Documentação

Materiais auxiliares do projeto.

## Doc vivo de requisitos e modelagem UML

A especificação de requisitos e os diagramas UML ficam em um **doc colaborativo do Claude Docs** (exportável para Google Docs):

<https://claude.ai/artifact/T1jSLmcGik6xKXDqK5aL2B>

> Como importar para Google Docs: fazer upload do `.docx` exportado para o Drive, abrir com Google Docs e aceitar comentários do grupo.

## Diagramas

Os PNGs (300 dpi) são gerados com matplotlib pelo script `gerar_diagramas.py`:

```bash
python docs/gerar_diagramas.py
```

- `diagrama_casos_de_uso.png`
- `diagrama_arquitetura.png`
- `diagrama_sequencia.png`

Ficam versionados — são a parte visual da entrega final e pesam algumas centenas de KB cada.
