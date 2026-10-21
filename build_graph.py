from pathlib import Path

from rdflib import Graph, Literal, Namespace
from rdflib.namespace import DCTERMS, FOAF, OWL, RDF, RDFS, XSD

import data

OUT = Path(__file__).parent / "output"

# --- Власні простори імен -------------------------------------------------
BASE = "http://example.org/movies/"
MO = Namespace(BASE + "ontology#")       # класи та властивості
FILM = Namespace(BASE + "film/")         # ресурси-фільми
PERSON = Namespace(BASE + "person/")     # режисери та актори
GENRE = Namespace(BASE + "genre/")
COUNTRY = Namespace(BASE + "country/")
STUDIO = Namespace(BASE + "studio/")
SCHEMA = Namespace("https://schema.org/")


def bind_prefixes(g: Graph) -> None:
    for prefix, ns in [
        ("mo", MO), ("film", FILM), ("person", PERSON), ("genre", GENRE),
        ("country", COUNTRY), ("studio", STUDIO), ("schema", SCHEMA),
        ("foaf", FOAF), ("dcterms", DCTERMS), ("owl", OWL),
    ]:
        g.bind(prefix, ns, override=True)


def add_ontology(g: Graph) -> None:
    classes = {
        MO.Film: ("Film", SCHEMA.Movie),
        MO.Person: ("Person", FOAF.Person),
        MO.Director: ("Director", MO.Person),
        MO.Actor: ("Actor", MO.Person),
        MO.Genre: ("Genre", SCHEMA.Thing),
        MO.Country: ("Country", SCHEMA.Country),
        MO.Studio: ("Studio", SCHEMA.Organization),
    }
    for cls, (label, parent) in classes.items():
        g.add((cls, RDF.type, OWL.Class))
        g.add((cls, RDFS.label, Literal(label, lang="en")))
        g.add((cls, RDFS.subClassOf, parent))

    object_props = {
        MO.directedBy: (MO.Film, MO.Director, SCHEMA.director),
        MO.hasActor: (MO.Film, MO.Actor, SCHEMA.actor),
        MO.hasGenre: (MO.Film, MO.Genre, SCHEMA.genre),
        MO.producedIn: (MO.Film, MO.Country, SCHEMA.countryOfOrigin),
        MO.producedBy: (MO.Film, MO.Studio, SCHEMA.productionCompany),
        MO.bornIn: (MO.Person, MO.Country, None),
        MO.basedIn: (MO.Studio, MO.Country, None),
    }
    for prop, (domain, range_, parent) in object_props.items():
        g.add((prop, RDF.type, OWL.ObjectProperty))
        g.add((prop, RDFS.domain, domain))
        g.add((prop, RDFS.range, range_))
        if parent is not None:
            g.add((prop, RDFS.subPropertyOf, parent))

    data_props = {
        MO.releaseYear: (MO.Film, XSD.integer),
        MO.runtimeMinutes: (MO.Film, XSD.integer),
        MO.imdbRating: (MO.Film, XSD.decimal),
        MO.birthYear: (MO.Person, XSD.integer),
    }
    for prop, (domain, range_) in data_props.items():
        g.add((prop, RDF.type, OWL.DatatypeProperty))
        g.add((prop, RDFS.domain, domain))
        g.add((prop, RDFS.range, range_))


def add_instances(g: Graph) -> None:
    for key, name in data.COUNTRIES.items():
        g.add((COUNTRY[key], RDF.type, MO.Country))
        g.add((COUNTRY[key], RDFS.label, Literal(name, lang="en")))

    for key, name in data.GENRES.items():
        g.add((GENRE[key], RDF.type, MO.Genre))
        g.add((GENRE[key], RDFS.label, Literal(name, lang="en")))

    for key, (name, country) in data.STUDIOS.items():
        g.add((STUDIO[key], RDF.type, MO.Studio))
        g.add((STUDIO[key], RDFS.label, Literal(name)))
        g.add((STUDIO[key], MO.basedIn, COUNTRY[country]))

    for people, cls in [(data.DIRECTORS, MO.Director), (data.ACTORS, MO.Actor)]:
        for key, (name, born, country) in people.items():
            p = PERSON[key]
            g.add((p, RDF.type, cls))
            g.add((p, RDF.type, FOAF.Person))
            g.add((p, FOAF.name, Literal(name)))
            g.add((p, MO.birthYear, Literal(born, datatype=XSD.integer)))
            g.add((p, MO.bornIn, COUNTRY[country]))

    for key, f in data.FILMS.items():
        film = FILM[key]
        g.add((film, RDF.type, MO.Film))
        g.add((film, DCTERMS.title, Literal(f["title"], lang="en")))
        g.add((film, MO.releaseYear, Literal(f["year"], datatype=XSD.integer)))
        g.add((film, MO.runtimeMinutes, Literal(f["runtime"], datatype=XSD.integer)))
        g.add((film, MO.imdbRating, Literal(str(f["rating"]), datatype=XSD.decimal)))
        g.add((film, MO.directedBy, PERSON[f["director"]]))
        for a in f["actors"]:
            g.add((film, MO.hasActor, PERSON[a]))
        for gen in f["genres"]:
            g.add((film, MO.hasGenre, GENRE[gen]))
        for c in f["countries"]:
            g.add((film, MO.producedIn, COUNTRY[c]))
        for s in f["studios"]:
            g.add((film, MO.producedBy, STUDIO[s]))


def build_graph() -> Graph:
    g = Graph()
    bind_prefixes(g)
    add_ontology(g)
    add_instances(g)
    return g


def print_stats(g: Graph) -> None:
    q = """
    SELECT ?type (COUNT(?s) AS ?n) WHERE {
      ?s a ?type .
      FILTER(STRSTARTS(STR(?type), STR(mo:)))
      FILTER(?type NOT IN (mo:Person))
    } GROUP BY ?type ORDER BY DESC(?n)
    """
    print("Екземпляри за типами:")
    total = 0
    for row in g.query(q, initNs={"mo": MO}):
        print(f"  {g.qname(row.type):<14} {row.n}")
        total += int(row.n)
    instances = set(g.subjects(RDF.type, None)) - set(g.subjects(RDF.type, OWL.Class)) \
        - set(g.subjects(RDF.type, OWL.ObjectProperty)) - set(g.subjects(RDF.type, OWL.DatatypeProperty))
    rels = {p for p, in g.query("SELECT DISTINCT ?p WHERE { ?s ?p ?o . ?s a ?t1 . ?o a ?t2 . "
                                "FILTER(?p != rdf:type && STRSTARTS(STR(?p), STR(mo:))) }",
                                initNs={"mo": MO, "rdf": RDF})}
    print(f"Унікальних екземплярів: {len(instances)}")
    print(f"Типів зв'язків між сутностями: {len(rels)} -> {', '.join(sorted(g.qname(r) for r in rels))}")
    print(f"Всього трійок: {len(g)}")


def main() -> Graph:
    OUT.mkdir(exist_ok=True)
    g = build_graph()
    print_stats(g)

    g.serialize(OUT / "movies.ttl", format="turtle")
    g.serialize(OUT / "movies.jsonld", format="json-ld", indent=2)
    g.serialize(OUT / "movies.nt", format="nt", encoding="utf-8")
    g.serialize(OUT / "movies.rdf", format="xml")
    print(f"Збережено: movies.ttl, movies.jsonld, movies.nt, movies.rdf у {OUT}")
    return g


if __name__ == "__main__":
    main()
