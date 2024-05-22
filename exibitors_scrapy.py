import re
import csv
from typing import List, Tuple, Optional, Set
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.businesstravelshoweurope.com/"
MAIN_URL = "https://www.businesstravelshoweurope.com/exhibitors"


class CompanyInfoExtractor:
    __slots__ = ('company_url', 'soup')

    def __init__(self, company_url: str):
        self.company_url = company_url
        self.soup = self._get_soup()

    def _get_soup(self) -> Optional[BeautifulSoup]:
        response = requests.get(self.company_url)
        if response.status_code == 200:
            return BeautifulSoup(response.content, 'html.parser')
        return None

    def _extract_text(self, selector: str, default: str = 'N/A') -> str:
        element = self.soup.select_one(selector) if self.soup else None
        return element.text.strip() if element else default

    def _extract_address(self) -> str:
        if not self.soup:
            return 'N/A'

        address_div = self.soup.find('div', class_='m-exhibitor-entry__item__body__contacts__address')
        if not address_div:
            return 'N/A'

        address_parts = []
        h4 = address_div.find('h4')
        if h4:
            initial_text = h4.next_sibling.strip() if h4.next_sibling and isinstance(h4.next_sibling, str) else ''
            if initial_text:
                address_parts.append(initial_text)
            for sibling in h4.next_siblings:
                if sibling.name == 'br':
                    next_element = sibling.next_sibling
                    if next_element and isinstance(next_element, str):
                        address_parts.append(next_element.strip())
        return ', '.join(address_parts)

    def _extract_libraries_info(self) -> Tuple[str, str, str]:
        if not self.soup:
            return 'N/A', 'N/A', 'N/A'

        parent_div = self.soup.find('div', class_='m-exhibitor-entry__item__body__libraries')
        if not parent_div:
            return 'N/A', 'N/A', 'N/A'

        sub_divs = parent_div.find_all('div', class_='m-exhibitor-entry__item__body__libraries__library')
        all_span_texts = [', '.join(span.get_text() for span in sub_div.find_all('span')) for sub_div in sub_divs]

        product_category = all_span_texts[0] if len(all_span_texts) > 0 else 'N/A'
        industry = all_span_texts[1] if len(all_span_texts) > 1 else 'N/A'
        sustainability_initiative = all_span_texts[2] if len(all_span_texts) > 2 else 'N/A'

        return product_category, industry, sustainability_initiative

    def _extract_social_media(self) -> Tuple[str, str, str, str]:
        if not self.soup:
            return 'N/A', 'N/A', 'N/A', 'N/A'

        li_tags = self.soup.find_all('li', class_='m-exhibitor-entry__item__body__contacts__additional__social__item')
        facebook_url, linkedin_url, instagram_url, youtube_url = 'N/A', 'N/A', 'N/A', 'N/A'

        for li_tag in li_tags:
            a_tag = li_tag.find('a')
            if a_tag:
                href = a_tag.get('href')
                if "facebook.com" in href:
                    facebook_url = href
                elif "linkedin.com" in href:
                    linkedin_url = href
                elif "instagram.com" in href:
                    instagram_url = href
                elif "youtube.com" in href:
                    youtube_url = href

        return facebook_url, linkedin_url, instagram_url, youtube_url

    def _extract_website_url(self) -> str:
        if not self.soup:
            return 'N/A'

        # The website might be in a div with class 'm-exhibitor-entry__item__body__contacts__additional__button'
        compay_website_div = self.soup.find('div', class_='m-exhibitor-entry__item__body__contacts__additional__button')
        if compay_website_div:
            a_tag = compay_website_div.find('a')
            if a_tag and 'href' in a_tag.attrs:
                return a_tag['href']

        # Fallback check for possible direct link in case class names change
        a_tag = self.soup.find('a', href=True, string=re.compile(r'website', re.I))
        if a_tag:
            return a_tag['href']

        return 'N/A'

    def extract_info(self) -> Tuple[str, str, str, str, str, str, str, str, str, str, str, str]:
        company_name = self._extract_text('h1.m-exhibitor-entry__item__header__infos__title')
        stand_info = self._extract_text('div.m-exhibitor-entry__item__header__infos__stand')
        usp_info = self._extract_text('div.m-exhibitor-entry__item__body__additional__item__value')
        address = self._extract_address()
        product_category, industry, sustainability_initiative = self._extract_libraries_info()
        website_url = self._extract_website_url()
        facebook_url, linkedin_url, instagram_url, youtube_url = self._extract_social_media()

        return (company_name, stand_info, usp_info, address, product_category, industry, sustainability_initiative,
                website_url, facebook_url, linkedin_url, instagram_url, youtube_url)


class ExhibitorsScraper:
    __slots__ = ('main_url', 'base_url', 'data')

    def __init__(self, main_url: str, base_url: str):
        self.main_url = main_url
        self.base_url = base_url
        self.data: List[List[str]] = []

    def _get_exhibitor_links(self) -> Set[str]:
        response = requests.get(self.main_url)
        if response.status_code != 200:
            return set()

        soup = BeautifulSoup(response.content, 'html.parser')
        main_div = soup.find('div', class_='js-library-list-outer')
        if not main_div:
            return set()

        a_tags = main_div.find_all('a', class_='js-librarylink-entry')
        return {tag.get('href') for tag in a_tags if tag.get('href')}

    def scrape(self) -> None:
        href_list = self._get_exhibitor_links()

        for count, href in enumerate(href_list, 1):
            company_url = self.base_url + href
            extractor = CompanyInfoExtractor(company_url)
            company_info = extractor.extract_info()
            self.data.append([company_info[0], company_url] + list(company_info[1:]))
            print(f'Count: {count}, Company name: {company_info[0]}')

    def save_to_csv(self, filename: str) -> None:
        headers = ['Company Name', 'Company URL', 'Stand', 'Company USP', 'Address', 'PRODUCT CATEGORY', 'INDUSTRIES',
                   'SUSTAINABILITY INITIATIVE', 'Official Website', 'Facebook handle', 'LinkedIn handle',
                   'Instagram handle', 'YouTube handle']
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(self.data)
        print(f"Data successfully saved to {filename}")


if __name__ == "__main__":
    scraper = ExhibitorsScraper(MAIN_URL, BASE_URL)
    scraper.scrape()
    scraper.save_to_csv('exhibitors_info.csv')
