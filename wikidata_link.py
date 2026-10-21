import time
from pathlib import Path
from urllib.error import HTTPError, URLError

import rdflib.plugins.sparql.evaluate as sparql_evaluate
from rdflib import Graph, URIRef
from rdflib.namespace import OWL, SKOS

from build_graph import COUNTRY, FILM, GENRE, PERSON, bind_prefixes
from queries import PREFIXES, print_table, run, md_table

ROOT = Path(__file__).parent
OUT = ROOT / "output"

WD = "http://www.wikidata.org/entity/"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

USER_AGENT = "SemanticWebLab1/1.0 (university lab work; rdflib)"
TRANSIENT_HTTP_CODES = {429, 500, 502, 503, 504}
_original_urlopen = sparql_evaluate.urlopen


def _urlopen_with_retry(request, *args, retries: int = 5, **kwargs):
    request.add_header("User-Agent", USER_AGENT)
    kwargs.setdefault("timeout", 60)
    for attempt in range(retries):
        try:
            return _original_urlopen(request, *args, **kwargs)
        except HTTPError as e:
            if e.code not in TRANSIENT_HTTP_CODES or attempt == retries - 1:
                raise
            reason = f"HTTP {e.code}"
        except (URLError, TimeoutError) as e:
            if attempt == retries - 1:
                raise
            reason = type(e).__name__
        delay = 2 ** attempt
        print(f"  [Wikidata: {reason}, повтор {attempt + 1}/{retries - 1} через {delay} с]")
        time.sleep(delay)


sparql_evaluate.urlopen = _urlopen_with_retry
NETWORK_ERRORS = (HTTPError, URLError, TimeoutError)

FILM_QIDS = {
    "Inception": "Q25188", "Interstellar": "Q13417189", "TheDarkKnight": "Q163872",
    "Oppenheimer": "Q108839994", "Tenet": "Q63985561", "Dune": "Q60834962",
    "DunePartTwo": "Q109228991", "Arrival": "Q20382729", "BladeRunner2049": "Q21500755",
    "Parasite": "Q61448040", "TheWolfOfWallStreet": "Q1392744",
    "KillersOfTheFlowerMoon": "Q66316924", "Amelie": "Q484048", "Barbie": "Q55436290",
    "LittleWomen": "Q56881140", "LaLaLand": "Q20856802",
}
DIRECTOR_QIDS = {
    "ChristopherNolan": "Q25191", "DenisVilleneuve": "Q548823", "BongJoonHo": "Q495980",
    "MartinScorsese": "Q41148", "JeanPierreJeunet": "Q217324", "GretaGerwig": "Q271967",
    "DamienChazelle": "Q18350026",
}
COUNTRY_QIDS = {
    "USA": "Q30", "UK": "Q145", "Canada": "Q16", "SouthKorea": "Q884", "France": "Q142",
    "Ireland": "Q27", "Australia": "Q408", "Sweden": "Q34", "Italy": "Q38",
}
GENRE_QIDS = {
    "SciFi": "Q471839", "Action": "Q188473", "Drama": "Q130232", "Crime": "Q959790",
    "Thriller": "Q2484376", "Comedy": "Q157443", "Romance": "Q1054574",
    "Musical": "Q842256", "Biographical": "Q645928", "Adventure": "Q319221",
}

WD_PREFIXES = """PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX wd:   <http://www.wikidata.org/entity/>
PREFIX wdt:  <http://www.wikidata.org/prop/direct/>
PREFIX p:    <http://www.wikidata.org/prop/>
PREFIX psn:  <http://www.wikidata.org/prop/statement/value-normalized/>
PREFIX wikibase: <http://wikiba.se/ontology#>
"""

FEDERATED_QUERIES = [
    (
        "F1. Місто та дата народження режисерів (Wikidata) і кількість їхніх фільмів у власному графі",
        f"""
SELECT ?director (COUNT(DISTINCT ?film) AS ?films) ?birthDate
       (GROUP_CONCAT(DISTINCT ?placeName; separator=" / ") AS ?birthPlace) WHERE {{
  ?film mo:directedBy ?d .                # власний граф
  ?d foaf:name ?director ;
     owl:sameAs ?wd .                     # зв'язок із Wikidata
  SERVICE <{WIKIDATA_SPARQL}> {{
    ?wd wdt:P569 ?birthDate ;             # дата народження
        wdt:P19 ?place .                  # місце народження
    ?place rdfs:label ?placeName .
    FILTER (LANG(?placeName) = "en")
  }}
}}
GROUP BY ?director ?birthDate
ORDER BY DESC(?films) ?director
""",
    ),
    (
        "F2. Фільми з рейтингом ≥ 8.0 (власний граф): кількість нагород і бюджет (Wikidata)",
        f"""
SELECT ?title ?rating (COUNT(DISTINCT ?award) AS ?awards) (MAX(?budget) AS ?budgetUSD) WHERE {{
  ?film dcterms:title ?title ;            # власний граф
        mo:imdbRating ?rating ;
        owl:sameAs ?wd .
  FILTER (?rating >= 8.0)
  SERVICE <{WIKIDATA_SPARQL}> {{
    OPTIONAL {{ ?wd wdt:P166 ?award . }}  # нагороди
    OPTIONAL {{ ?wd wdt:P2130 ?budget . }} # бюджет
  }}
}}
GROUP BY ?title ?rating
ORDER BY DESC(?awards)
""",
    ),
    (
        "F3. Звірка даних: тривалість фільму у власному графі та у Wikidata (P2047, нормалізовано)",
        f"""
SELECT DISTINCT ?title ?ourRuntime ?wdRuntime (?ourRuntime - ?wdRuntime AS ?diff) WHERE {{
  ?film dcterms:title ?title ;
        mo:runtimeMinutes ?ourRuntime ;
        owl:sameAs ?wd .
  SERVICE <{WIKIDATA_SPARQL}> {{
    # нормалізоване значення (завжди в секундах), а не wdt:P2047 «як введено»
    ?wd p:P2047/psn:P2047/wikibase:quantityAmount ?seconds .
  }}
  BIND (ROUND(?seconds / 60) AS ?wdRuntime)
}}
ORDER BY ?title
""",
    ),
]


def add_links(g: Graph) -> int:
    before = len(g)
    for ns, mapping in [(FILM, FILM_QIDS), (PERSON, DIRECTOR_QIDS), (COUNTRY, COUNTRY_QIDS)]:
        for key, qid in mapping.items():
            g.add((ns[key], OWL.sameAs, URIRef(WD + qid)))
    for key, qid in GENRE_QIDS.items():
        g.add((GENRE[key], SKOS.exactMatch, URIRef(WD + qid)))
    return len(g) - before


def verify_links(g: Graph) -> None:
    """Порівнює назви у власному графі з мітками у Wikidata (через SERVICE)."""
    q = f"""
SELECT ?local ?ourName ?wdName WHERE {{
  ?local owl:sameAs|skos:exactMatch ?wd .
  ?local dcterms:title|foaf:name|rdfs:label ?ourName .
  SERVICE <{WIKIDATA_SPARQL}> {{
    ?wd rdfs:label ?wdName .
    FILTER (LANG(?wdName) IN ("en", "mul"))
  }}
}}
ORDER BY ?local
"""
    cols, rows = run(g, WD_PREFIXES + q)
    by_local: dict[str, tuple[str, set]] = {}
    for local, ours, wd in rows:
        by_local.setdefault(local, (ours, set()))[1].add(wd)
    bad = [(k, o, w) for k, (o, w) in by_local.items()
           if o.lower() not in {x.lower() for x in w} and not any(o.lower() in x.lower() for x in w)]
    print(f"Перевірено зв'язків: {len(by_local)}; розбіжностей у назвах: {len(bad)}")
    for k, o, w in bad:
        print(f"  ! {k}: '{o}' vs {sorted(w)}")


def main() -> None:
    g = Graph().parse(ROOT / "movies_edited.ttl", format="turtle")
    bind_prefixes(g)
    g.bind("wd", WD)
    g.bind("skos", SKOS)

    n = add_links(g)
    print(f"Додано зв'язків із Wikidata: {n}")
    for s, p, o in [(FILM.Inception, OWL.sameAs, None), (PERSON.ChristopherNolan, OWL.sameAs, None),
                    (GENRE.SciFi, SKOS.exactMatch, None)]:
        print(f"  {s.n3(g.namespace_manager)} {p.n3(g.namespace_manager)} <{g.value(s, p)}> .")

    OUT.mkdir(exist_ok=True)
    g.serialize(OUT / "movies_linked.ttl", format="turtle")
    print(f"Збережено {OUT / 'movies_linked.ttl'} ({len(g)} трійок)")

    print("\nПеревірка відповідності назв у власному графі та Wikidata:")
    try:
        verify_links(g)
    except NETWORK_ERRORS as e:
        print(f"Wikidata недоступна ({e}); перевірку пропущено.")

    md = ["# Результати федеративних запитів (власний граф + Wikidata)\n"]
    failed = 0
    for title, q in FEDERATED_QUERIES:
        print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)
        print(q.strip() + "\n")
        try:
            cols, rows = run(g, WD_PREFIXES + q)
        except NETWORK_ERRORS as e:
            failed += 1
            print(f"Wikidata недоступна ({e}); запит пропущено.")
            continue
        print_table(cols, rows)
        md.append(f"## {title}\n\n```sparql\n{q.strip()}\n```\n\n"
                  f"**Результат ({len(rows)} рядків):**\n\n{md_table(cols, rows)}\n")

    if failed:
        print(f"\n{failed} запит(и) не виконано через недоступність Wikidata; "
              f"попередні результати лишаються в {OUT / 'federated_results.md'}")
    else:
        (OUT / "federated_results.md").write_text("\n".join(md), encoding="utf-8")
        print(f"\nЗбережено {OUT / 'federated_results.md'}")


if __name__ == "__main__":
    main()
