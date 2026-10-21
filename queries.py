from pathlib import Path

from rdflib import Graph, Literal, URIRef

ROOT = Path(__file__).parent
OUT = ROOT / "output"

PREFIXES = """PREFIX mo:      <http://example.org/movies/ontology#>
PREFIX film:    <http://example.org/movies/film/>
PREFIX person:  <http://example.org/movies/person/>
PREFIX genre:   <http://example.org/movies/genre/>
PREFIX country: <http://example.org/movies/country/>
PREFIX foaf:    <http://xmlns.com/foaf/0.1/>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
"""

QUERIES = [
    (
        "Q1. Які фільми зняв Крістофер Нолан?",
        "зв'язок Film → Director, ORDER BY",
        """
SELECT ?title ?year WHERE {
  ?film a mo:Film ;
        dcterms:title ?title ;
        mo:releaseYear ?year ;
        mo:directedBy person:ChristopherNolan .
}
ORDER BY ?year
""",
    ),
    (
        "Q2. Які фільми вийшли після 2020 року і хто їх режисер?",
        "FILTER, ORDER BY, зв'язок Film → Director",
        """
SELECT ?title ?year ?director WHERE {
  ?film a mo:Film ;
        dcterms:title ?title ;
        mo:releaseYear ?year ;
        mo:directedBy ?d .
  ?d foaf:name ?director .
  FILTER (?year > 2020)
}
ORDER BY DESC(?year) ?title
""",
    ),
    (
        "Q3. Який режисер має найбільше фільмів у графі (і який у нього середній рейтинг)?",
        "агрегатні функції COUNT, AVG, GROUP BY, ORDER BY",
        """
SELECT ?director (COUNT(?film) AS ?films) (ROUND(AVG(?rating) * 100) / 100 AS ?avgRating) WHERE {
  ?film a mo:Film ;
        mo:directedBy ?d ;
        mo:imdbRating ?rating .
  ?d foaf:name ?director .
}
GROUP BY ?director
ORDER BY DESC(?films) DESC(?avgRating)
""",
    ),
    (
        "Q4. Які актори брали участь у фільмах жанру «Science Fiction»?",
        "зв'язки між різними типами сутностей Actor ← Film → Genre, GROUP_CONCAT",
        """
SELECT ?actor (GROUP_CONCAT(?title; separator=", ") AS ?films) WHERE {
  ?film mo:hasGenre ?genre ;
        mo:hasActor ?a ;
        dcterms:title ?title .
  ?genre rdfs:label "Science Fiction"@en .
  ?a foaf:name ?actor .
}
GROUP BY ?actor
ORDER BY ?actor
""",
    ),
    (
        "Q5. Які актори, народжені НЕ у США, грали у фільмах режисерів, народжених у Великій Британії?",
        "перехід через 3 зв'язки: Actor ←hasActor— Film —directedBy→ Director —bornIn→ Country; FILTER",
        """
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
""",
    ),
    (
        "Q6. Середній, мінімальний і максимальний рейтинг та середня тривалість фільмів за жанрами",
        "AVG, MIN, MAX, COUNT, HAVING",
        """
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
""",
    ),
    (
        "Q7. Які актори знімалися у кількох фільмах графу і в яких режисерів?",
        "COUNT + HAVING, зв'язки Actor ← Film → Director",
        """
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
""",
    ),
    (
        "Q8. Які фільми знято студіями, що базуються поза США, і в якій країні ці студії?",
        "зв'язки Film → Studio → Country, FILTER NOT EXISTS",
        """
SELECT ?title ?studioName ?countryName WHERE {
  ?film dcterms:title ?title ;
        mo:producedBy ?studio .
  ?studio rdfs:label ?studioName ;
          mo:basedIn ?c .
  ?c rdfs:label ?countryName .
  FILTER NOT EXISTS { ?studio mo:basedIn country:USA }
}
ORDER BY ?countryName ?title
""",
    ),
]


def fmt(term) -> str:
    if term is None:
        return ""
    if isinstance(term, Literal):
        return str(term)
    if isinstance(term, URIRef):
        return str(term).rsplit("/", 1)[-1]
    return str(term)


def run(g: Graph, query: str):
    res = g.query(PREFIXES + query)
    cols = [str(v) for v in res.vars]
    rows = [[fmt(r[v]) for v in res.vars] for r in res]
    return cols, rows


def print_table(cols, rows) -> None:
    widths = [max(len(c), *(len(r[i]) for r in rows)) if rows else len(c) for i, c in enumerate(cols)]
    line = " | ".join(c.ljust(w) for c, w in zip(cols, widths))
    print(line + "\n" + "-" * len(line))
    for r in rows:
        print(" | ".join(v.ljust(w) for v, w in zip(r, widths)))
    print(f"({len(rows)} рядків)")


def md_table(cols, rows) -> str:
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    out += ["| " + " | ".join(v.replace("|", "\\|") for v in r) + " |" for r in rows]
    return "\n".join(out)


def main(graph_file: Path = ROOT / "movies_edited.ttl") -> None:
    g = Graph().parse(graph_file, format="turtle")
    print(f"Граф: {graph_file.name}, трійок: {len(g)}")
    md = [f"# Результати SPARQL-запитів\n\nГраф: `{graph_file.name}` ({len(g)} трійок)\n"]

    for title, demo, q in QUERIES:
        print("\n" + "=" * 78 + f"\n{title}\nДемонструє: {demo}\n" + "=" * 78)
        print(q.strip() + "\n")
        cols, rows = run(g, q)
        print_table(cols, rows)
        md.append(f"## {title}\n\n*Демонструє:* {demo}\n\n```sparql\n{q.strip()}\n```\n\n"
                  f"**Результат ({len(rows)} рядків):**\n\n{md_table(cols, rows)}\n")

    OUT.mkdir(exist_ok=True)
    (OUT / "query_results.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nЗбережено {OUT / 'query_results.md'}")


if __name__ == "__main__":
    main()
