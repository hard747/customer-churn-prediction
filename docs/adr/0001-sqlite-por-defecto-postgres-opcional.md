# ADR-0001: SQLite por padrão, Postgres opcional via SQLAlchemy

**Estado:** Aceita
**Data:** 2026-07-16

## Contexto

O projeto precisa persistir o dataset em um banco de dados para poder
rodar consultas SQL de diagnóstico (requisito explícito do projeto). Este
é um repositório de portfólio: qualquer pessoa que o clone deve
conseguir reproduzi-lo com o menor número de passos possível, sem
instalar nem configurar um servidor de banco de dados. Ao mesmo tempo,
quer-se poder demonstrar competência com um motor de banco de dados
"real" de produção (Postgres), não só com um arquivo local.

## Decisão

Usar SQLite como motor padrão (arquivo `data/churn.db`, gerado
automaticamente, configuração zero) e suportar Postgres como alternativa
opcional, ativada apenas se a variável de ambiente `DATABASE_URL`
estiver definida. Toda a lógica de conexão se centraliza em `src/db.py`
(`get_engine()`), que devolve um engine do SQLAlchemy — o resto do
código nunca importa `sqlite3` nem `psycopg2` diretamente.

## Alternativas consideradas

- **Postgres obrigatório desde o início** — descartado: obriga quem
  clona o repositório a instalar/configurar um servidor antes de poder
  rodar qualquer coisa, o que quebra o objetivo de "reproduzível com um
  único comando".
- **Só SQLite, sem opção de Postgres** — descartado: não permite
  demonstrar domínio de um motor cliente-servidor real, e não deixa
  caminho de crescimento em direção a um warehouse na nuvem.
- **Duas bases de código separadas (uma para cada motor)** — descartado:
  duplicação de lógica e alto risco de divergirem silenciosamente.

## Consequências

- Positivas: o projeto continua sendo "clone e rode" para qualquer
  revisor, e ao mesmo tempo suporta um motor de produção real sem tocar
  em código de negócio, via Docker Compose ou um Postgres gerenciado
  (Supabase, Neon, Render).
- Negativas / trade-offs: é preciso escrever SQL portável entre os dois
  motores. Na prática isso já causou dois bugs reais descobertos durante
  a migração (sensibilidade a maiúsculas em identificadores sem aspas, e
  `ROUND()` sem sobrecarga para `double precision` no Postgres) —
  documentados em `src/sql_queries.sql` e `src/build_database.py`.
- Revisar esta decisão se o dataset crescer o suficiente para que o
  SQLite deixe de ser viável como padrão (limitado por ser um único
  arquivo sem escrita concorrente real).
