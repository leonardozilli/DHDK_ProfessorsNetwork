from bs4 import BeautifulSoup, SoupStrainer
import requests
import json
import re
import codecs
from tqdm import tqdm
from pprint import pprint


class Page(object):
    def __init__(self, target: str):
        self.target = target
        self.last_page = None
        self.pubblicazioni = []
        self.soup = self.get_soup(self.target)

    def get_page(self, target):
        r = requests.get(target)
        if r.status_code == 200:
            return r.text
        else:
            return None

    def get_soup(self, target):
        page = self.get_page(target)
        if page:
            return BeautifulSoup(page, 'lxml', parse_only=SoupStrainer('main', {'id': 'content'}))
        else:
            return None

    def get_qualifica(self):
        if self.soup:
            return self.soup.find('p', {'class': 'qualifica'}).text

    def get_sede(self):
        if self.soup:
            return self.soup.find('p', {'class': 'sede'}).text
    
    def append_pubblicazioni(self, target):
        if self.soup:
            report_list = self.soup.find('div', {'class': 'report-list'})
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
        pagination = self.soup.find('div', {'class': 'pagination'})
        if pagination:
            try:
                self.last_page = pagination.find_all('a', class_=None)[-1].get('href')
                print(self.last_page)
                self.last_page = int(re.search(r'\d+', self.last_page).group(0))
            except IndexError:
                self.last_page = 1

    def get_academic_discipline(self):
        try:
            ad = self.soup.find('p', {'class': 'ssd'}).get_text(strip=True)
            return ad.split(':')[1].strip()
        except AttributeError:
            return None
    
    def get_name(self):
        name = self.soup.find('span', {'itemprop': 'name'}).get_text(strip=True)
        return ', '.join(list(reversed(name.rsplit(' ', 1))))
    
    def get_first_result(self):
        return self.soup.find('a', {'class': 'authority author'})['href']

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


class CrisPublicationsPage(Page):
    def __init__(self, target: str):
        super().__init__(target)
        self.soup = self.get_soup(self.target)
        self.pub_list = []
    
    def cycle_pages(self):
        arrow = self.soup.find('i', {'class':'fa-chevron-circle-right'})
        if arrow:
            self.pub_list += self.get_publications()
            self.soup = self.get_soup('https://cris.unibo.it/' + arrow.parent['href'])
            self.cycle_pages()
        else:
            self.pub_list += self.get_publications()
        return self.pub_list

    def get_publications(self):
        pub_list_page = [href['href'] for href in self.soup.findAll('a', {'class': 'list-group-item'})]
        return pub_list_page


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




def scrape_publications(prof_list, output_dir):
    target = 'https://www.unibo.it/sitoweb/{}/pubblicazioni'
    prof_dict = {key:{'academic discipline':None, 'publications': None} for key in prof_list}

    for prof in tqdm(prof_list):
        print(prof)
        page = Page(target.format(prof))
        page.get_pubblicazioni()
        prof_dict[prof]['academic discipline'] = page.get_academic_discipline()
        prof_dict[prof]['publications'] = page.pubblicazioni

    with open(output_dir, "w") as outfile: 
        json.dump(prof_dict, outfile)

def search_author(name):
    target = 'https://cris.unibo.it/browse?type=author&order=ASC&rpp=20&starts_with=' + name
    search_page = Page(target)
    try:
        return 'https://cris.unibo.it/' + search_page.get_first_result()[:-2] + '100'
    except TypeError:
        print('---------------------------------------------', target, ' not found!')
        return target


def scrape_pub_info(input, output_dir):
    with open(input, "r") as file: 
        data = json.load(file)

    for prof in tqdm(data, desc="Professor"):
        pubs = data[prof]['Publications']
        data[prof]['Publications'] = {}
        for link in tqdm(pubs, desc=f"{prof}'s publications"):
            full_link = 'https://cris.unibo.it' + link
            page = PublicationPage(full_link + '?mode=full')
            data[prof]['Publications'][full_link] = page.build_pub_dict()
    
        with codecs.open(output_dir, "w", "utf-8") as output: 
            json.dump(data, output, indent=4)


def identify_authors(input, output_dir):
    with open(input, "r") as outfile: 
        data = json.load(outfile)
    
    internalAuthorsUniqueList = {author for prof in data.values() for link in prof['Publications'] for author in prof['Publications'][link]['internalAuthor']}

    author_d = {}
    c = 0

    for author in tqdm(list(internalAuthorsUniqueList)):
        c += 1
        author_page = AuthorPage('https://cris.unibo.it' + author)
        try:
            print(f'{c}/{len(internalAuthorsUniqueList)}', author, bool(author_page.get_author_data()))
            author_d[author] = author_page.get_author_data()
        except AttributeError:
            print(f'id {author_page.target} not found')

        with codecs.open(output_dir, "w", "utf-8") as output: 
            json.dump(author_d, output, indent=4)

def scrape_publications():
    dhdk_prof_list = set(['silvio.peroni', 'sofia.pescarin', 'fabio.vitali', 'francesca.tomasi', 'aldo.gangemi', 'paola.italia', 'fabio.tamburini', 'marilena.daquino2', 'saverio.giallorenzo2', 'annafelicia.zuffran2', 'giulio.iovine2', 'ilaria.bartolini', 'giorgio.spedicato', 'monica.palmirani', 'ekaterina.baskakova2', 'simone.ferriani', 'daniele.donati', 'luca.trapin', 'michela.milano'])
    cs_prof_list = set(['claudio.sacerdoticoen', 'armando.bazzani', 'giulia.spaletta', 'serena.morigi', 'stefano.pagliarani9', 'danilo.montesi', 'maurizio.gabbrielli', 'fabio.vitali', 'cosimo.laneve', 'ugo.dallago', 'andrea.asperti', 'gianluigi.zavattaro', 'claudio.sacerdoticoen', 'zeynep.kiziltan', 'alessandro.amoroso', 'lorenzo.donatiello', 'renzo.davoli', 'roberto.gorrieri', 'marco.difelice3', 'daviderossi', 'furio.camillo', 'valentina.presutti', 'ilaria.bartolini', 'luciano.bononi', 'giuseppe.lisanti', 'p.torroni', 'gustavo.marfia', 'ozalp.babaoglu'])
    it_prof_list = set(["bruno.capaci2", "matteo.viale", "luigi.weber", "filippo.milani", "francesco.ferretti", "marco.bazzocchi", "marco.veglia", "francesco.sberlati", "giovanni.baffetti", "sebastiana.nobili", "nicola.bonazzi3", "chiara.coluccia", "alberto.bertoni", "stefano.colangelo", "riccardo.gasperina", "riccardo.tesi", "elisa.dalchiele3", "giuseppina.brunetti", "andrea.villani5", "giuseppe.ledda", "daniele.tripaldi", "lucia.floridi2", "rosa.pugliese", "gloria.gagliardi", "luca.disabatino2", "simone.mattiola", "elisa.scerrati", "l.lugli", "francesca.masini", "silvia.ballare", "fabio.tamburini", "francesco.carbognin", "ferdinando.amigoni", "vanessa.pietrantonio", "federico.bertoni", "stefano.malfatti", "paolo.tinti", "francesca.tomasi", "maddalena.modesti3", "leonardo.quaquarelli", "iolanda.ventura", "francesca.florimbii2", "sandra.costa", "annafelicia.zuffran2", "sebastiano.moruzzi", "guido.gherardi", "costantino.marmo", "berardo.pio", "eleonora.caramelli2", "giovanni.matteucci", "alessandr.zanchettin", "fabio.martelli3", "vincenzo.lavenia", "michele.caputo", "bruna.conconi", "gilberta.golinelli2", "michael.dallapiazza", "annapaola.soncini", 'elisa.dalchiele3', 'giuseppina.brunetti', 'andrea.villani5', 'giuseppe.ledda', 'iolanda.ventura', 'daniele.tripaldi', 'luca.disabatino2', 'lucia.floridi2', 'stefano.malfatti', 'paolo.tinti', 'francesca.tomasi', 'maddalena.modesti3', 'sandra.costa', 'annafelicia.zuffran2', 'francesco.carbognin', 'ferdinando.amigoni', 'vanessa.pietrantonio', 'federico.bertoni', 'bruno.capaci2', 'matteo.viale', 'luigi.weber', 'filippo.milani', 'francesco.ferretti', 'marco.bazzocchi', 'marco.veglia', 'loredana.chines', 'francesco.sberlati', 'giovanni.baffetti', 'sebastiana.nobili', 'nicola.bonazzi3', 'chiara.coluccia', 'alberto.bertoni', 'stefano.colangelo', 'riccardo.gasperina', 'riccardo.tesi'])

    royalty_dict = {'claudio.sacerdoticoen': 'SACERDOTI COEN, CLAUDIO', 'ugo.dallago': 'DAL LAGO, UGO', 'marco.difelice3': 'DI FELICE, MARCO', 'luca.disabatino2': 'DI SABATINO, LUCA', 'elisa.dalchiele3': 'DAL CHIELE, ELISA', 'riccardo.gasperina': 'GASPERINA GERONI, RICCARDO'}

    prof_list = cs_prof_list

    prof_dict = {prof: {'Academic discipline': None, 'Afferenza': None, 'Publications': None} for prof in prof_list}
    for prof in tqdm(prof_list):
        unibo_page = Page(f'https://www.unibo.it/sitoweb/{prof}/en')
        prof_dict[prof]['Academic discipline'] = unibo_page.get_academic_discipline()
        if prof in royalty_dict:
            name = royalty_dict[prof]
            print('royalty', name)
        else:
            name = unibo_page.get_name()
        cris_publications_page = CrisPublicationsPage(search_author(name))
        prof_dict[prof]['Publications'] = cris_publications_page.cycle_pages()

    with codecs.open('./cs_authors.json', "w", "utf-8") as output: 
        json.dump(prof_dict, output, indent=4)
    
def main():

    #scrape_publications()
    #scrape_pub_info('./dhdk_authors.json', './data/dhdk_publications.json')
    #scrape_pub_info('./cs_authors.json', './data/cs_publications.json')
    #scrape_pub_info('./it_authors.json', './data/it_publications.json')
    #identify_authors('./data/dhdk_publications.json', './data/dhdk/dhdk_authors.json')
    #identify_authors('./data/cs_publications.json', './data/cs/cs_authors.json')
    identify_authors('./data/it/it_publications.json', './data/it/it_authors.json')

if __name__ == '__main__':
    main()