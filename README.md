# Marvel Calculation Universe (MCU)

Dashboard web analitico inspirado no universo Marvel, construido para apresentar uma experiencia visual premium, responsiva e resiliente em ambiente academico. O projeto refatora a ideia de um painel Power BI para uma aplicacao web completa, combinando backend Python, frontend HTML/CSS/JavaScript nativo, dados locais tratados e visualizacoes interativas.

## Visao Executiva

O Marvel Calculation Universe organiza dados de personagens Marvel em quatro jornadas de analise:

- Escolha Aleatoria: sorteio dinamico de personagens com avatar, identidade, alinhamento, equipe e descricao.
- Pesquisa de Herois: busca textual, filtros laterais, paginacao fixa Top 20 e filtro alfabetico A-Z.
- Estatisticas Avancadas: KPIs, ranking de poder, data bars e grafico comparativo com Chart.js.
- Analise de Grupos: agrupamento por equipe ou alinhamento com classificacao visual por estrelas.

O objetivo principal e reduzir friccao cognitiva, evitar sobrecarga visual e transformar uma base extensa de dados em uma experiencia clara para apresentacao em banca.

## Decisoes de UX Baseadas em Cole Nussbaumer Knaflic

As decisoes de interface seguem principios defendidos por Cole Nussbaumer Knaflic em storytelling com dados: reduzir carga cognitiva, direcionar atencao, remover ruido visual e usar elementos graficos para facilitar comparacoes.

### Reducao de carga cognitiva

O painel evita despejar todos os dados em uma tela unica. Em vez disso, o conteudo foi dividido em abas funcionais. Cada aba responde a uma pergunta especifica:

- Quem posso sortear agora?
- Como encontro um personagem?
- Quem tem os maiores atributos?
- Quais grupos performam melhor?

Essa separacao ajuda o usuario a entender o contexto antes de interagir com os dados.

### Abas dinamicas sem reload

As abas sao controladas por JavaScript nativo. O clique altera classes CSS e mostra apenas a secao ativa, sem recarregar a pagina. Isso preserva o contexto mental do usuario e evita interrupcoes visuais.

### Paginacao rigida Top 20

A tabela de pesquisa limita a exibicao a 20 personagens por pagina. Essa decisao evita tabelas longas, scroll excessivo e poluicao visual. A paginacao torna a leitura previsivel e mantem avatares, nomes e metricas sempre legiveis.

### Filtro A-Z

O filtro alfabetico no rodape da tabela permite reduzir rapidamente o conjunto de dados por inicial do nome. Ele funciona como um atalho cognitivo: em vez de obrigar o usuario a digitar, oferece uma navegacao direta e familiar.

### Data bars

Na aba Estatisticas, atributos numericos de 0 a 100 sao convertidos em barras horizontais. Essa representacao permite comparar grandezas visualmente sem exigir leitura numero a numero.

### Tooltips

Informacoes densas ficam ocultas em tooltips ativados por hover. Assim, a tabela permanece limpa, mas o usuario ainda consegue acessar detalhes quando necessario.

## Tecnologias Utilizadas

- Python 3: backend e servidor local.
- Flask: usado automaticamente quando instalado.
- Fallback nativo Python: usado quando Flask nao esta disponivel.
- HTML5: estrutura semantica da interface.
- CSS3: layout responsivo, variaveis, gradientes, glassmorphism e neon visual.
- JavaScript Vanilla: abas, filtros, paginacao, sorteio, agrupamentos e renderizacao dinamica.
- Chart.js via CDN: grafico comparativo da aba Estatisticas.
- JSON local: banco documental `marvel_dados.json` com personagens Marvel tratados.

## Arquitetura

O sistema usa uma arquitetura monolitica leve:

```text
Navegador
   |
   | GET /painel
   v
app.py
   |
   | le marvel_dados.json
   v
templates/painel.html
   |
   | injeta const herois = [...]
   v
JavaScript no navegador
```

O backend entrega a pagina renderizada e a base de dados inicial. Depois disso, a maior parte da interatividade acontece no frontend, sem chamadas repetidas ao servidor. A unica rota assincrona usada durante a experiencia e `/api/random`, que retorna um personagem aleatorio em JSON.

## Resiliencia Sem Flask

O arquivo `app.py` tenta importar Flask. Se Flask estiver instalado, o projeto roda como uma aplicacao Flask comum. Se Flask nao estiver instalado, o sistema ativa automaticamente um servidor HTTP nativo com `BaseHTTPRequestHandler` e `ThreadingHTTPServer`.

Isso foi feito para garantir que o projeto rode no laboratorio da faculdade mesmo sem instalacao previa de dependencias.

## Como Rodar Amanhã na Faculdade

### Opcao 1: Python puro, sem instalar nada

```bash
python app.py
```

Abra no navegador:

```text
http://127.0.0.1:5000/painel
```

Se a porta `5000` estiver ocupada, o servidor procura automaticamente uma proxima porta livre e informa no terminal.

### Opcao 2: escolhendo uma porta manualmente

```bash
python app.py 5001
```

Abra:

```text
http://127.0.0.1:5001/painel
```

### Opcao 3: com Flask instalado

Se o computador tiver Flask, o mesmo comando continua funcionando:

```bash
python app.py
```

O codigo detecta Flask automaticamente.

## Rotas do Sistema

- `/`: tela de abertura.
- `/painel`: dashboard principal.
- `/api/random`: retorna um personagem aleatorio em JSON.

Exemplo de resposta de `/api/random`:

```json
{
  "id": 717,
  "nome": "Wolverine",
  "real_name": "Logan",
  "alinhamento": "Herói",
  "equipe": "X-Men",
  "descricao": "...",
  "forca": 32,
  "inteligencia": 63,
  "velocidade": 50,
  "durabilidade": 100,
  "url_imagem": "https://..."
}
```

## Banco de Dados Local

O arquivo `marvel_dados.json` possui 270 personagens Marvel com:

- identificador;
- nome;
- nome real;
- alinhamento;
- equipe;
- descricao;
- forca;
- inteligencia;
- velocidade;
- durabilidade;
- URL de imagem valida.

Os atributos numericos sao padronizados entre 0 e 100, permitindo calculos diretos de medias, rankings e barras de progresso.

## Chart.js

O Chart.js e carregado via CDN no `<head>` do template `templates/painel.html`. O grafico e instanciado dinamicamente pelo JavaScript da aba Estatisticas e renderiza os personagens com maior indice medio de poder.

Caso a internet esteja indisponivel, o restante do painel continua funcionando. O impacto fica restrito ao grafico externo, pois as tabelas, filtros, sorteio e dados locais nao dependem da CDN.

## Estrutura do Projeto

```text
.
├── app.py
├── baixar_dados.py
├── marvel_dados.json
├── README.md
├── LICENSE
├── .gitignore
└── templates
    ├── index.html
    └── painel.html
```

## Validacoes Realizadas

- Compilacao Python com `python -m py_compile`.
- Leitura de `marvel_dados.json` com 270 registros validos.
- Verificacao de schema consistente.
- Atributos numericos validados entre 0 e 100.
- URLs de imagens com HTTP/HTTPS.
- Rotas `/painel` e `/api/random` testadas com status 200.
- Fallback sem Flask testado com servidor HTTP nativo.
- Importacao unica do Chart.js no `<head>`.
- Verificacao de HTML sem IDs duplicados e sem tags abertas.
- Renderizacao em Edge headless sem erros de JavaScript filtrados.

## Repositorio

Repositorio remoto:

```text
https://github.com/JoaoCesarDev22/Analise-Marvel-Personagens
```

## Licenca

Este projeto esta licenciado sob a MIT License. Consulte o arquivo `LICENSE`.
