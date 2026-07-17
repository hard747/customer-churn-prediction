# ADR-0008: Simular CRM/ERP normalizando o mesmo dataset, em vez de somar um novo

**Estado:** Aceita
**Data:** 2026-07-16

## Contexto

O padrão enterprise real começa em sistemas de origem (Salesforce, SAP)
que não existem para este projeto de portfólio. Era preciso decidir como
simular essa camada de origem para que `warehouse_demo/` tivesse algo
plausível para extrair.

## Decisão

Normalizar o **mesmo** CSV do Telco Customer Churn (a única fonte de
dados de todo o projeto) em quatro tabelas "raw" que representam o que
diferentes sistemas operacionais exporiam, todas compartilhando
`customerID` como chave real:

- `raw_crm_customers` (perfil demográfico → simula CRM)
- `raw_crm_subscriptions` (contrato e serviços → simula ERP/assinaturas)
- `raw_billing_charges` (faturamento → simula sistema de billing)
- `raw_churn_labels` (sinal histórico de churn)

## Alternativas consideradas

- **Buscar um segundo dataset no Kaggle** (p. ex., um de tickets de
  suporte) para simular uma fonte diferente — descartado: um dataset
  diferente não compartilha uma chave real com o CSV do Telco, então
  qualquer join entre os dois seria fabricado (uniria linhas por posição
  ou por uma chave inventada, não por uma relação real entre clientes).
  Isso é pior prática do que ser explícito sobre estar simulando: um
  join falso pode passar despercebido e gerar conclusões sem sentido;
  uma simulação declarada explicitamente não engana ninguém.
- **Não simular nada, dbt lê direto a tabela `customers` já pronta** —
  descartado: perde-se todo o ponto pedagógico de ter uma camada "raw"
  separada de "staging", que é central ao padrão real (os dados brutos
  chegam sujos/desnormalizados de sistemas de origem diferentes, e a
  limpeza/join acontece na camada de transformação, não antes).

## Consequências

- Positivas: o join em `fct_customer_features.sql` é um join real sobre
  uma chave real (mesmo `customerID` nas quatro tabelas), não uma
  fabricação. A camada raw ainda preserva de propósito o mesmo problema
  de `TotalCharges` como texto com linhas vazias que o CSV original tem,
  para que a limpeza real aconteça em `stg_billing_charges.sql` (dbt) em
  vez de na carga bruta — exatamente o padrão ELT real.
- Negativas / trade-offs: continua sendo, no fundo, um único dataset
  "agindo" como se viesse de três sistemas — não há latência de rede,
  inconsistências de esquema entre fontes, nem defasagens temporais
  entre sistemas que existiriam de verdade em uma integração real com
  Salesforce/SAP. Isso está documentado explicitamente (não escondido)
  em `warehouse_demo/README.md` e nos comentários de
  `warehouse_demo/src/build_raw_tables.py`.
- Revisar esta decisão se em algum momento houver dados reais (ou
  sintéticos mas genuinamente independentes) de um CRM e um sistema de
  billing separados.
