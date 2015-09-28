#!/usr/bin/python
# -*- coding: UTF-8 -*-


import requests
from lxml import html
import re
import logging, ConfigParser
import sys
from urllib import quote_plus
import importlib


CONFIG_FILE = "leboncoin.cfg"


class MySearch:
    name = None
    search_parameter = None
    max_page = None
    price_min = None
    price_max = None
    lastlog = None

    def __init__(self, name, search_parameter, max_page, price_min, prince_max, lastlog):
        self.name = name
        self.search_parameter = quote_plus(search_parameter)
        self.max_page = max_page
        self.price_min = int(price_min)
        self.price_max = int(price_max)
        self.lastlog = lastlog

    def __str__(self):
        return "{name : %s, search_parameter : %s, max_page : %s, price_min : %s, price_max : %s, lastlog: %s}" % (self.name,  self.search_parameter, self.max_page, self.price_min, self.price_max, self.lastlog)

    def scrap(self):
        alert_text = []
        finish = False
        i=1
        first = None
        while not finish and i <= int(self.max_page):
            page = requests.get('http://www.leboncoin.fr/annonces/offres/ile_de_france/?o='+str(i)+'&q='+self.search_parameter)
            tree = html.fromstring(page.text)
            result = tree.xpath('//div[@class="list-lbc"]/a')
            if i == 1:
                first = result[0].attrib['href']
            
            for elt in result:
                status = "[%s]\n" % self.name
                url = elt.attrib['href']
                if url == self.lastlog:
                    finish = True
                    break
                # title
                status = status + "%s" % elt.attrib['title']
                try:
                    # price
                    price = elt[0][2][3].text.strip()
                    if int(price[:-2]) < self.price_min or int(price[:-2]) > self.price_max:
                        continue
                    status = status + " - %s" % (price)
                except:
                    pass
                     
                status = status + "\n"
                # location
                status = status +  "Lieu: %s\n" % (re.sub('[\s+]', '',elt[0][2][2].text))
                #link
                status = status + "%s\n" % url
                alert_text.append(status)
            i = i + 1
        return alert_text, first


if __name__ == "__main__":
    Config = ConfigParser.SafeConfigParser()
    
    try:
        Config.read(CONFIG_FILE)

        log_level = Config.get("init","log_level")
        log_file = Config.get("init","log_file")
    except:
        sys.exit(sys.exc_info()[0])   
   
    logging.basicConfig(filename=log_file,level=log_level,format='%(asctime)s -- %(name)s -- %(levelname)s -- %(message)s')

    logging.debug('Init scrapper')

    backend = None
    backend_lib = None
    backend_config = None
    try:
        backend_name = Config.get("init","backend")
        backend_config = dict(Config._sections[backend_name])
    except Exception as e:
        logging.error("No backend provided : %s" % e)
        sys.exit()
    logging.debug("Configuring backend %s" % backend_name)

    try:
        backend_lib = importlib.import_module("backend."+backend_name)
    except Exception as e:
        logging.critical("Unknown backend %s" % e)
        sys.exit()

    try:
        backend = backend_lib.init(backend_config)
    except Exception as e:
        logging.critical("Error while initializing backend : %s" % e)
        sys.exit()

    search_sections = [ x[7:] for x in Config.sections() if "search:" in x]
    
    logging.debug("Found %d research parameter : %s" % (len(search_sections), search_sections))
    
    for search_section in search_sections:
        logging.debug("Reading minimum configuration for search %s" % search_section)
        try:
            section_name = "search:"+search_section
            search_parameter = Config.get(section_name,"search_parameter")
            max_page = Config.get(section_name,"max_page")
            price_min = Config.get(section_name,"price_min")
            price_max = Config.get(section_name,"price_max")
            lastlog = Config.get(section_name,"lastlog")
        except ConfigParser.NoOptionError as e:
            logging.error("Missing parameter in config file : %s" % e)
            sys.exit()

        search = MySearch(search_section, search_parameter, max_page, price_min, price_max, lastlog)
        logging.debug("Scrapping %s with parameter %s" % (search_section, search))

        alerts, last = search.scrap()
    
        # update lastlog in config section
        Config.set("search:"+search_section,'lastlog',last)    
        with open(CONFIG_FILE, 'wb') as configfile:
            Config.write(configfile)

        backend.alert(alerts)
    logging.debug("Scrapping finish")

