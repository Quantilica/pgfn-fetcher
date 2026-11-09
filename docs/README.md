# Dívida Ativa da União — PGFN (`pgfn`)

O `pgfn-fetcher` coleta os dados abertos da Dívida Ativa da União publicados pela Procuradoria-Geral da Fazenda Nacional (PGFN) e os converte para o lake em Parquet particionado por ano e trimestre. A PGFN publica três conjuntos: a dívida ativa não previdenciária (sistema SIDA), a previdenciária e a do FGTS.

| Dataset | O que é | Origem | Período | Página |
|---|---|---|---|---|
| `sida` | Inscrições em dívida ativa não previdenciária, uma linha por inscrição e devedor | ZIP trimestral `Dados_abertos_Nao_Previdenciario` (a partir de 2026, `Dados_abertos_Sistema_SIDA`) | 2020-T1 em diante | [sida](datasets/sida.md) |
| `previdenciario` | Inscrições em dívida ativa previdenciária | ZIP trimestral `Dados_abertos_Previdenciario` | 2020-T1 em diante | [previdenciario](datasets/previdenciario.md) |
| `fgts` | Inscrições em dívida ativa de contribuições ao FGTS e à contribuição social da LC 110 | ZIP trimestral `Dados_abertos_FGTS` | 2020-T1 em diante | [fgts](datasets/fgts.md) |

## Como a PGFN publica

- Os arquivos ficam em um diretório público, em uma pasta por trimestre (`<ano>_trimestre_<NN>`), com um ZIP por conjunto. A PGFN publica só trimestres fechados: o trimestre corrente não tem arquivo.
- Cada ZIP é uma fotografia completa do estoque no fim do trimestre, não um incremento: o mesmo débito aparece em vários trimestres, até ser extinto.
- Cada ZIP traz vários CSVs (separador ponto e vírgula, codificação Windows-1252). Até 2022-T3 os arquivos são divididos por UF; desde 2022-T4, por região da PGFN (números de 1 a 6) com arquivos adicionais para casos sem região (`NA`, `-1`, `-9`).
- A fonte não publica dicionário de variáveis nem licença nos diretórios consultados (conferido em 2026-11-09); as descrições das colunas nestas páginas vêm dos nomes e dos valores observados.
- O nome do ZIP varia (`Nao_Previdenciario`, `Sistema_SIDA`); o fetcher reconhece o conjunto pelo nome.
- Conferido em 2026-11-09 pela listagem do bruto: os três conjuntos têm 27 trimestres, de 2020-T1 a 2026-T3.

O fetcher guarda cada versão baixada com a data de coleta no nome (`<arquivo>@AAAAMMDD`). O lake converte a versão mais recente de cada trimestre.

## Dados pessoais

Os três conjuntos listam devedores pelo CPF ou CNPJ e pelo nome. A PGFN mascara o CPF das pessoas físicas (`XXX999.999XX`, só os seis dígitos do meio); o CNPJ das pessoas jurídicas vem completo, e o nome do devedor vem sem máscara nos dois casos. O fetcher e o lake preservam os campos como a fonte publica. Veja a nota em cada página de dataset.

## Como os conjuntos se relacionam

- Os três conjuntos têm quase as mesmas colunas e a mesma estrutura de inscrição; mudam a receita (`receita_principal` ou `tipo_credito`) e, no FGTS, as colunas da entidade responsável e da unidade de inscrição.
- Um mesmo devedor pode ter inscrições nos três conjuntos; cada inscrição pertence a um só deles.

## Quebras que valem para mais de um conjunto

| Desde | Mudança | Afeta |
|---|---|---|
| 2022-10 (2022-T4) | A coluna `UF_UNIDADE_RESPONSAVEL` passa a se chamar `UF_DEVEDOR`, e o particionamento dos arquivos por UF dá lugar ao particionamento por região da PGFN | `sida`, `previdenciario`, `fgts` |
