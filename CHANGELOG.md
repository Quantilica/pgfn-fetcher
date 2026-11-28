# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

## [0.4.0] - 2026-11-28

### Adicionado

- `catalog`: `DiscoveryFailure`, `DiscoveryReport.failures`/`ambiguous_files`/`root_error` e `group_failures(dataset)`.
- `lake`: `DATASET_DESCONHECIDO`, valor que `_match_pgfn_dataset` devolve para nome que não casa com dataset.

### Corrigido

- `catalog`/`plugin`: trimestre cujo ZIP de um dataset some da listagem (nome trocado) deixa de sair do catálogo em silêncio. O `DiscoveryReport` já contava `missing`, mas ninguém o lia: agora é falha de descoberta. No `sync`, cada falha é um erro `descoberta:<dataset>:<trimestre>` no resultado e no `--summary-json` (saída 3 se algo baixou, 1 se nada baixou; os demais trimestres seguem). No `check`, vira um item `skip-unavailable` com motivo `listing-error` (causa em `entry["error"]` e `entry["error_class"]`), o `check` sai 0 e grava o plano dos demais; o `sync --from-plan` (`quantilica-cli` 0.30.1) conta o item como erro. Só o `check` tolera; os avisos em WARNING listam os itens.
- `catalog`: dataset com mais de um arquivo no trimestre agora avisa em WARNING quais são os arquivos e que usa o primeiro em ordem alfabética.
- `catalog`/`client`: `discover_trimesters` não engole mais a exceção da raiz (devolvia `[]`, igual a "sem trimestres"). A descoberta registra a causa (`root_error`) e avisa em WARNING que usa o catálogo aritmético de reserva, que não confere o que a fonte publica (arquivo renomeado só aparece como 404 no download). Trimestres sem listagem (nome fixo) também entram num aviso único. O catálogo de reserva continua sendo usado.
- `client`: `PgfnClient.download_file` chamava `download_with_manifest` com `manifest_path=` e sem `source_id`, `dataset_id` e `producer` (`TypeError` em qualquer chamada real; o teste mockava o método do core). Agora recebe `dataset_id` (obrigatório), `source_id="pgfn"`, `producer="pgfn-fetcher"`, `force` e `expected_format` (por padrão, o da extensão do destino, de modo que página de erro com HTTP 200 não vira arquivo) e devolve o `Path` baixado, como o core, em vez de um manifesto. Testada com o `download_with_manifest` real sobre transporte simulado. Nada no monorepo a chamava.
- `client`: o cliente da descoberta deixa de ser um `HttpClient` próprio e passa a ser o cliente padrão do host, que respeita `QUANTILICA_HTTP_*`, `QUANTILICA_SSL_VERIFY` e o bundle de CA. Sem o host instalado, cai num cliente do core com a verificação TLS lida do ambiente.
- `lake`: `_match_pgfn_dataset` devolvia `sida` para qualquer nome desconhecido, e o conversor gravava esse bruto no dataset errado. Agora devolve `desconhecido` e o `convert` registra um erro (`ConvertResult.errors`, o host sai 1) e um log ERROR com o nome, sem converter o arquivo. O sidecar `.manifest.json` é ignorado antes da classificação. O nome `*Nao_Previdenciario*` também deixa de cair em `previdenciario` (a checagem do SIDA passa a vir antes).

### Alterado

- Dependência de desenvolvimento: `quantilica-cli>=0.30.1`.

## [0.3.1] - 2026-11-19

### Adicionado

- Testes: identidade do registro conferida.

### Alterado

- CI e infraestrutura alinhados ao template (fetcher-template v0.2.1).

### Corrigido

- `lake`: o build sem mudança não abre mais o ZIP do bruto. A conversão declara ao lake, antes da primeira gravação, todas as saídas do bruto (`origin_outputs`: uma por membro CSV com dados) e o build só pula o bruto quando `LakeWriter.origin_complete` confirma, pelos rodapés e pelo sidecar, que todas existem com o sha256 atual (e que a partição do nome não mudou); `skipped` conta as saídas. Uma conversão interrompida ou um membro que falhou deixa de virar pulo permanente: o bruto é reaberto e só o que falta é gravado; erros determinísticos de membro seguem aparecendo a cada build. Lake gravado sem a declaração (inclusive o anterior à colisão `PREV_-1`/`PREV_1`) reconverte uma vez. Mesma contagem de `converted`/`skipped`/`errors`; `force` e bruto novo seguem convertendo. Exige `quantilica-analytics>=0.15.0`.
- `lake`: a pré-checagem do build sem mudança (`origin_complete`) deixa de derrubar o `convert` inteiro quando o sidecar não é confiável e o bruto está ilegível (o hash levanta `OSError`/erro de armazenamento). A falha é registrada em log e o bruto segue o caminho completo, que acumula os erros por membro como antes.
- CI: o pyproject declara o PyPI antes do índice Quantilica (`[[tool.uv.index]]`), e o workflow perde `--index` e `--index-strategy`. Com a estratégia padrão `first-index`, o `uv sync` só consulta o índice para o que não está no PyPI (`quantilica-analytics`) e deixa de receber o 503 intermitente que o GitHub Pages devolve a caminhos inexistentes.

## [0.3.0] - 2026-11-14

### Adicionado
- O fetcher declara os fatos da fonte (`FetcherInfo`: id canônico, apelidos, órgão, licença, página e cadência) para o registro de fetchers da Quantilica.

### Alterado
- Requer `quantilica-core>=0.19.0` (e `quantilica-cli>=0.17.0` como host).
- `FetcherInfo.licenca` passa a declarar a licença da fonte: Sem licença declarada; dados públicos pela Lei 12.527/2011 (LAI) e Decreto 8.777/2016.

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

