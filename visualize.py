from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.patches import Patch
from rdflib import Graph, URIRef
from rdflib.namespace import FOAF, RDF, RDFS, DCTERMS

from build_graph import MO, PERSON

OUT = Path(__file__).parent / "output"

TYPE_COLORS = {
    MO.Film: "#e4572e",
    MO.Director: "#7b2cbf",
    MO.Actor: "#29335c",
    MO.Genre: "#f3a712",
    MO.Country: "#2a9d8f",
    MO.Studio: "#8d99ae",
}


def label(g: Graph, node: URIRef) -> str:
    for p in (DCTERMS.title, FOAF.name, RDFS.label):
        v = g.value(node, p)
        if v is not None:
            return str(v)
    return g.qname(node)


def node_type(g: Graph, node: URIRef):
    for t in g.objects(node, RDF.type):
        if t in TYPE_COLORS:
            return t
    return None


def to_nx(g: Graph, keep=None) -> nx.MultiDiGraph:
    G = nx.MultiDiGraph()
    for s, p, o in g:
        if not isinstance(o, URIRef) or p == RDF.type or not str(p).startswith(str(MO)):
            continue
        if node_type(g, s) is None or node_type(g, o) is None:
            continue
        if keep is not None and not keep(s, p, o):
            continue
        G.add_edge(s, o, label=g.qname(p).split(":")[1])
    return G


def draw(g: Graph, G: nx.MultiDiGraph, path: Path, title: str, edge_labels: bool, figsize, pos):
    plt.figure(figsize=figsize)
    colors = [TYPE_COLORS[node_type(g, n)] for n in G.nodes]
    sizes = [900 if node_type(g, n) == MO.Film else 450 for n in G.nodes]
    nx.draw_networkx_edges(G, pos, alpha=0.35, arrows=True, arrowsize=8,
                           connectionstyle="arc3,rad=0.05")
    nx.draw_networkx_nodes(G, pos, node_color=colors, node_size=sizes, alpha=0.95)
    nx.draw_networkx_labels(G, pos, labels={n: label(g, n) for n in G.nodes}, font_size=7)
    if edge_labels:
        el = {(u, v): d["label"] for u, v, d in G.edges(data=True)}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=el, font_size=6, font_color="#555")
    legend = [Patch(color=c, label=g.qname(t)) for t, c in TYPE_COLORS.items()]
    plt.legend(handles=legend, loc="lower left", fontsize=9)
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Збережено {path.name}: {G.number_of_nodes()} вузлів, {G.number_of_edges()} ребер")


def main(g: Graph | None = None):
    if g is None:
        g = Graph().parse(OUT / "movies.ttl", format="turtle")
    OUT.mkdir(exist_ok=True)

    G_full = to_nx(g)
    draw(g, G_full, OUT / "graph_full.png", "RDF-граф «Фільми»: сутності та зв'язки",
         edge_labels=False, figsize=(22, 16), pos=nx.kamada_kawai_layout(nx.Graph(G_full)))

    nolan_films = set(g.subjects(MO.directedBy, PERSON.ChristopherNolan))
    G_nolan = to_nx(g, keep=lambda s, p, o: s in nolan_films
                    or (s == PERSON.ChristopherNolan and p == MO.bornIn))
    inner = sorted(nolan_films) + [PERSON.ChristopherNolan]
    outer = sorted((n for n in G_nolan.nodes if n not in inner), key=lambda n: str(node_type(g, n)))
    draw(g, G_nolan, OUT / "graph_nolan.png", "Фрагмент графу: фільми Крістофера Нолана",
         edge_labels=True, figsize=(16, 14), pos=nx.shell_layout(G_nolan, [inner, outer]))


if __name__ == "__main__":
    main()
