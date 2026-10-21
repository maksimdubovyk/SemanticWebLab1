# Результати федеративних запитів (власний граф + Wikidata)

## F1. Місто та дата народження режисерів (Wikidata) і кількість їхніх фільмів у власному графі

```sparql
SELECT ?director (COUNT(DISTINCT ?film) AS ?films) ?birthDate
       (GROUP_CONCAT(DISTINCT ?placeName; separator=" / ") AS ?birthPlace) WHERE {
  ?film mo:directedBy ?d .                # власний граф
  ?d foaf:name ?director ;
     owl:sameAs ?wd .                     # зв'язок із Wikidata
  SERVICE <https://query.wikidata.org/sparql> {
    ?wd wdt:P569 ?birthDate ;             # дата народження
        wdt:P19 ?place .                  # місце народження
    ?place rdfs:label ?placeName .
    FILTER (LANG(?placeName) = "en")
  }
}
GROUP BY ?director ?birthDate
ORDER BY DESC(?films) ?director
```

**Результат (7 рядків):**

| director | films | birthDate | birthPlace |
|---|---|---|---|
| Christopher Nolan | 5 | 1970-07-30T00:00:00+00:00 | London / City of Westminster |
| Denis Villeneuve | 4 | 1967-10-03T00:00:00+00:00 | Bécancour |
| Greta Gerwig | 2 | 1983-08-04T00:00:00+00:00 | Sacramento |
| Martin Scorsese | 2 | 1942-11-17T00:00:00+00:00 | Queens |
| Bong Joon-ho | 1 | 1969-09-14T00:00:00+00:00 | Daegu |
| Damien Chazelle | 1 | 1985-01-19T00:00:00+00:00 | Providence |
| Jean-Pierre Jeunet | 1 | 1953-09-03T00:00:00+00:00 | Le Coteau |

## F2. Фільми з рейтингом ≥ 8.0 (власний граф): кількість нагород і бюджет (Wikidata)

```sparql
SELECT ?title ?rating (COUNT(DISTINCT ?award) AS ?awards) (MAX(?budget) AS ?budgetUSD) WHERE {
  ?film dcterms:title ?title ;            # власний граф
        mo:imdbRating ?rating ;
        owl:sameAs ?wd .
  FILTER (?rating >= 8.0)
  SERVICE <https://query.wikidata.org/sparql> {
    OPTIONAL { ?wd wdt:P166 ?award . }  # нагороди
    OPTIONAL { ?wd wdt:P2130 ?budget . } # бюджет
  }
}
GROUP BY ?title ?rating
ORDER BY DESC(?awards)
```

**Результат (11 рядків):**

| title | rating | awards | budgetUSD |
|---|---|---|---|
| Parasite | 8.5 | 14 | 13200000 |
| La La Land | 8.0 | 13 | 30000000 |
| Amélie | 8.3 | 10 | 10000000 |
| Inception | 8.8 | 7 | 160000000 |
| Oppenheimer | 8.3 | 6 | 100000000 |
| The Dark Knight | 9.1 | 4 | 185000000 |
| Blade Runner 2049 | 8.0 | 3 | 150000000 |
| Dune | 8.0 | 3 | 165000000 |
| Dune: Part Two | 8.5 | 2 | 190000000 |
| Interstellar | 8.7 | 2 | 165000000 |
| The Wolf of Wall Street | 8.2 | 1 | 100000000 |

## F3. Звірка даних: тривалість фільму у власному графі та у Wikidata (P2047, нормалізовано)

```sparql
SELECT DISTINCT ?title ?ourRuntime ?wdRuntime (?ourRuntime - ?wdRuntime AS ?diff) WHERE {
  ?film dcterms:title ?title ;
        mo:runtimeMinutes ?ourRuntime ;
        owl:sameAs ?wd .
  SERVICE <https://query.wikidata.org/sparql> {
    # нормалізоване значення (завжди в секундах), а не wdt:P2047 «як введено»
    ?wd p:P2047/psn:P2047/wikibase:quantityAmount ?seconds .
  }
  BIND (ROUND(?seconds / 60) AS ?wdRuntime)
}
ORDER BY ?title
```

**Результат (16 рядків):**

| title | ourRuntime | wdRuntime | diff |
|---|---|---|---|
| Amélie | 122 | 122 | 0 |
| Arrival | 116 | 116 | 0 |
| Barbie | 114 | 114 | 0 |
| Blade Runner 2049 | 163 | 164 | -1 |
| Dune | 155 | 155 | 0 |
| Dune: Part Two | 166 | 165 | 1 |
| Inception | 148 | 148 | 0 |
| Interstellar | 169 | 169 | 0 |
| Killers of the Flower Moon | 206 | 206 | 0 |
| La La Land | 128 | 128 | 0 |
| Little Women | 135 | 134 | 1 |
| Oppenheimer | 180 | 180 | 0 |
| Parasite | 132 | 132 | 0 |
| Tenet | 150 | 150 | 0 |
| The Dark Knight | 152 | 153 | -1 |
| The Wolf of Wall Street | 180 | 180 | 0 |
