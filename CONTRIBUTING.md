# Guia de contribuição

Este é um projeto de portfólio de autor único, mas segue as mesmas
convenções que se esperariam em um repositório de equipe — documentado
aqui para ficar consistente ao longo do tempo (mesmo que o único
colaborador seja você mesmo, seis meses depois).

## Configuração do ambiente de desenvolvimento

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Antes de abrir um Pull Request

```bash
ruff check src/ tests/ warehouse_demo/src/    # lint
pytest tests/ -v                              # testes
```

Ambos os comandos também rodam no CI (`.github/workflows/ci.yml`); um PR
com CI vermelho não é mesclado. Se você mexeu em `warehouse_demo/`, rode
também `python warehouse_demo/src/flow.py` ponta a ponta contra Postgres
antes de abrir o PR (não está no CI porque exige um banco de dados real
rodando).

## Convenção de commits

[Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/):

```
<tipo>: <descrição breve no imperativo>

[corpo opcional explicando o porquê, não o quê]
```

Tipos usados neste repositório: `feat`, `fix`, `docs`, `chore`, `test`,
`ci`, `refactor`. Exemplos reais deste projeto:

```
feat: pipeline de treinamento com LR, RF e XGBoost
fix: converter AVG para NUMERIC em sql_queries.sql para compatibilidade com Postgres
docs: adicionar ADR sobre backtest retrospectivo de impacto de negócio
```

## Convenção de branches

`<tipo>/<descrição-curta-em-kebab-case>`, por exemplo:
`feat/mlflow-tracking`, `fix/qcut-duplicate-bins`.

## Quando escrever uma ADR

Se a mudança decide *como* algo é resolvido (não só *o que* é
implementado) e essa decisão não é óbvia a partir do código — por
exemplo, escolher uma biblioteca, uma métrica, um padrão de arquitetura,
ou reverter uma decisão anterior — adicionar uma entrada em
[`docs/adr/`](docs/adr/README.md) seguindo o [template](docs/adr/template.md).
Uma correção de bug pontual normalmente não precisa de ADR; uma decisão
de design, sim.

## Gestão de tarefas

Este repositório usa **GitHub Issues + Projects**, não um board externo
(Jira, Trello, etc.) — todo o contexto de uma tarefa (issue, PR,
commits, CI) fica em um só lugar. Usar os templates em
[`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/) ao abrir uma issue.

## Atualizar o CHANGELOG.md

Toda mudança visível (não só refatorações internas) é adicionada sob
`[Unreleased]` no [`CHANGELOG.md`](CHANGELOG.md), na categoria
correspondente (`Added`, `Changed`, `Fixed`, `Removed`).
