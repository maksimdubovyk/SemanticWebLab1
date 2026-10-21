from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import OWL

import wikidata_link  # noqa: F401 — вмикає повтори та User-Agent для SERVICE-запитів
from build_graph import FILM
from queries import PREFIXES

ROOT = Path(__file__).parent

ROOT_PREFIXES = """@prefix mo: <http://example.org/movies/ontology#> .
@prefix film: <http://example.org/movies/film/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""


def header(text: str) -> None:
    print("\n" + "=" * 78 + f"\n{text}\n" + "=" * 78)


def e1_turtle_syntax() -> None:
    header("E1. Синтаксична помилка в Turtle")
    wrong = ROOT_PREFIXES + """
film:Tenet a mo:Film ;
    dcterms:title "Tenet"@en ;
    mo:releaseYear 2020
film:Dune a mo:Film .
"""
    print("Помилковий Turtle:\n" + wrong)
    try:
        Graph().parse(data=wrong, format="turtle")
    except Exception as e:
        print(f"-> ОЧІКУВАНА помилка розбору (так і має бути): {type(e).__name__}: {str(e).splitlines()[0][:200]}")

    fixed = ROOT_PREFIXES + """@prefix dcterms: <http://purl.org/dc/terms/> .

film:Tenet a mo:Film ;
    dcterms:title "Tenet"@en ;
    mo:releaseYear 2020 .
film:Dune a mo:Film .
"""
    print("\nВиправлений Turtle (додано @prefix dcterms і крапку після 2020):\n" + fixed)
    g = Graph().parse(data=fixed, format="turtle")
    print(f"-> розібрано успішно, трійок: {len(g)}")


def e2_untyped_year() -> None:
    header("E2. Рік як рядок замість xsd:integer")
    q = PREFIXES + "SELECT ?f ?year WHERE { ?f mo:releaseYear ?year . FILTER (?year > 2020) } ORDER BY ?f"
    wrong = ROOT_PREFIXES + """
film:Dune   mo:releaseYear "2021" .
film:Barbie mo:releaseYear "2023" .
film:Tenet  mo:releaseYear "2020" .
film:Amelie mo:releaseYear "2001" .
"""
    fixed = ROOT_PREFIXES + """
film:Dune   mo:releaseYear 2021 .
film:Barbie mo:releaseYear "2023"^^xsd:integer .
film:Tenet  mo:releaseYear 2020 .
film:Amelie mo:releaseYear 2001 .
"""
    for name, ttl in [("Помилково (рядки)", wrong), ("Виправлено (xsd:integer)", fixed)]:
        g = Graph().parse(data=ttl, format="turtle")
        rows = [str(r.f).rsplit("/", 1)[-1] for r in g.query(q)]
        print(f"{name:<26} FILTER (?year > 2020) -> {rows}")
    print("Причина: \"2023\" — рядок (xsd:string), тож числового порівняння немає. За специфікацією SPARQL\n"
          "це помилка типу, а RDFLib впорядковує значення різних типів і вважає будь-який рядок\n"
          "«більшим» за число — тому у вибірку потрапляють навіть Tenet (2020) та Amélie (2001).")


def e3_language_tag() -> None:
    header("E3. Літерал без мовного тегу не дорівнює літералу з тегом @en")
    g = Graph().parse(ROOT / "movies_edited.ttl", format="turtle")
    wrong = 'SELECT ?film WHERE { ?film mo:hasGenre ?g . ?g rdfs:label "Science Fiction" . }'
    fixed1 = 'SELECT ?film WHERE { ?film mo:hasGenre ?g . ?g rdfs:label "Science Fiction"@en . }'
    fixed2 = ('SELECT ?film WHERE { ?film mo:hasGenre ?g . ?g rdfs:label ?l . '
              'FILTER (STR(?l) = "Science Fiction") }')
    for name, q in [("Помилково", wrong), ("Виправлено (@en)", fixed1), ("Виправлено (STR())", fixed2)]:
        n = len(list(g.query(PREFIXES + q)))
        print(f"{name:<20} {q}\n{'':<20} -> {n} рядків")


def e4_wikidata_units() -> None:
    header("E4. Wikidata: одиниці вимірювання тривалості (P2047)")
    g = Graph()
    g.add((FILM.Oppenheimer, OWL.sameAs, URIRef("http://www.wikidata.org/entity/Q108839994")))
    g.add((FILM.Inception, OWL.sameAs, URIRef("http://www.wikidata.org/entity/Q25188")))
    prefixes = """PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX p:   <http://www.wikidata.org/prop/>
PREFIX psn: <http://www.wikidata.org/prop/statement/value-normalized/>
PREFIX wikibase: <http://wikiba.se/ontology#>
"""
    wrong = """SELECT DISTINCT ?film ?runtime WHERE { ?film owl:sameAs ?wd .
  SERVICE <https://query.wikidata.org/sparql> { ?wd wdt:P2047 ?runtime . } } ORDER BY ?film ?runtime"""
    fixed = """SELECT DISTINCT ?film ?runtime WHERE { ?film owl:sameAs ?wd .
  SERVICE <https://query.wikidata.org/sparql> { ?wd p:P2047/psn:P2047/wikibase:quantityAmount ?sec . }
  BIND (ROUND(?sec / 60) AS ?runtime) } ORDER BY ?film"""
    try:
        for name, q in [("Помилково (wdt:P2047)", wrong), ("Виправлено (psn:P2047 / 60)", fixed)]:
            rows = [(str(r.film).rsplit("/", 1)[-1], str(r.runtime)) for r in g.query(prefixes + q)]
            print(f"{name:<28} -> {rows}")
        print("Причина: wdt: повертає лише число «як введено»; для Oppenheimer одне з тверджень "
              "записане в секундах (10809 s), тож без урахування одиниць отримуємо хибне значення.")
    except Exception as e:  # немає мережі
        print(f"Wikidata недоступна: {type(e).__name__}: {e}")


if __name__ == "__main__":
    e1_turtle_syntax()
    e2_untyped_year()
    e3_language_tag()
    e4_wikidata_units()
