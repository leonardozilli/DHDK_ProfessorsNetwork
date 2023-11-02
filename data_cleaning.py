import pandas as pd
import json

def extract_data_to_dataframe(json_file, person_name):
    with open(json_file) as f:
        data = json.load(f)

    internal_author = []
    external_author = []
    title = []
    keywords = []
    scopus_keywords = []
    date_issued = []
    doi = []
    collection_name = []
    url_list = []

    for url, url_data in data[person_name].items():
        url_list.append(url)
        internal_author.append(url_data['internalAuthor'])
        external_author.append(url_data['externalAuthor'])
        title.append(url_data.get('dc.title', ''))
        keywords.append(url_data.get('dc.keywords', ''))
        scopus_keywords.append(url_data.get('scopus.keywords', ''))
        date_issued.append(url_data.get('dc.date.issued', ''))
        doi.append(url_data.get('dc.identifier.doi', ''))
        collection_name.append(url_data.get('dc.collection.name', ''))

    df = pd.DataFrame({
        'URL': url_list,
        'Internal_Author': internal_author,
        'External_Author': external_author,
        'Title': title,
        'Keywords': keywords,
        'Scopus_Keywords': scopus_keywords,
        'Date_Issued': date_issued,
        'DOI': doi,
        'Collection_Name': collection_name
    })

    return df

df_peroni = extract_data_to_dataframe('data/publications.json', 'silvio.peroni')
df_pescarin = extract_data_to_dataframe('data/publications.json', 'sofia.pescarin')
df_tamburini = extract_data_to_dataframe('data/publications.json', 'fabio.tamburini')
df_tomasi = extract_data_to_dataframe('data/publications.json', 'francesca.tomasi')
df_vitali = extract_data_to_dataframe('data/publications.json', 'fabio.vitali')
df_gangemi = extract_data_to_dataframe('data/publications.json', 'aldo.gangemi')
df_italia = extract_data_to_dataframe('data/publications.json', 'paola.italia')


all_dataframes = [df_peroni, df_gangemi, df_italia, df_pescarin, df_tamburini, df_tomasi, df_vitali]


combined_df = pd.concat(all_dataframes, ignore_index=True)
combined_df['Keywords'] = combined_df['Keywords'].str.replace(';', ',')
print(combined_df['Scopus_Keywords'])