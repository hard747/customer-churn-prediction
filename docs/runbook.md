# Runbook operacional

Guia de "o que fazer se algo falhar" — pensado para que alguém (incluindo
o seu eu do futuro) consiga diagnosticar um problema sem reler todo o
código.

## Execução normal

```bash
python -m venv .venv && source .venv/bin/activate   # ou .venv\Scripts\activate no Windows
pip install -r requirements.txt
python src/run_all.py
```

Tempo esperado: ~3–6 minutos (o treinamento com `GridSearchCV` dos 3
modelos é a etapa mais longa).

## Problemas comuns

### `ModuleNotFoundError: No module named 'pandas'` (ou qualquer pacote)
**Causa:** o ambiente virtual não está ativado, ou o `pip install` não
terminou de rodar.
**Solução:** confirmar que o prompt mostra `(.venv)`; se não, ativar de
novo. Reinstalar com `pip install -r requirements.txt`.

### `ModuleNotFoundError: No module named 'db'` (ou `train_models`, etc.) ao rodar um script isolado
**Causa:** os scripts de `src/` se importam entre si assumindo que
`src/` está em `sys.path` (o `run_all.py` faz isso automaticamente). Se
você rodar um script individual a partir de outra pasta, pode falhar.
**Solução:** sempre rodar a partir da raiz do repositório:
`python src/build_database.py` (não `cd src && python build_database.py`
sem ajustar o path).

### A instalação do `jupyter` falha com um erro de caminhos longos no Windows
**Causa:** já resolvido neste repositório — não se usa o metapacote
`jupyter` (que traz o `jupyterlab` com arquivos estáticos de caminho
muito longo, esbarrando no limite do Windows sem *Long Path Support*).
Usa-se apenas `nbformat` + `nbclient` + `ipykernel`, suficientes para
executar notebooks sem UI.
**Se mesmo assim aparecer:** habilitar o Long Path Support no Windows,
ou confirmar que `jupyter`/`jupyterlab` não foi adicionado de volta ao
`requirements.txt`.

### O notebook não executa: `NoSuchKernel` ou similar
**Causa:** o kernel `python3` não está registrado para este ambiente
virtual.
**Solução:**
```bash
python -m ipykernel install --user --name python3 --display-name "Python 3 (customer-churn-prediction)"
```

### `psycopg2.errors.UndefinedColumn: column "contract" does not exist` (ou outra coluna em minúscula)
**Causa:** rodando contra o Postgres, uma consulta em `sql_queries.sql`
tem um identificador com maiúsculas sem aspas duplas. Ver
[ADR-0001](adr/0001-sqlite-por-defecto-postgres-opcional.md).
**Solução:** colunas com maiúsculas devem ficar entre aspas duplas, p.
ex. `"Contract"`, não `Contract`.

### `function round(double precision, integer) does not exist` (Postgres)
**Causa:** `ROUND()` sobre uma coluna `float`/`double precision` sem
conversão — o Postgres só tem essa sobrecarga para `numeric`.
**Solução:** `ROUND(CAST(AVG(coluna) AS NUMERIC), 2)` em vez de
`ROUND(AVG(coluna), 2)`.

### `docker compose up -d` falha com `unable to get image ... dockerDesktopLinuxEngine`
**Causa:** o Docker Desktop não está rodando.
**Solução:** abrir o Docker Desktop e esperar o ícone indicar que o
motor está pronto (`docker info` deve mostrar uma seção `Server:` sem
erros) antes de tentar de novo.

### Os testes de `tests/test_risk_scores.py` são pulados (`SKIPPED`)
**Causa esperada, não é um bug:** `outputs/best_model.joblib` ainda não
existe.
**Solução:** rodar `python src/train_models.py` uma vez (ou
`python src/run_all.py` completo) para gerá-lo. No CI isso não acontece
porque o arquivo está versionado no repositório.

### `pd.qcut` falha ou gera menos de 10 decis
**Causa:** se muitos clientes tiverem exatamente a mesma
`churn_probability` (pouco provável com XGBoost, mais provável com um
modelo com saídas muito discretas), o `qcut` não consegue dividir em 10
quantis únicos e usa `duplicates="drop"`, gerando menos de 10 decis.
**Solução:** não é um erro — `generate_risk_scores.py` já trata esse
caso com `duplicates="drop"`. Se o número de decis resultante importar
para o consumo no Power BI, validar `risk_decile.nunique()` antes de
usá-lo.

## Como voltar a um estado limpo

Se algo ficou em um estado estranho (banco de dados corrompido,
artefatos gerados pela metade):

```bash
rm -f data/churn.db outputs/*.csv outputs/*.joblib
rm -rf outputs/sql_analysis
rm -f reports/figures/*.png
python src/run_all.py
```

Isso reconstrói tudo a partir do CSV bruto (`data/Telco-Customer-Churn.csv`,
que está versionado e nunca é apagado).

## Contato / responsável

Projeto de portfólio de autor único — ver [README](../README.md#licença-e-autoria).
