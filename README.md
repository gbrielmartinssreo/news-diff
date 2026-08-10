# News Diff 📰

Sistema para **coleta, análise e agrupamento de notícias semelhantes** publicadas por diferentes portais.

O News Diff coleta notícias através de feeds RSS, identifica matérias que tratam do mesmo assunto e gera um ranking dos temas mais republicados. A comparação entre os títulos é realizada utilizando o algoritmo **LCS (Longest Common Subsequence)**, implementado com Programação Dinâmica.

Projeto desenvolvido para a disciplina de **Projeto e Análise de Algoritmos** da Faculdade de Engenharia da Universidade Federal de Mato Grosso (UFMT).

**Autores:** Pedro Reis e Gabriel Martins

---

## 🎯 Objetivo

Portais de notícias frequentemente publicam matérias sobre o mesmo acontecimento com pequenas alterações nos títulos.

Por exemplo:

* `Neil Sedaka morre aos 86 anos`
* `Morre Neil Sedaka, cantor, aos 86 anos`
* `Neil Sedaka, ícone do pop, morre`

O objetivo do News Diff é identificar que essas notícias estão relacionadas e agrupá-las em um único tópico.

O sistema também permite identificar quais assuntos tiveram maior repercussão entre os diferentes portais.

---

## ⚙️ Funcionamento

O processamento segue um pipeline de cinco etapas:

```text
RSS dos portais
      │
      ▼
   Coleta
      │
      ▼
   Filtros
      │
      ▼
 Pré-filtro por palavras-chave
      │
      ▼
      LCS
      │
      ▼
 Agrupamento
      │
      ▼
   Ranking
```

### 1. Coleta

As notícias são obtidas através de feeds **RSS**, evitando a necessidade de scraping direto das páginas.

O sistema suporta portais pré-configurados e também permite adicionar portais através do arquivo `portais_extra.txt`.

### 2. Filtragem

Antes da comparação são realizadas algumas otimizações:

* remoção de URLs duplicadas;
* remoção de títulos que seguem templates editoriais;
* normalização dos títulos;
* tokenização das palavras;
* cache das palavras-chave.

### 3. Pré-filtro

Antes de executar o LCS, o sistema verifica a interseção entre as palavras dos títulos.

Somente notícias que possuem pelo menos **duas palavras em comum** seguem para a comparação LCS.

Isso evita milhares de comparações desnecessárias.

### 4. Comparação com LCS

O algoritmo **Longest Common Subsequence** encontra a maior subsequência comum entre dois títulos.

A similaridade é calculada por:

```text
similaridade = LCS / max(|A|, |B|)
```

O limiar utilizado pelo agrupamento é **0.35**.

### 5. Agrupamento e ranking

Notícias consideradas semelhantes são agrupadas em um mesmo tópico.

Depois disso, os tópicos são ordenados de acordo com a quantidade de portais que republicaram o assunto.

---

## 🧠 Algoritmo LCS

O LCS foi implementado utilizando **Programação Dinâmica**.

A implementação possui:

* tabela DP;
* reconstrução da subsequência através de backtracking;
* normalização dos textos;
* cache de pré-processamento;
* cálculo de similaridade normalizada.

### Complexidade

Para títulos com `m` e `n` palavras:

```text
Tempo:  O(m × n)
Espaço: O(m × n)
```

Uma abordagem por força bruta teria complexidade exponencial, tornando-se impraticável para grandes quantidades de notícias.

O LCS também preserva a **ordem das palavras**, permitindo capturar similaridade estrutural entre títulos.

---

## 🚀 Otimizações

### Pré-filtro por palavras-chave

O LCS é executado somente quando existem pelo menos duas palavras em comum entre os títulos.

Em uma execução típica:

```text
Comparações totais:       ~83.000
Bloqueadas pelo filtro:   ~82.700
LCS executado:            ~300
```

Isso significa que aproximadamente **99,6% das comparações foram eliminadas antes do LCS**.

### Deduplicação por URL

Notícias que possuem a mesma URL são removidas antes do agrupamento.

### Filtro editorial

Títulos considerados templates editoriais, como chamadas de vídeos e telejornais, são descartados para reduzir ruído.

### Cache

O processamento de palavras-chave é armazenado em cache para evitar que os mesmos títulos sejam processados repetidamente.

Também é utilizado `LRU Cache` no pré-processamento do LCS.

---

## 📁 Estrutura do projeto

```text
news-diff/
├── main.py
├── coletor.py
├── analisador.py
├── lcs.py
├── portais_extra.txt
└── README.md
```

### `main.py`

Interface CLI do sistema.

Disponibiliza:

1. coleta de notícias;
2. utilização de snapshot offline;
3. coleta e salvamento de snapshot.

### `coletor.py`

Responsável por:

* acessar os feeds RSS;
* fazer parsing dos feeds;
* processar datas;
* limpar HTML;
* criar e carregar snapshots JSON;
* controlar o intervalo entre requisições.

### `analisador.py`

Responsável pelo processamento das notícias:

* deduplicação;
* filtros editoriais;
* pré-filtro por palavras-chave;
* agrupamento através do LCS;
* geração das estatísticas;
* ranking dos assuntos.

### `lcs.py`

Implementa o algoritmo LCS utilizando Programação Dinâmica.

### `portais_extra.txt`

Permite adicionar portais personalizados através do formato:

```text
Nome do Portal | URL do RSS
```

---

## 📦 Requisitos

* Python `>= 3.13`
* `feedparser >= 6.0.12`
* `newspaper3k >= 0.2.8`

---

## 🔧 Instalação

### Com `uv`

O projeto recomenda o uso do [`uv`](https://docs.astral.sh/uv/).

Depois de instalar o `uv`, execute:

```bash
uv sync
```

---

### Sem `uv`

Instale as dependências manualmente:

```bash
pip install feedparser newspaper3k
```

---

## ▶️ Execução

Com `uv`:

```bash
uv run main.py
```

Ou utilizando Python diretamente:

```bash
python main.py
```

Ao iniciar, o programa apresenta:

```text
══════════════════════════
        NEWS DIFF
══════════════════════════

1. Coletar notícias agora
2. Usar snapshot (offline)
3. Coletar e salvar snapshot
0. Sair

Escolha uma opção:
```

---

## ⚙️ Parâmetros

Durante a execução, o sistema permite configurar:

* **janela de tempo** das notícias;
* **quantidade de resultados** no ranking;
* **arquivo de snapshot** utilizado.

Os valores padrão são:

```text
Janela de tempo: 5 horas
Ranking:         10 notícias
```

Basta pressionar `Enter` para utilizar os valores padrão.

---

## 🌐 Portais

O sistema trabalha com diversos portais através de RSS, incluindo categorias como:

* G1
* Folha
* IG
* InfoMoney
* Exame
* MoneyTimes
* Investing Brasil
* Canaltech
* Olhar Digital
* Tecnoblog
* BBC
* CNN Brasil
* The Guardian
* Al Jazeera
* The New York Times
* The Washington Post
* TechCrunch
* Wired
* Ars Technica
* MIT Technology Review
* Financial Times
* CNBC
* MarketWatch
* Rolling Stone
* Variety
* The Hollywood Reporter

Novos portais podem ser adicionados através do `portais_extra.txt`.

---

## 📊 Exemplo

Uma execução pode produzir um resultado semelhante a:

```text
1. Neil Sedaka, ícone do rock e do pop americano, morre aos 86 anos

   Republicada 4x
   Exame, Folha, CNN Brasil, G1

2. Milei tem vitória no Senado e consegue aprovar reforma trabalhista

   Republicada 3x
   Folha, CNN Brasil, G1
```

O sistema também apresenta estatísticas de processamento, como:

```text
Templates descartados: 17
Pré-filtro bloqueou:   82.379
LCS executado:         297
Total de comparações:  82.676
```

---

## 📈 Resultados

Nos testes realizados durante o desenvolvimento:

* o pré-filtro eliminou aproximadamente **99,6%** das comparações desnecessárias;
* notícias repetidas foram identificadas e agrupadas;
* notícias sobre o mesmo evento puderam ser agrupadas mesmo com diferenças nos títulos;
* o ranking permitiu identificar assuntos com maior repercussão entre os portais.

---

## ⚠️ Limitações

O sistema possui algumas limitações conhecidas.

### Limiar fixo

O valor `0.35` foi calibrado empiricamente.

Títulos muito curtos ou muito longos podem gerar falsos positivos ou negativos.

### Feeds

Alguns portais podem apresentar feeds quebrados ou deixar de fornecer notícias através do RSS.

### Idiomas

Notícias em português e inglês são processadas no mesmo ranking. Atualmente não existe separação por idioma.

---

## 🎓 Contexto acadêmico

Projeto desenvolvido para a disciplina de **Projeto e Análise de Algoritmos** da:

**Universidade Federal de Mato Grosso (UFMT)**
**Faculdade de Engenharia**
**Engenharia da Computação**

Professor: **Prof. Dr. Gustavo Post Sabin**.
