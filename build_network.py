import json
import pandas as pd
import numpy as np
import networkx as nx
from pprint import pprint
import matplotlib.pyplot as plt
from itertools import combinations


def add_authors(graph, input):
    with open(input, 'r') as f:
        authors = json.load(f)

    for author in authors:
        graph.add_node(authors[author]['Nome completo'], id=author, affiliation=authors[author]['Afferenza'])

def add_edges(graph, input1, input2, threshold=None):
    with open(input2, 'r') as f:
        publications = json.load(f)
    
    with open(input1, 'r') as f:
        authors = json.load(f)

    for prof in publications:
        for link in publications[prof]['Publications']:
            for author, coauthor in combinations(publications[prof]['Publications'][link]['internalAuthor'], 2):
                if graph.has_edge(authors[author]['Nome completo'], authors[coauthor]['Nome completo']):
                    graph[authors[author]['Nome completo']][authors[coauthor]['Nome completo']]['weight'] += 1
                    graph[authors[author]['Nome completo']][authors[coauthor]['Nome completo']]['publications'].append(link)
                else:
                    graph.add_edge(authors[author]['Nome completo'], authors[coauthor]['Nome completo'], weight=1, publications=[link])


def visualize_graph(graph, list):
    color_palette = {
        'DIPARTIMENTO DI FILOLOgraphIA CLASSICA E ITALIANISTICA': 'gold',
        'DIPARTIMENTO DI INFORMATICA - SCIENZA E INgraphEGNERIA': 'green',
    }


    bbox_props = {
        'boxstyle': 'round',
        'facecolor': 'white',
        'edgecolor': 'black',
        'linewidth': 1,
        'pad': 0.5,
        'alpha': 1,
    }

    pos = nx.spring_layout(graph, iterations=30)
    plt.figure(figsize=(15,15))
    nx.draw(graph, 
            pos,
            node_color=[color_palette[node[1]['affiliation']] if color_palette.get(node[1]['affiliation']) else 'blue' for node in graph.nodes(data=True)], 
            node_size = [800 if node[0] in list else 10 for node in graph.nodes(data=True)],)
    for node, data in graph.nodes(data=True):
        if node in list:
            nx.draw_networkx_labels(graph, pos, labels={node: node}, font_size=12, font_color='black', verticalalignment='top', bbox=bbox_props)
        else:
            nx.draw_networkx_labels(graph, pos, labels={node: node}, font_size=5, font_color='black', verticalalignment='top')

    plt.show()

def build_network(graph, authors_json, publications_json):
    add_authors(graph, authors_json)
    add_edges(graph, publications_json, authors_json)



def write_network(graph, output):
    nx.write_gml(graph, output, stringizer=lambda x: str(x))


def main():
    dhdk_prof_list = ['PERONI, SILVIO', 'TOMASI, FRANCESCA', 'VITALI, FABIO', 'PESCARIN, SOFIA', 'GANGEMI, ALDO', 'ITALIA, PAOLA', 'TAMBURINI, FABIO', 'DAQUINO, MARILENA', 'GIALLORENZO, SAVERIO', 'ZUFFRAN, ANNAFELICIA', 'IOVINE, GIULIO', 'BARTOLINI, ILARIA', 'SPEDICATO, GIORGIO', 'PALMIRANI, MONICA', 'BASKAKOVA, EKATERINA', 'FERRIANI, SIMONE']
    cs_prof_list = []
    it_prof_list = []

    dhdk_graph = nx.Graph()
    cs_graph = nx.Graph()
    it_graph = nx.Graph()


    #target_graph = nx.read_gml('./data/{0}/{0}_coauthorship_network.gml'.format('dhdk'))
    build_network(target_graph, './data/it/it_authors.json', './data/it/it_publications.json')
    
    #print(sorted(target_graph.degree(), key=lambda x: x[1]))
    #nx.write_gml(target_graph, 'data/it/it_coauthorship_network.gml', stringizer=lambda x: str(x))
    #print(sorted(target_graph.edges(data=True),key= lambda x: x[2]['weight'],reverse=True)[0])
    #visualize_graph(target_graph, dhdk_prof_list)

if __name__ == '__main__':
    main()