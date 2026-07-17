## O que muda e por quê

## Checklist

- [ ] `ruff check src/ tests/ warehouse_demo/src/` passa localmente
- [ ] `pytest tests/ -v` passa localmente
- [ ] Se a mudança afeta dados/pipeline: rodei `python src/run_all.py`
      do zero e confirmei que termina sem erros
- [ ] Atualizei o `CHANGELOG.md` sob `[Unreleased]`
- [ ] Se isso é uma decisão de design não trivial, adicionei uma
      entrada em `docs/adr/`
- [ ] Se mudei a estrutura de dados/colunas, atualizei
      `docs/data_dictionary.md`

## Issue relacionada

Closes #
