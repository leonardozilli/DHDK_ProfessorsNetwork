from bs4 import BeautifulSoup
import requests
import json
import re
import codecs
from pprint import pprint


class Page(object):
    def __init__(self, target: str):
        self.target = target
        self.last_page = None
        self.pubblicazioni = []

    def get_page(self, target):
        r = requests.get(target)
        if r.status_code == 200:
            return r.text
        else:
            return None

    def get_soup(self, target):
        page = self.get_page(target)
        if page:
            return BeautifulSoup(page, 'html.parser')
        else:
            return None

    def get_qualifica(self):
        soup = self.get_soup()
        if soup:
            return soup.find('p', {'class': 'qualifica'}).text

    def get_sede(self):
        soup = self.get_soup()
        if soup:
            return soup.find('p', {'class': 'sede'}).text
    
    def append_pubblicazioni(self, target):
        soup = self.get_soup(target)
        if soup:
            report_list = soup.find('div', {'class': 'report-list'})
            for report in report_list.find_all('p'):
                link = report.find('a').get('href')
                self.pubblicazioni.append(link)

    def get_pubblicazioni(self):
        if not self.last_page:
            self.retrieve_pages()
            self.append_pubblicazioni(self.target)
        for page in range(2, self.last_page + 1):
            self.new_page_target = self.target + '?page={}'.format(page)
            self.append_pubblicazioni(self.new_page_target)
    
    def retrieve_pages(self):
        soup = self.get_soup(self.target)
        pagination = soup.find('div', {'class': 'pagination'})
        if pagination:
            try:
                self.last_page = pagination.find_all('a', class_=None)[-1].get('href')
                print(self.last_page)
                self.last_page = int(re.search(r'\d+', self.last_page).group(0))
            except IndexError:
                self.last_page = 1

class PublicationPage(Page):
    def __init__(self, target: str):
        super().__init__(target)
        keys = ['internalAuthor', 'externalAuthor', 'dc.title', 'dc.keywords', 'scopus.keywords', 'dc.date.issued', 'dc.identifier.doi', 'dc.collection.name']
        self.pub_dict = {key:None for key in keys}
        self.soup = self.get_soup(self.target)
    
    def get_authors(self):
        internal_authors = [author.find(recursive=False).get('href') for author in self.soup.find_all('span', {'class': 'internalContributor'})]
        external_authors = [author.text for author in self.soup.find_all('span', {'class': 'externalContributor'})]
        return internal_authors, external_authors
    
    def get_table_data(self, *value):
        data = []
        for el in value:
            table_data = self.soup.find('td', string=el)
            data.append(table_data.findNext('td').text if table_data else None)
        return tuple(data)

    def build_pub_dict(self):
        self.pub_dict['internalAuthor'], self.pub_dict['externalAuthor'] = self.get_authors()
        self.pub_dict['dc.title'], self.pub_dict['dc.keywords'], self.pub_dict['scopus.keywords'], self.pub_dict['dc.date.issued'], self.pub_dict['dc.identifier.doi'], self.pub_dict['dc.collection.name'] = self.get_table_data('dc.title', 'dc.subject.keywords', 'scopus.subject.keywords', 'dc.date.issued', 'dc.identifier.doi', 'dc.collection.name')
        return self.pub_dict


class AuthorPage(Page):
    def __init__(self, target: str):
        super().__init__(target)
        author_obj = {target: None}
        self.soup = self.get_soup(self.target)

    def get_author_data(self):
        nome_completo = self.soup.find('span', string="Nome completo").parent.parent.parent.select_one("div:nth-of-type(2)").find("p").get_text(strip=True)
        try:
            afferenza = self.soup.find('span', string="Afferenza").parent.parent.parent.select_one("div:nth-of-type(2)").find("p").get_text(strip=True)
            return {"Nome completo": nome_completo, "Afferenza": afferenza, "Author page": self.target}
        except AttributeError:
            return {"Nome completo": nome_completo, "Afferenza": None, "Author page": self.target}
    

def scrape_publications():
    target = 'https://www.unibo.it/sitoweb/{}/pubblicazioni'
    prof_list = ['silvio.peroni', 'sofia.pescarin', 'fabio.vitali', 'francesca.tomasi', 'aldo.gangemi', 'paola.italia', 'fabio.tamburini']
    prof_dict = {key:None for key in prof_list}

    for prof in prof_list:
        print(prof)
        page = Page(target.format(prof))
        page.get_pubblicazioni()
        prof_dict[prof] = page.pubblicazioni

    with open("cris_publications.json", "w") as outfile: 
        json.dump(prof_dict, outfile)

def scrape_pub_info():
    with open("test.json", "r") as outfile: 
        data = json.load(outfile)

    for prof in data:
        c = 0
        print(prof)
        for link in data[prof]:
            c += 1
            print(f'{c}/{len(data[prof])}')
            page = PublicationPage(link + '?mode=full')
            data[prof][link] = page.build_pub_dict()
    
    with codecs.open("data/publications.json", "w", "utf-8") as output: 
        json.dump(data, output, indent=4)


def identify_authors():
    with open("data/publications.json", "r") as outfile: 
        data = json.load(outfile)
    
    internalAuthorsUniqueList = {author for prof in data.values() for link in prof.values() for author in link.get('internalAuthor')}

    author_d = {}
    c = 0

    for author in list(internalAuthorsUniqueList):
        c += 1
        author_page = AuthorPage('https://cris.unibo.it' + author)
        try:
            print(f'{c}/{len(internalAuthorsUniqueList)}', author, bool(author_page.get_author_data()))
            author_d[author] = author_page.get_author_data()
        except AttributeError:
            print(f'id {author_page.target} not found')

    with codecs.open("data/internalAuthors.json", "w", "utf-8") as output: 
        json.dump(author_d, output, indent=4)
    





def main():
    #scrape_publication()
    #scrape_pub_info()
    identify_authors()

if __name__ == '__main__':
    main()