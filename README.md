# pgfn-fetcher

[![CI](https://github.com/Quantilica/pgfn-fetcher/actions/workflows/test.yml/badge.svg)](https://github.com/Quantilica/pgfn-fetcher/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Coletor e conversor Lake Hive para dados abertos de **Procuradoria-Geral da Fazenda Nacional — Dívida Ativa da União** (`pgfn`), parte do ecossistema [Quantilica](https://quantilica.com).

## Instalação

### Via CLI Quantilica (recomendado)

```bash
quantilica install pgfn
```

Para instalar com suporte à conversão Parquet Lake:

```bash
quantilica install pgfn --extra analysis
```

### Como biblioteca Python

```bash
uv add pgfn-fetcher --index https://index.quantilica.com/simple/
```

Com o extra de análise analítica:

```bash
uv add 'pgfn-fetcher[analysis]' --index https://index.quantilica.com/simple/
```

## Uso via CLI

```bash
# Listar conjuntos disponíveis
quantilica pgfn list

# Verificar novos arquivos e frescor
quantilica pgfn check

# Sincronizar arquivos para o diretório local bruto
quantilica pgfn sync -o /data/pgfn

# Converter acervo bruto para o Universal Hive Parquet Lake
quantilica pgfn convert /data/pgfn /data/lake
```

## Falha de descoberta

O catálogo vem da listagem real do site da PGFN. Um trimestre cujo arquivo de um
dataset não está mais na listagem (por exemplo, porque o ZIP mudou de nome) é falha
de descoberta, não ausência: o `sync` direto a conta como erro `descoberta:<dataset>:<trimestre>`
(saída 3 se algo baixou, 1 se nada baixou) e o `check` grava, no plano, um item
`skip-unavailable` com motivo `listing-error` (o `check` sai 0; o `sync --from-plan` do
host, `quantilica-cli` 0.30.1 ou mais novo, conta o item como erro). Listagem da raiz
que falha, trimestre sem listagem e dataset com mais de um arquivo no trimestre ficam em
WARNING, com a causa e os nomes.

## Documentação dos dados

O que cada dataset contém, de onde vem, como chega ao lake e os cuidados de uso: [docs/README.md](docs/README.md).

## Licença

Distribuído sob licença MIT. Consulte [LICENSE](LICENSE) para mais detalhes.
