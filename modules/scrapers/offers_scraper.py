import csv
import os
import time

import requests
from bs4 import BeautifulSoup

from modules.scrapers.get_offers import OfferScraper
from utils.logger import console_logger
from utils.logger import file_logger

PATH_DATA = 'data'
PATH_MANUFACTURERS_FILE = 'manufacturers.txt'
URL_BASE = 'https://www.otomoto.pl/osobowe/'
OUTPUT_NAME = 'offers.csv'


class ManufacturerScraper:
    """
    Scraps data related to offers of cars from www.otomoto.pl
    Args:
        path_data_directory: path to a directory where data will be stored
        path_manufacturers_file: path to a file with names of manufacturers
    """

    console_logger.info('Initializing a scraper')
    file_logger.info('Initializing a scraper')

    def __init__(self, path_data_directory=PATH_DATA, path_manufacturers_file=PATH_MANUFACTURERS_FILE):
        self.path_manufacturers_file = os.path.join(os.getcwd(), 'inputs', path_manufacturers_file)
        self.path_data_directory = os.path.join(os.getcwd(), 'outputs', path_data_directory)
        self.manufacturers = self.get_manufacturers()
        self.offers = OfferScraper()

    def get_manufacturers(self) -> list:
        """
        Gets a list of manufacturers from a static file
        :return: a list of cars manufacturers names
        """
        with open(self.path_manufacturers_file, 'r', encoding='utf-8') as file:
            manufacturers = file.readlines()

        return manufacturers

    @staticmethod
    def get_links(path: str, i: str) -> list:
        """
        Gets links of car offers from a web page
        :param path:    path to a web page
        :param i:       web page number
        :return:        a list of links
        """
        console_logger.info(f'Scrapping page: {i}')
        file_logger.info(f'Scrapping page: {i}')

        respond = requests.get(f'{path}?page={i}')
        respond.raise_for_status()

        soup = BeautifulSoup(respond.text, features='lxml')

        car_links_section = soup.find('main', attrs={'data-testid': 'search-results'})
        links = [x.find('a', href=True)['href'] for x in car_links_section.find_all('article')]

        console_logger.info(f'Found {len(links)} links')
        file_logger.info(f'Found {len(links)} links')

        return links

    def scrap_manufacturer(self, manufacturer: str) -> None:
        """
        Scraps manufacturer data from otomoto.pl
        :param manufacturer:    car manufacturer name
        :return:                None
        """
        manufacturer = manufacturer.strip()

        console_logger.info(f'Start of scrapping the manufacturer: {manufacturer}')
        file_logger.info(f'Start of scrapping the manufacturer: {manufacturer}')

        # clear a list of offers
        self.offers.clear_list()

        url = f'{URL_BASE}{manufacturer}'

        try:
            respond = requests.get(url)
            respond.raise_for_status()

            soup = BeautifulSoup(respond.text, features='lxml')
            last_page_num = int(soup.find_all('li', attrs={'data-testid': 'pagination-list-item'})[-1].text)

        except Exception as e:
            file_logger.error(f'Error {e} while searching for last_page_num')
            last_page_num = 1

        last_page_num = min(last_page_num, 500)

        console_logger.info(f'Manufacturer has: {last_page_num} subpages')
        file_logger.info(f'Manufacturer has: {last_page_num} subpages')

        pages = range(1, last_page_num + 1)

        for p, page in enumerate(pages):
            links = self.get_links(path=url, i=page)
            self.offers.get_offers(links=links)

            time.sleep(0.2)

        # save a list of offers
        self.offers.save_offers(manufacturer=manufacturer)

        console_logger.info(f'End of scrapping the manufacturer: {manufacturer}')
        file_logger.info(f'End of scrapping the manufacturer: {manufacturer}')

    def scrap_all_manufacturers(self) -> None:
        """
        Loops over list of manufacturers names to scrap data for each one of them
        :return: None
        """
        console_logger.info('Starting scrapping cars...')
        file_logger.info('Starting scrapping cars...')

        for m, manufacturer in enumerate(self.manufacturers):
            self.scrap_manufacturer(manufacturer=manufacturer)

        console_logger.info('End of scrapping manufacturers')
        file_logger.info('End of scrapping manufacturers')

    def dump_data(self) -> None:
        """
        Appends offers data and stores it as a static file
        :return: None
        """

        console_logger.info('Appending the data...')
        file_logger.info('Appending the data...')

        filenames = [
            os.path.join(self.path_data_directory, f'{manufacturer.strip()}.csv') for manufacturer in self.manufacturers
        ]

        combined_data = []

        for f, filename in enumerate(filenames):
            try:
                with open(filename, 'r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    data = list(reader)
                    combined_data.extend(data)

            except Exception as e:
                file_logger.error(f'Error {e} while searching for {filename}')

        with open(os.path.join(self.path_data_directory, OUTPUT_NAME), 'w', encoding='utf-8', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(combined_data)

        console_logger.info(f'Appended data saved as {OUTPUT_NAME}')
        file_logger.info(f'Appended data saved as {OUTPUT_NAME}')
