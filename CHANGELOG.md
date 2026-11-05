# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

## [0.2.0] - 2026-11-04

### Adicionado
- Catálogo dirigido pela listagem real: `catalog.discover_entries` usa
  `PgfnClient.discover_trimesters` e a listagem de cada trimestre para achar os nomes
  reais (`Nao_Previdenciariozip.zip` em 2022-T4, `Sistema_SIDA.zip` em 2026-T3).
  Listagem de trimestre que falha usa o nome fixo (fallback); arquivo esperado ausente
  não vira entrada (sem 404 diário) e é contado em `DiscoveryReport.missing`.
  `PGFN_DISCOVER=0` desliga a descoberta (testes offline).

### Corrigido
- Lake `sida`: o `Dados_abertos_Sistema_SIDA.zip` de 2026-T3 (sondado por HEAD/Range: 6 membros `arquivo_lai_SIDA_<n>_202609.csv`, cp1252, 13 colunas) traz `CPF_CNPJ` com pontuacao (`84.461.748/0001-81`) e valores com ponto decimal; `cnpj_basico` exigia 14 caracteres e ficava nulo para todos. Agora extrai os 14 digitos. Reconverter `sida` 2026-T3 (e qualquer trimestre com CNPJ formatado) com `--force`.
- Política de frescor volta a F2 (`HEAD_FALLBACK_GET`): `REMOTE_ONLY` (F3, para fontes sem validadores) causava re-download diário de fontes com Last-Modified/ETag, porque descartava o Last-Modified e o nome do arquivo caía em `@hoje`.
- Lake: cada membro de um ZIP vira um arquivo de origem próprio (chave composta
  `zip__membro`). Antes, só o primeiro membro chegava ao lake: o `LakeWriter` tomava os
  seguintes por já convertidos (mesmo `src`/sha256/partição).
- Lake: leitura membro a membro em streaming (sem `ZipFile.read` do membro inteiro) e
  decodificação estrita (`cp1252` para `sida`/`fgts`, `utf-8` para `previdenciario`),
  sem `errors="replace"`: byte inválido vira erro contado. Colunas lidas como texto
  (CNPJ com zero à esquerda não vira inteiro). Período não inferido do nome é erro, não
  mais `2020-T1`. `skipped` passa a contar os membros já convertidos.
- O catálogo para no último trimestre **fechado**: trimestres futuros (ex.: `2026-T4`
  antes da publicação) deixavam de ser agendados e de gerar 404 diário.
- Sem o extra `analysis`, o comando `convert` termina com código 1 e a instrução de instalação (`quantilica install pgfn --extra analysis`), sem traceback.

## [0.1.0] - 2026-11-01

### Adicionado
- Versão inicial do pacote `pgfn-fetcher` (`quantilica pgfn`).
- Suporte a `list`, `check`, `sync` e verificação de frescor via SDK `FetcherApp`.

- Conversor Universal Hive Parquet Lake com `DatasetSpec` em `lake.py`.

