---
dataset:
  id: sida
  fonte: pgfn
  titulo: Dívida ativa não previdenciária (SIDA)
  resumo: Inscrições em dívida ativa da União de natureza não previdenciária, uma linha por inscrição e devedor, com situação e valor consolidado, em fotografias trimestrais.
  orgao: Procuradoria-Geral da Fazenda Nacional (PGFN)
  pagina_oficial: https://dadosabertos.pgfn.gov.br
  licenca: "Não informada pela fonte: o diretório de dados abertos da PGFN não traz licença nem termo de uso (conferido em 2026-11-09)."
  periodicidade: trimestral; cada arquivo é a fotografia do estoque no fim do trimestre
  cobertura: {inicio: 2020-01, fim: em-curso}
  unidade: uma inscrição em dívida ativa de um devedor (principal, corresponsável ou solidário), numa fotografia trimestral
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

# Dívida ativa não previdenciária (SIDA)

## Resumo

Lista das inscrições em dívida ativa da União de natureza não previdenciária (tributos como IRPJ, CSLL, COFINS, PIS e Simples Nacional, multas e outras receitas), mantida pela PGFN no Sistema da Dívida Ativa (SIDA). Cada linha liga um devedor a uma inscrição, com a situação da cobrança e o valor consolidado. Serve para estudar o estoque e a composição da dívida ativa ao longo do tempo.

## Ficha técnica

<!-- gerado:ficha -->

| Campo | Valor |
|---|---|
| Dataset | `pgfn/sida` |
| Órgão | Procuradoria-Geral da Fazenda Nacional (PGFN) |
| Página oficial | https://dadosabertos.pgfn.gov.br |
| Licença | Não informada pela fonte: o diretório de dados abertos da PGFN não traz licença nem termo de uso (conferido em 2026-11-09). |
| Periodicidade | trimestral; cada arquivo é a fotografia do estoque no fim do trimestre |
| Cobertura | 2020-01 a em-curso |
| Unidade (uma linha) | uma inscrição em dívida ativa de um devedor (principal, corresponsável ou solidário), numa fotografia trimestral |
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

- O fetcher lista os trimestres no diretório de dados abertos da PGFN (`<ano>_trimestre_<NN>/`) e baixa o ZIP do conjunto. O nome do ZIP varia entre trimestres (`Dados_abertos_Nao_Previdenciario.zip`, `Nao_Previdenciariozip.zip` em 2022-T4, `Dados_abertos_Sistema_SIDA.zip` em 2026-T3); o fetcher reconhece o conjunto por partes do nome.
- No bruto, o arquivo se chama `sida/sida_<ano>-T<NN>@AAAAMMDD.zip`, em que o sufixo é a data da coleta.
- Dentro do ZIP há CSVs `arquivo_lai_SIDA_<UF ou região>_<AAAAMM>.csv`. O fetcher lê só os arquivos que terminam em `.csv` e ignora lixo de arquivo (`~$*`, `md5_*`, `._*`, `__MACOSX/`).
- Conferido em 2026-11-09 pela listagem do bruto: 27 trimestres, de 2020-T1 a 2026-T3. Os ZIPs de 2020-T1 a 2020-T4 foram baixados em 2021-06-10.

## Conteúdo

- Uma linha por inscrição e devedor. Uma inscrição com corresponsáveis aparece uma vez para o devedor principal e uma para cada corresponsável ou devedor solidário, **repetindo o mesmo valor consolidado**.
- Cobertura real, conferida em duas fotografias: 2022-T3 (24 CSVs, um por UF) com 19.492.158 linhas e 14.647.048 inscrições distintas; 2026-T3 (6 CSVs, um por região) com 49.617.572 linhas e 32.330.195 inscrições distintas.
- `tipo_devedor` em 2026-T3: 32.330.195 principais, 17.232.448 corresponsáveis e 54.929 solidários.
- Datas de inscrição em 2026-T3 vão de 1973 a 2026.

## Variáveis

A fonte não publica dicionário. As descrições abaixo vêm dos nomes das colunas e dos valores observados em 2022-T3 e 2026-T3.

| Coluna no lake | Na fonte | Tipo | Descrição | Unidade / códigos | Período |
|---|---|---|---|---|---|
| `cpf_cnpj` | `CPF_CNPJ` | texto | CPF mascarado ou CNPJ do devedor. CPF: `XXX999.999XX` (12 caracteres, seis dígitos visíveis); CNPJ: `99.999.999/9999-99` (18 caracteres) | — | todo |
| `tipo_pessoa` | `TIPO_PESSOA` | texto | Natureza do devedor | `Pessoa física`, `Pessoa jurídica` | todo |
| `tipo_devedor` | `TIPO_DEVEDOR` | texto | Papel do devedor na inscrição | `PRINCIPAL`, `CORRESPONSAVEL`, `SOLIDARIO` | todo |
| `nome_devedor` | `NOME_DEVEDOR` | texto | Nome da pessoa física ou razão social; nulo em 1.713 linhas de 2022-T3 | — | todo |
| `uf_unidade_responsavel` | `UF_UNIDADE_RESPONSAVEL` | texto | UF da unidade da PGFN responsável pela inscrição | sigla | até 2022-T3 |
| `uf_devedor` | `UF_DEVEDOR` | texto | UF do devedor | sigla | desde 2022-T4 |
| `unidade_responsavel` | `UNIDADE_RESPONSAVEL` | texto | Unidade da PGFN responsável pela inscrição | — | todo |
| `numero_inscricao` | `NUMERO_INSCRICAO` | texto | Número da inscrição em dívida ativa; repete-se entre devedores da mesma inscrição | — | todo |
| `tipo_situacao_inscricao` | `TIPO_SITUACAO_INSCRICAO` | texto | Grupo da situação | `Em cobrança`, `Benefício Fiscal`, `Garantia`, `Suspenso por decisão judicial`, `Em negociação` | todo |
| `situacao_inscricao` | `SITUACAO_INSCRICAO` | texto | Situação detalhada da inscrição | por exemplo `ATIVA EM COBRANCA`, `ATIVA AJUIZADA`, `ATIVA A SER AJUIZADA` | todo |
| `receita_principal` | `RECEITA_PRINCIPAL` | texto | Receita (tributo ou multa) da dívida; a grafia varia (`R D Ativa - Simples Nacional - MEI`, `R D ATIVA - SIMP NAC - MEI`) | — | todo |
| `data_inscricao` | `DATA_INSCRICAO` | texto | Data da inscrição em dívida ativa, como a fonte publica | dd/mm/aaaa | todo |
| `indicador_ajuizado` | `INDICADOR_AJUIZADO` | texto | Se a cobrança foi ajuizada | `SIM`, `NAO` | todo |
| `valor_consolidado` | `VALOR_CONSOLIDADO` | decimal | Valor consolidado da inscrição na data da fotografia, em reais; repete-se entre os devedores da mesma inscrição | R$ | todo |
| `regiao_pgfn` | — (nome do CSV) | texto | Código tirado do nome do CSV dentro do ZIP; veja os cuidados de uso | ver cuidados de uso | todo |
| `cnpj_basico` | — (gerada) | texto | Raiz de oito dígitos do CNPJ; nula para pessoa física | 8 dígitos | todo |
| `ano` | — (partição) | inteiro | Ano do trimestre | — | todo |
| `trimestre` | — (partição) | inteiro | Trimestre | 1 a 4 | todo |

## No lake

- Dataset `pgfn/sida`, particionado por `ano` e `trimestre`; um Parquet por CSV do ZIP.
- Todas as colunas são lidas como texto, para preservar zeros à esquerda; só `valor_consolidado` vira decimal (a vírgula decimal, se houver, vira ponto).
- O texto é decodificado de Windows-1252 para UTF-8; os poucos bytes que o Windows-1252 deixa indefinidos viram o caractere de controle de mesmo código, sem perda.
- Nomes de coluna são normalizados (minúsculas, sem acento); por isso a coluna de UF tem dois nomes, conforme a era.
- `cnpj_basico` é acrescentada: os oito primeiros dígitos do CNPJ, quando o documento tem 14 dígitos; CPF mascarado fica sem ela.
- `regiao_pgfn` é acrescentada a partir do nome do CSV.
- CSVs só com cabeçalho são ignorados.

## Cuidados de uso

- **Não some `valor_consolidado` das linhas.** O valor da inscrição repete-se para cada corresponsável e devedor solidário. Em 2022-T3 a soma de todas as linhas dá R$ 4,61 tri, e a soma só dos devedores `PRINCIPAL` dá R$ 2,17 tri; em 2026-T3 são R$ 7,09 tri contra R$ 3,03 tri (conferido em 2026-11-09). Filtre `tipo_devedor = 'PRINCIPAL'` para valores por inscrição.
- **Fotografias, não fluxo.** Cada trimestre é o estoque inteiro. Somar trimestres conta o mesmo débito várias vezes; compare estoques entre trimestres.
- **A chave quase se confirma.** Em 2022-T3, 19.492.158 linhas têm 19.492.152 pares (`cpf_cnpj`, `numero_inscricao`) distintos; em 2026-T3, 49.617.572 linhas têm 49.617.528 pares. Como o CPF é mascarado, pessoas diferentes podem compartilhar o mesmo CPF mascarado.
- **`regiao_pgfn` não é confiável como região.** Até 2022-T3 os CSVs são por UF e o conversor só reconhece números e `NA` no nome; todos os arquivos por UF recebem o valor `1` (conferido em 2022-T3: único valor `1`). Desde 2022-T4 o valor é o número do CSV (`1` a `6`). A fonte não explica o significado das regiões.
- **Duas colunas de UF.** `uf_unidade_responsavel` (até 2022-T3) e `uf_devedor` (desde 2022-T4) não significam a mesma coisa: a primeira é da unidade da PGFN, a segunda do devedor. Para uma série longa, não as una sem decidir isso.
- **Datas e nomes como texto.** `data_inscricao` é dd/mm/aaaa em texto. A grafia de `receita_principal` e `situacao_inscricao` varia entre trimestres.
- **Pessoa física:** o nome do devedor vem completo mesmo com o CPF mascarado; trate-o como dado pessoal.
- **Valor zero:** 9 linhas de 2022-T3 têm `valor_consolidado` igual a zero.

## Exemplos

Estoque de dívida ativa (só devedores principais) por UF do devedor, em R$ bilhões, no último trimestre disponível:

```python
import duckdb

duckdb.sql("""
    SELECT coalesce(uf_devedor, uf_unidade_responsavel) AS uf,
           count(*) AS inscricoes,
           round(sum(valor_consolidado) / 1e9, 1) AS valor_bi
    FROM read_parquet('lake/pgfn/sida/**/*.parquet', hive_partitioning = true, union_by_name = true)
    WHERE ano = 2026 AND trimestre = 3 AND tipo_devedor = 'PRINCIPAL'
    GROUP BY uf
    ORDER BY valor_bi DESC
""").show()
```

## Referências

- Diretório de dados abertos da PGFN: https://dadosabertos.pgfn.gov.br
