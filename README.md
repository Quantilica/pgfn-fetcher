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

## Licença

Distribuído sob licença MIT. Consulte [LICENSE](LICENSE) para mais detalhes.
