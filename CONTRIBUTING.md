# Guia de contribuição

## Fluxo de branches

- `main` — código estável, sempre funcionando. **Nunca commitem direto na `main`.**
- `feature/<área>-<descrição-curta>` — nova funcionalidade (ex.: `feature/agregador-modo-concorrente`).
- `bugfix/<descrição>` — correção de bug.
- `experimento/<nome>` — scripts e dados de experimento.

## Passo a passo para abrir uma contribuição

1. Suba para o remoto (`git fetch origin`) e atualize sua `main` (`git pull --rebase origin main`).
2. Crie a branch de trabalho a partir da `main`:
   ```bash
   git checkout -b feature/posto-carregar-csv
   ```
3. Faça commits pequenos e com mensagens claras (ver "Convenção de commits" abaixo).
4. Antes de abrir PR, rode os testes locais:
   ```bash
   python -m pytest tests/
   ```
5. Suba a branch e abra um Pull Request no GitHub, marcando pelo menos **um revisor** do grupo.
6. O revisor aprova, e aí quem abriu o PR faz o merge (squash merge recomendado).

## Convenção de commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/pt-br/):

| Prefixo | Quando usar | Exemplo |
| --- | --- | --- |
| `feat:` | nova funcionalidade | `feat(posto): carregar preços do CSV da ANP` |
| `fix:` | correção de bug | `fix(agregador): corrigir timeout em modo sequencial` |
| `docs:` | mudança apenas em documentação | `docs: atualizar PROTOCOLO.md com status nao_atendida` |
| `refactor:` | refatoração sem mudar comportamento | `refactor(cliente): extrair impressão do ranking` |
| `test:` | adicionar/alterar testes | `test(protocolo): cobrir normalizar_cidade` |
| `chore:` | infra, scripts, configuração | `chore: adicionar requirements.txt` |

## Estilo de código

- **Python:** PEP 8. Rodem `python -m black src/ experimentos/ tests/` antes de abrir PR. Configurem a linha máxima em 100 caracteres.
- **Imports:** agrupem em três blocos (stdlib, terceiros, locais), separados por uma linha em branco.
- **Docstrings:** obrigatórias em módulos e funções públicas. Use o estilo PEP 257.
- **Type hints:** use sempre que possível.

## Arquivos que NÃO devem ser commitados

Já listados no `.gitignore`:
- `data/anp_bruto.csv` e `data/anp_posto_*.csv` (cada um gera localmente)
- `resultados/*.json`, `resultados/*.csv`, `resultados/*.png`
- Qualquer `.venv/`, `__pycache__/`, `.env`

## Comunicação do grupo

- Para decisões pequenas: comentário no doc do Google Docs (apontado no README) ou no próprio PR.
- Para mudanças arquiteturais: criem uma **issue** no GitHub e discutam lá antes de abrir PR.
