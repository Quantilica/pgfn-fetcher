# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [Não lançado]

### Adicionado
- O fetcher declara os fatos da fonte (`FetcherInfo`: id canônico, apelidos, órgão, licença, página e cadência) para o registro de fetchers da Quantilica.

### Alterado
- Requer `quantilica-core>=0.19.0` (e `quantilica-cli>=0.17.0` como host).

## [0.2.3] - 2026-11-09

### Corrigido
- `lake` (`previdenciario`): quando o ZIP trazia os membros `PREV_-1` e `PREV_1` (caso de 2026-T3), o lake guardava só o menor e perdia as linhas da região 1 (2.696.362 linhas em vez de 3.397.082). Membros de um mesmo ZIP nunca mais compartilham o mesmo arquivo de saída. Exige reconversão de 2026-T3: apague `previdenciario/ano=2026/trimestre=3/` do lake e converta de novo (só esse trimestre é afetado; os demais não mudam de nome). Só o `--force` não basta, porque o arquivo antigo, de outra chave, ficaria ao lado dos novos e duplicaria linhas.

### Adicionado
- Documentação dos dados em `docs/`, conforme a norma de documentação dos dados: página, dicionário de todas as variáveis e esquema de referência para cada um dos três datasets. Um teste a verifica.

## [0.2.2] - 2026-11-06

### Corrigido
- `lake`: o membro de ZIP só vira CSV de dados se terminar em `.csv`; `~$*`, `md5_*`, `._*` e `__MACOSX/` são ignorados (antes bastava o nome conter `.csv`).

## [0.2.1] - 2026-11-05

### Corrigido

- Lake `previdenciario`: os arquivos publicados (2020-T1 a 2026-T3) estão em cp1252, não em UTF-8, e todos os membros falhavam na conversão (`'utf-8' codec can't decode byte 0xed`). O encoding declarado passa a `cp1252`, como `sida` e `fgts`. Reconverta `previdenciario` com `--force`.

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

