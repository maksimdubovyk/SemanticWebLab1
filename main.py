"""Запуск усіх етапів лабораторної роботи по черзі."""

import build_graph
import errors_demo
import queries
import visualize
import wikidata_link
import work_with_graph


def section(title: str) -> None:
    print("\n" + "#" * 78 + f"\n# {title}\n" + "#" * 78)


if __name__ == "__main__":
    section("П.2 Побудова RDF-графу та серіалізація")
    g = build_graph.main()
    section("П.2 Візуалізація")
    visualize.main(g)
    section("П.3 Робота з RDF-графом")
    work_with_graph.main()
    section("П.4 SPARQL-запити")
    queries.main()
    section("П.5 Поєднання з Wikidata")
    wikidata_link.main()
    section("П.6 Помилкові та виправлені приклади")
    errors_demo.e1_turtle_syntax()
    errors_demo.e2_untyped_year()
    errors_demo.e3_language_tag()
    errors_demo.e4_wikidata_units()
