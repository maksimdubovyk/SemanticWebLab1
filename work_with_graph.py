from pathlib import Path

from rdflib import Graph
from rdflib.compare import graph_diff, to_isomorphic
from rdflib.namespace import RDF

from build_graph import FILM, MO, PERSON, bind_prefixes

ROOT = Path(__file__).parent
OUT = ROOT / "output"


def header(text: str) -> None:
    print("\n" + "=" * 78 + f"\n{text}\n" + "=" * 78)


def short(g: Graph, term) -> str:
    try:
        return term.n3(g.namespace_manager)
    except Exception:
        return str(term)


def print_triples(g: Graph, triples, limit: int | None = None) -> None:
    for i, (s, p, o) in enumerate(sorted(triples)):
        if limit is not None and i >= limit:
            print(f"  ... (ще {len(list(triples)) - limit})")
            break
        print(f"  {short(g, s)}  {short(g, p)}  {short(g, o)} .")


def main() -> None:
    header("1. Читання Turtle-файлу output/movies.ttl")
    original = Graph().parse(OUT / "movies.ttl", format="turtle")
    print(f"Прочитано трійок: {len(original)}")

    header("2. Вручну змінений файл movies_edited.ttl — що змінилося")
    edited = Graph().parse(ROOT / "movies_edited.ttl", format="turtle")
    bind_prefixes(edited)
    print(f"Трійок до змін: {len(original)}, після змін: {len(edited)}")
    _, removed, added = graph_diff(to_isomorphic(original), to_isomorphic(edited))
    print(f"\nДодані трійки ({len(added)}):")
    print_triples(edited, added)
    print(f"\nВидалені трійки ({len(removed)}):")
    print_triples(edited, removed)

    g = edited  # далі працюємо з оновленим графом

    header("3а. Усі трійки з предикатом mo:directedBy (фільм -> режисер)")
    print_triples(g, g.triples((None, MO.directedBy, None)))

    header("3б. Перші 15 трійок графу (у відсортованому порядку)")
    print_triples(g, list(g), limit=15)

    header("4а. Трійки, де film:Inception є суб'єктом")
    print_triples(g, g.triples((FILM.Inception, None, None)))

    header("4б. Трійки, де person:LeonardoDiCaprio є суб'єктом або об'єктом")
    print_triples(g, set(g.triples((PERSON.LeonardoDiCaprio, None, None)))
                  | set(g.triples((None, None, PERSON.LeonardoDiCaprio))))

    header("4в. Опис нового фільму film:Tenet (з ручних змін) через g.predicate_objects()")
    for p, o in sorted(g.predicate_objects(FILM.Tenet)):
        print(f"  {short(g, p):<20} {short(g, o)}")

    header("5. Порівняння серіалізацій (Turtle / JSON-LD / N-Triples / RDF/XML)")
    for fname, fmt in [("movies.jsonld", "json-ld"), ("movies.nt", "nt"), ("movies.rdf", "xml")]:
        other = Graph().parse(OUT / fname, format=fmt)
        same = to_isomorphic(other) == to_isomorphic(original)
        print(f"  {fname:<14} трійок: {len(other):<4} ізоморфний Turtle-графу: {same}")

    print(f"\nТипів у графі: rdf:type mo:Film -> {len(set(g.subjects(RDF.type, MO.Film)))} фільмів")


if __name__ == "__main__":
    main()
