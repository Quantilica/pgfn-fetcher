---
dataset:
  id: previdenciario
  fonte: pgfn
  titulo: Dívida ativa previdenciária
  resumo: Inscrições em dívida ativa da União de natureza previdenciária, com situação, tipo de crédito e valor consolidado, em fotografias trimestrais.
  orgao: Procuradoria-Geral da Fazenda Nacional (PGFN)
  pagina_oficial: https://dadosabertos.pgfn.gov.br
  licenca: "Não informada pela fonte: o diretório de dados abertos da PGFN não traz licença nem termo de uso (conferido em 2026-11-09)."
  periodicidade: trimestral; cada arquivo é a fotografia do estoque no fim do trimestre
  cobertura: {inicio: 2020-01, fim: em-curso}
  unidade: uma inscrição em dívida ativa previdenciária de um devedor, numa fotografia trimestral
  granularidade: {espacial: "UF do devedor (até 2022-T3, UF da unidade responsável)", temporal: trimestre}
  formato_bruto: ZIP com vários CSVs, separador ponto e vírgula, Windows-1252, cabeçalho na primeira linha, valores com ponto decimal; até 2022-T3 um CSV por UF, desde 2022-T4 um CSV por região da PGFN
  lake: {estado: convertido, particoes: [ano, trimestre], chave: [ano, trimestre, cpf_cnpj, numero_inscricao], colunas: 16}
  unidades_de_medida:
    valor_consolidado: R$
  dados_pessoais:
    - {coluna: cpf_cnpj, categoria: "CPF mascarado (pessoa física) ou CNPJ (pessoa jurídica)"}
    - {coluna: cnpj_basico, categoria: "raiz do CNPJ (pessoa jurídica)"}
    - {coluna: nome_devedor, categoria: "nome de pessoa física ou razão social"}
    - {coluna: uf_devedor, categoria: "UF do devedor"}
    - {coluna: uf_unidade_responsavel, categoria: "UF da unidade da PGFN responsável"}
  eras:
    - {desde: 2022-10, mudanca: "a coluna UF_UNIDADE_RESPONSAVEL passa a se chamar UF_DEVEDOR e os CSVs passam de um por UF a um por região da PGFN"}
  revisado_em: 2026-11-09
  versao_fetcher: 0.2.2
---

# Dívida ativa previdenciária

## Resumo

Inscrições em dívida ativa da União de natureza previdenciária (contribuições à seguridade social), publicadas pela PGFN. Cada linha liga um devedor a uma inscrição, com a situação da cobrança, o tipo de crédito e o valor consolidado.

## Ficha técnica

<!-- gerado:ficha -->

| Campo | Valor |
|---|---|
| Dataset | `pgfn/previdenciario` |
| Órgão | Procuradoria-Geral da Fazenda Nacional (PGFN) |
| Página oficial | https://dadosabertos.pgfn.gov.br |
| Licença | Não informada pela fonte: o diretório de dados abertos da PGFN não traz licença nem termo de uso (conferido em 2026-11-09). |
| Periodicidade | trimestral; cada arquivo é a fotografia do estoque no fim do trimestre |
| Cobertura | 2020-01 a em-curso |
| Unidade (uma linha) | uma inscrição em dívida ativa previdenciária de um devedor, numa fotografia trimestral |
| Granularidade | espacial: UF do devedor (até 2022-T3, UF da unidade responsável); temporal: trimestre |
| Formato bruto | ZIP com vários CSVs, separador ponto e vírgula, Windows-1252, cabeçalho na primeira linha, valores com ponto decimal; até 2022-T3 um CSV por UF, desde 2022-T4 um CSV por região da PGFN |
| Estado no lake | convertido |
| Partições | `ano`, `trimestre` |
| Chave | `ano`, `trimestre`, `cpf_cnpj`, `numero_inscricao` |
| Colunas | 16 |
| Unidades de medida | `valor_consolidado`: R$ |
| Dados pessoais | `cpf_cnpj` (CPF mascarado (pessoa física) ou CNPJ (pessoa jurídica)); `cnpj_basico` (raiz do CNPJ (pessoa jurídica)); `nome_devedor` (nome de pessoa física ou razão social); `uf_devedor` (UF do devedor); `uf_unidade_responsavel` (UF da unidade da PGFN responsável) |
| Eras | 2022-10: a coluna UF_UNIDADE_RESPONSAVEL passa a se chamar UF_DEVEDOR e os CSVs passam de um por UF a um por região da PGFN |
| Revisado em | 2026-11-09 |
| Versão do fetcher | 0.2.2 |

## Origem e coleta

- O fetcher baixa `Dados_abertos_Previdenciario.zip` de cada pasta trimestral do diretório de dados abertos da PGFN.
- No bruto, o arquivo se chama `previdenciario/previdenciario_<ano>-T<NN>@AAAAMMDD.zip`, em que o sufixo é a data da coleta.
- Dentro do ZIP há CSVs `arquivo_lai_PREV_<UF ou região>_<AAAAMM>.csv`. O ZIP de 2022-T4 traz também uma pasta `nao-PREV/` sem arquivos de dados, que o fetcher ignora.
- Conferido em 2026-11-09 pela listagem do bruto: 27 trimestres, de 2020-T1 a 2026-T3.

## Conteúdo

- Uma linha por inscrição e devedor. Nas fotografias examinadas todos os devedores são `Principal` e o número de inscrição não se repete (2020-T1: 5.059.821 linhas; 2026-T3: 3.397.082 linhas nos CSVs e 2.696.362 no lake, veja os cuidados de uso).
- `tipo_credito` mostra, em 2026-T3, a classe do crédito: `OUTROS` em quase todas as linhas, e poucas de `CONTRIBUICAO NAO REPASSADA`, `AFERICAO INDIRETA`, `SOLIDARIEDADE`, `SUCUMBENCIA`, `ARREMATACAO`, `Não Informado` e `RECLAMATORIA TRABALHISTA - JUST.TRABALHO`.
- O conjunto previdenciário não tem as colunas `receita_principal`, `entidade_responsavel` e `unidade_inscricao` dos outros dois.

## Variáveis

A fonte não publica dicionário. As descrições abaixo vêm dos nomes das colunas e dos valores observados em 2020-T1, 2022-T4 (só o cabeçalho) e 2026-T3.

| Coluna no lake | Na fonte | Tipo | Descrição | Unidade / códigos | Período |
|---|---|---|---|---|---|
| `cpf_cnpj` | `CPF_CNPJ` | texto | CPF mascarado ou CNPJ do devedor. CPF: `XXX999.999XX`; CNPJ: `99.999.999/9999-99` | — | todo |
| `tipo_pessoa` | `TIPO_PESSOA` | texto | Natureza do devedor | `Pessoa física`, `Pessoa jurídica` | todo |
| `tipo_devedor` | `TIPO_DEVEDOR` | texto | Papel do devedor na inscrição; só `Principal` nas fotografias examinadas | `Principal` | todo |
| `nome_devedor` | `NOME_DEVEDOR` | texto | Nome da pessoa física ou razão social | — | todo |
| `uf_unidade_responsavel` | `UF_UNIDADE_RESPONSAVEL` | texto | UF da unidade da PGFN responsável | sigla | até 2022-T3 |
| `uf_devedor` | `UF_DEVEDOR` | texto | UF do devedor | sigla | desde 2022-T4 |
| `unidade_responsavel` | `UNIDADE_RESPONSAVEL` | texto | Unidade da PGFN responsável; `Sem Informação` em alguns casos | — | todo |
| `numero_inscricao` | `NUMERO_INSCRICAO` | texto | Número da inscrição | — | todo |
| `tipo_situacao_inscricao` | `TIPO_SITUACAO_INSCRICAO` | texto | Grupo da situação | `Em cobrança`, `Benefício Fiscal`, `Garantia`, `Suspenso por decisão judicial`, `Em negociação` | todo |
| `situacao_inscricao` | `SITUACAO_INSCRICAO` | texto | Situação detalhada; a grafia mudou entre 2020 e 2026 (`AJUIZAMENTO / DISTRIBUICAO` virou `AJUIZAMENTO   DISTRIBUICAO`, com espaços no lugar da barra) | por exemplo `PARCELAMENTO RESCINDIDO`, `NEGOCIADO NO SISPAR` | todo |
| `tipo_credito` | `TIPO_CREDITO` | texto | Classe do crédito | ver conteúdo | todo |
| `data_inscricao` | `DATA_INSCRICAO` | texto | Data da inscrição, como a fonte publica; `01/01/1000` aparece como valor de preenchimento | dd/mm/aaaa | todo |
| `indicador_ajuizado` | `INDICADOR_AJUIZADO` | texto | Se a cobrança foi ajuizada | `SIM`, `NAO` | todo |
| `valor_consolidado` | `VALOR_CONSOLIDADO` | decimal | Valor consolidado da inscrição na data da fotografia | R$ | todo |
| `regiao_pgfn` | — (nome do CSV) | texto | Código tirado do nome do CSV dentro do ZIP; veja os cuidados de uso | ver cuidados de uso | todo |
| `cnpj_basico` | — (gerada) | texto | Raiz de oito dígitos do CNPJ; nula para pessoa física | 8 dígitos | todo |
| `ano` | — (partição) | inteiro | Ano do trimestre | — | todo |
| `trimestre` | — (partição) | inteiro | Trimestre | 1 a 4 | todo |

## No lake

- Dataset `pgfn/previdenciario`, particionado por `ano` e `trimestre`; um Parquet por CSV do ZIP.
- Todas as colunas são lidas como texto; só `valor_consolidado` vira decimal. O texto é decodificado de Windows-1252 para UTF-8.
- Nomes de coluna normalizados (minúsculas, sem acento); a coluna de UF tem dois nomes, conforme a era.
- `cnpj_basico` e `regiao_pgfn` são acrescentadas pelo conversor.
- CSVs só com cabeçalho são ignorados.

## Cuidados de uso

- **Lake de 2026-T3 gerado pela versão 0.2.2 ou anterior perde linhas.** O ZIP de 2026-T3 traz os CSVs `PREV_-1` (1 linha) e `PREV_1` (700.720 linhas). Até a versão 0.2.2 os dois viravam o mesmo arquivo Parquet e o de uma linha sobrescrevia o outro (a região 1 inteira sumia): o lake tinha 2.696.362 linhas, e os CSVs têm 3.397.082 (conferido em 2026-11-09). A partir da versão 0.2.3 cada CSV do ZIP tem seu próprio arquivo. Para corrigir um lake antigo, apague `previdenciario/ano=2026/trimestre=3/` e converta de novo; só `--force` não basta, porque o arquivo antigo ficaria ao lado dos novos e duplicaria linhas.
- **Fotografias, não fluxo.** Cada trimestre é o estoque inteiro; compare estoques entre trimestres e não some trimestres.
- **Data de preenchimento.** `data_inscricao` vale `01/01/1000` em 7.350 linhas de 2020-T1 e 2.719 de 2026-T3, provavelmente por ausência da data; a fonte não explica.
- **`regiao_pgfn` não é confiável como região.** Os arquivos por UF (2020-T1) recebem todos o valor `1`; desde 2022-T4 o valor é o número do CSV. Em 2026-T3 aparece o valor `-1`, que a fonte não explica.
- **Duas colunas de UF**, conforme a era (veja `sida`); não as una sem decidir o significado.
- **Pessoa física:** o nome do devedor vem completo mesmo com o CPF mascarado; trate-o como dado pessoal.
- **Valores por pessoa jurídica** estão no CNPJ completo; use `cnpj_basico` para agrupar por empresa.

## Exemplos

Valor consolidado por tipo de crédito e situação (grupo), em R$ milhões, no trimestre de 2020-T1, que não sofre a perda de linhas de 2026-T3:

```python
import duckdb

duckdb.sql("""
    SELECT tipo_credito, tipo_situacao_inscricao,
           count(*) AS inscricoes,
           round(sum(valor_consolidado) / 1e6, 1) AS valor_mi
    FROM read_parquet('lake/pgfn/previdenciario/**/*.parquet', hive_partitioning = true, union_by_name = true)
    WHERE ano = 2020 AND trimestre = 1
    GROUP BY ALL
    ORDER BY valor_mi DESC
""").show()
```

## Referências

- Diretório de dados abertos da PGFN: https://dadosabertos.pgfn.gov.br
