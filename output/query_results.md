# Результати SPARQL-запитів

Граф: `movies_edited.ttl` (557 трійок)

## Q1. Які фільми зняв Крістофер Нолан?

*Демонструє:* зв'язок Film → Director, ORDER BY

```sparql
SELECT ?title ?year WHERE {
  ?film a mo:Film ;
        dcterms:title ?title ;
        mo:releaseYear ?year ;
        mo:directedBy person:ChristopherNolan .
}
ORDER BY ?year
```

**Результат (5 рядків):**

| title | year |
|---|---|
| The Dark Knight | 2008 |
| Inception | 2010 |
| Interstellar | 2014 |
| Tenet | 2020 |
| Oppenheimer | 2023 |

## Q2. Які фільми вийшли після 2020 року і хто їх режисер?

*Демонструє:* FILTER, ORDER BY, зв'язок Film → Director

```sparql
SELECT ?title ?year ?director WHERE {
  ?film a mo:Film ;
        dcterms:title ?title ;
        mo:releaseYear ?year ;
        mo:directedBy ?d .
  ?d foaf:name ?director .
  FILTER (?year > 2020)
}
ORDER BY DESC(?year) ?title
```

**Результат (5 рядків):**

| title | year | director |
|---|---|---|
| Dune: Part Two | 2024 | Denis Villeneuve |
| Barbie | 2023 | Greta Gerwig |
| Killers of the Flower Moon | 2023 | Martin Scorsese |
| Oppenheimer | 2023 | Christopher Nolan |
| Dune | 2021 | Denis Villeneuve |

## Q3. Який режисер має найбільше фільмів у графі (і який у нього середній рейтинг)?

*Демонструє:* агрегатні функції COUNT, AVG, GROUP BY, ORDER BY

```sparql
SELECT ?director (COUNT(?film) AS ?films) (ROUND(AVG(?rating) * 100) / 100 AS ?avgRating) WHERE {
  ?film a mo:Film ;
        mo:directedBy ?d ;
        mo:imdbRating ?rating .
  ?d foaf:name ?director .
}
GROUP BY ?director
ORDER BY DESC(?films) DESC(?avgRating)
```

**Результат (7 рядків):**

| director | films | avgRating |
|---|---|---|
| Christopher Nolan | 5 | 8.44 |
| Denis Villeneuve | 4 | 8.1 |
| Martin Scorsese | 2 | 7.9 |
| Greta Gerwig | 2 | 7.3 |
| Bong Joon-ho | 1 | 8.5 |
| Jean-Pierre Jeunet | 1 | 8.3 |
| Damien Chazelle | 1 | 8 |

## Q4. Які актори брали участь у фільмах жанру «Science Fiction»?

*Демонструє:* зв'язки між різними типами сутностей Actor ← Film → Genre, GROUP_CONCAT

```sparql
SELECT ?actor (GROUP_CONCAT(?title; separator=", ") AS ?films) WHERE {
  ?film mo:hasGenre ?genre ;
        mo:hasActor ?a ;
        dcterms:title ?title .
  ?genre rdfs:label "Science Fiction"@en .
  ?a foaf:name ?actor .
}
GROUP BY ?actor
ORDER BY ?actor
```

**Результат (16 рядків):**

| actor | films |
|---|---|
| Amy Adams | Arrival |
| Anne Hathaway | Interstellar |
| Austin Butler | Dune: Part Two |
| Harrison Ford | Blade Runner 2049 |
| Jeremy Renner | Arrival |
| Jessica Chastain | Interstellar |
| John David Washington | Tenet |
| Joseph Gordon-Levitt | Inception |
| Leonardo DiCaprio | Inception |
| Matthew McConaughey | Interstellar |
| Rebecca Ferguson | Dune, Dune: Part Two |
| Robert Pattinson | Tenet |
| Ryan Gosling | Blade Runner 2049 |
| Timothée Chalamet | Dune, Dune: Part Two |
| Tom Hardy | Inception |
| Zendaya | Dune, Dune: Part Two |

## Q5. Які актори, народжені НЕ у США, грали у фільмах режисерів, народжених у Великій Британії?

*Демонструє:* перехід через 3 зв'язки: Actor ←hasActor— Film —directedBy→ Director —bornIn→ Country; FILTER

```sparql
SELECT DISTINCT ?actor ?actorCountry ?title ?director WHERE {
  ?film mo:hasActor ?a ;                 # зв'язок 1
        mo:directedBy ?d ;               # зв'язок 2
        dcterms:title ?title .
  ?d mo:bornIn country:UK ;              # зв'язок 3
     foaf:name ?director .
  ?a foaf:name ?actor ;
     mo:bornIn ?c .
  ?c rdfs:label ?actorCountry .
  FILTER (?c != country:USA)
}
ORDER BY ?actor ?title
```

**Результат (6 рядків):**

| actor | actorCountry | title | director |
|---|---|---|---|
| Christian Bale | United Kingdom | The Dark Knight | Christopher Nolan |
| Cillian Murphy | Ireland | Oppenheimer | Christopher Nolan |
| Emily Blunt | United Kingdom | Oppenheimer | Christopher Nolan |
| Heath Ledger | Australia | The Dark Knight | Christopher Nolan |
| Robert Pattinson | United Kingdom | Tenet | Christopher Nolan |
| Tom Hardy | United Kingdom | Inception | Christopher Nolan |

## Q6. Середній, мінімальний і максимальний рейтинг та середня тривалість фільмів за жанрами

*Демонструє:* AVG, MIN, MAX, COUNT, HAVING

```sparql
SELECT ?genreName (COUNT(?film) AS ?films)
       (ROUND(AVG(?rating) * 100) / 100 AS ?avgRating)
       (MIN(?rating) AS ?minRating) (MAX(?rating) AS ?maxRating)
       (ROUND(AVG(?runtime)) AS ?avgRuntime) WHERE {
  ?film mo:hasGenre ?g ;
        mo:imdbRating ?rating ;
        mo:runtimeMinutes ?runtime .
  ?g rdfs:label ?genreName .
}
GROUP BY ?genreName
HAVING (COUNT(?film) >= 3)
ORDER BY DESC(?avgRating)
```

**Результат (8 рядків):**

| genreName | films | avgRating | minRating | maxRating | avgRuntime |
|---|---|---|---|---|---|
| Thriller | 4 | 8.6 | 8.0 | 9.1 | 149 |
| Action | 3 | 8.4 | 7.3 | 9.1 | 150 |
| Adventure | 3 | 8.4 | 8.0 | 8.7 | 163 |
| Crime | 3 | 8.3 | 7.6 | 9.1 | 179 |
| Science Fiction | 7 | 8.17 | 7.3 | 8.8 | 152 |
| Drama | 7 | 8.11 | 7.6 | 8.7 | 152 |
| Romance | 3 | 8.03 | 7.8 | 8.3 | 128 |
| Comedy | 4 | 7.95 | 6.8 | 8.5 | 137 |

## Q7. Які актори знімалися у кількох фільмах графу і в яких режисерів?

*Демонструє:* COUNT + HAVING, зв'язки Actor ← Film → Director

```sparql
SELECT ?actor (COUNT(DISTINCT ?film) AS ?films)
       (GROUP_CONCAT(DISTINCT ?director; separator=", ") AS ?directors) WHERE {
  ?film mo:hasActor ?a ;
        mo:directedBy ?d .
  ?a foaf:name ?actor .
  ?d foaf:name ?director .
}
GROUP BY ?actor
HAVING (COUNT(DISTINCT ?film) > 1)
ORDER BY DESC(?films) ?actor
```

**Результат (6 рядків):**

| actor | films | directors |
|---|---|---|
| Leonardo DiCaprio | 3 | Christopher Nolan, Martin Scorsese |
| Ryan Gosling | 3 | Denis Villeneuve, Greta Gerwig, Damien Chazelle |
| Timothée Chalamet | 3 | Denis Villeneuve, Greta Gerwig |
| Margot Robbie | 2 | Greta Gerwig, Martin Scorsese |
| Rebecca Ferguson | 2 | Denis Villeneuve |
| Zendaya | 2 | Denis Villeneuve |

## Q8. Які фільми знято студіями, що базуються поза США, і в якій країні ці студії?

*Демонструє:* зв'язки Film → Studio → Country, FILTER NOT EXISTS

```sparql
SELECT ?title ?studioName ?countryName WHERE {
  ?film dcterms:title ?title ;
        mo:producedBy ?studio .
  ?studio rdfs:label ?studioName ;
          mo:basedIn ?c .
  ?c rdfs:label ?countryName .
  FILTER NOT EXISTS { ?studio mo:basedIn country:USA }
}
ORDER BY ?countryName ?title
```

**Результат (8 рядків):**

| title | studioName | countryName |
|---|---|---|
| Amélie | Claudie Ossard Productions | France |
| Parasite | Barunson E&A | South Korea |
| Barbie | Heyday Films | United Kingdom |
| Inception | Syncopy | United Kingdom |
| Interstellar | Syncopy | United Kingdom |
| Oppenheimer | Syncopy | United Kingdom |
| Tenet | Syncopy | United Kingdom |
| The Dark Knight | Syncopy | United Kingdom |
