import json
import pandas as pd
import numpy as np
import networkx as nx
from pprint import pprint
import matplotlib.pyplot as plt
from itertools import combinations


G = nx.Graph()

with open('data/internalAuthors.json', 'r') as f:
    authors = json.load(f)

with open('data/unique_publications.json', 'r') as f:
    publications = json.load(f)

def add_authors(graph):
    for author in authors:
        G.add_node(authors[author]['Nome completo'], id=author, affiliation=authors[author]['Afferenza'])

def add_edges(graph):
    for link in publications:
        for author, coauthor in combinations(publications[link]['internalAuthor'], 2):
            if G.has_edge(authors[author]['Nome completo'], authors[coauthor]['Nome completo']):
                G[authors[author]['Nome completo']][authors[coauthor]['Nome completo']]['weight'] += 1
                G[authors[author]['Nome completo']][authors[coauthor]['Nome completo']]['publications'].append(link)
            else:
                G.add_edge(authors[author]['Nome completo'], authors[coauthor]['Nome completo'], weight=1, publications=[link])


def visualize_graph(graph):
    color_palette = {
        'DIPARTIMENTO DI FILOLOGIA CLASSICA E ITALIANISTICA': 'gold',
        'DIPARTIMENTO DI INFORMATICA - SCIENZA E INGEGNERIA': 'green',
    }

    prof_list = ['PERONI, SILVIO', 'TOMASI, FRANCESCA', 'VITALI, FABIO', 'PESCARIN, SOFIA', 'GANGEMI, ALDO', 'ITALIA, PAOLA', 'TAMBURINI, FABIO', 'DAQUINO, MARILENA', 'GIALLORENZO, SAVERIO', 'ZUFFRAN, ANNAFELICIA', 'IOVINE, GIULIO', 'BARTOLINI, ILARIA', 'SPEDICATO, GIORGIO', 'PALMIRANI, MONICA', 'BASKAKOVA, EKATERINA', 'FERRIANI, SIMONE']

    bbox_props = {
        'boxstyle': 'round',
        'facecolor': 'white',
        'edgecolor': 'black',
        'linewidth': 1,
        'pad': 0.5,
        'alpha': 1,
    }

    pos = nx.spring_layout(G, iterations=30)
    plt.figure(figsize=(15,15))
    nx.draw(graph, 
            pos,
            node_color=[color_palette[node[1]['affiliation']] if color_palette.get(node[1]['affiliation']) else 'blue' for node in G.nodes(data=True)], 
            node_size = [800 if node[0] in prof_list else 10 for node in G.nodes(data=True)],)
    for node, data in G.nodes(data=True):
        if node in prof_list:
            nx.draw_networkx_labels(G, pos, labels={node: node}, font_size=12, font_color='black', verticalalignment='top', bbox=bbox_props)
        else:
            nx.draw_networkx_labels(G, pos, labels={node: node}, font_size=5, font_color='black', verticalalignment='top')


    plt.show()

def analysis(graph):
    betweenness_centrality = nx.betweenness_centrality(G)
    degree_centrality = nx.degree_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    eigenvector_centrality = nx.eigenvector_centrality(G)

    bc_data = pd.DataFrame.from_dict(betweenness_centrality, 
                                columns=["BetweennessCentrality"], 
                                orient="index")

    dc_data = pd.DataFrame.from_dict(degree_centrality, 
                                columns=["DegreeCentrality"], 
                                orient="index")

    cc_data = pd.DataFrame.from_dict(closeness_centrality, 
                                columns=["ClosenessCentrality"], 
                                orient="index")

    ec_data = pd.DataFrame.from_dict(eigenvector_centrality, 
                                columns=["EigenvectorCentrality"], 
                                orient="index")

    centrality_data = pd.concat([bc_data, dc_data, cc_data, ec_data], axis=1)

    print(centrality_data.sort_values(by=['BetweennessCentrality'], ascending=False).head())

def main():
    add_authors(G)
    add_edges(G)
    analysis(G)
    print(G)
    #most recurring collaborations -> print(sorted(G.edges(data=True),key= lambda x: x[2]['weight'],reverse=True)[0])
    visualize_graph(G)

if __name__ == '__main__':
    main()


"""
todo:
    - add weights to edges
    - add keywords
    - associate departments to colors
"""