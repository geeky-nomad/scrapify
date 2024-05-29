import aiohttp
import asyncio
import csv
import os
import sys

from typing import Dict, Any, List, Union

from config import ParticipantEnvLoader

'''
# TODO -> uncomment when need to use BeautifulSoup & selenium
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
'''


class ParticipantManager:
    def __init__(self, base_url: str, total_pages: int, limit: int, info_url: str, interests_url: str,
                 activities_url: str, max_retries: int = 5, auth: bool = False):
        self.base_url = base_url
        self.total_pages = total_pages
        self.limit = limit
        self.info_url = info_url
        self.interests_url = interests_url
        self.activities_url = activities_url
        self.max_retries = max_retries
        self.participants = []
        self.count = 0
        self.auth = auth

    async def fetch_page_data(self, session: aiohttp.ClientSession, page: int) -> None:
        """Fetch data for a single page and store it"""
        payload = {"page": page, "limit": self.limit}
        retries = 0
        while retries < self.max_retries:
            try:
                print('Fetching page:', page)
                if self.auth:
                    cookies = {
                        'PHPSESSID': ParticipantEnvLoader().get('PHPSESSID'),
                        'token': ParticipantEnvLoader().get('TOKEN')
                    }
                    headers = {'Cookie': '; '.join([f'{k}={v}' for k, v in cookies.items()])}
                    async with session.post(self.base_url, json=payload, headers=headers) as response:
                        await self.handle_response(response, page)
                else:
                    async with session.post(self.base_url, json=payload) as response:
                        await self.handle_response(response, page)
                return
            except aiohttp.ClientConnectionError as e:
                print(f"Connection error on page {page}: {e}")
                retries += 1
                wait_time = 2 ** retries  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

        if retries == self.max_retries:
            print(f"Max retries reached for page {page}. Skipping this page.")

    async def handle_response(self, response, page):
        if response.status == 200:
            try:
                if response.headers.get('Content-Type') == 'application/json; charset=UTF-8':
                    data = await response.json()
                    self.extract_participants(data)
                else:
                    print(f"Unexpected content type for page {page}: {response.headers.get('Content-Type')}")
            except aiohttp.ClientResponseError:
                print(f"Failed to decode JSON for page {page}")
        else:
            print(f"Failed to retrieve data for page {page} (status code: {response.status})")

    def extract_participants(self, data: Dict[str, Any]) -> None:
        """Extract participants' data from the JSON response"""
        participant_base_url = ParticipantEnvLoader().get('PARTICIPANT_BASE_URL')
        for participant in data.get('data')['list']:
            delegate_id = participant.get('id', '')
            first_name = participant.get('firstName', '')
            last_name = participant.get('lastName', '')
            company_name = participant.get('company_name', '')
            company_website = participant.get('company_website', '')
            position = participant.get('position', '')
            self.participants.append({
                'delegate_id': delegate_id,
                'participant_url': f'{participant_base_url}/{delegate_id}',
                'first_name': first_name,
                'last_name': last_name,
                'company_name': company_name,
                'company_website': company_website,
                'position': position
            })

    async def process_chunk(self, session: aiohttp.ClientSession, chunk: List[int]) -> None:
        tasks = [self.fetch_page_data(session, page) for page in chunk]
        await asyncio.gather(*tasks)

    async def fetch_data(self) -> None:
        """Fetch data from the API and store it in self.participants"""
        async with aiohttp.ClientSession() as session:
            chunk_size = 100
            for i in range(1, self.total_pages + 1, chunk_size):
                chunk = list(range(i, min(i + chunk_size, self.total_pages + 1)))
                await self.process_chunk(session, chunk)

    def save_to_csv(self, file_name: str) -> None:
        """Save the participants' data to a CSV file, appending if the file already exists"""
        file_exists = os.path.isfile(file_name)

        with open(file_name, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=['Delegate ID', 'Participant URL', 'First Name', 'Last Name',
                                                      'Company Name', 'Company Website', 'Position'])
            if not file_exists:
                writer.writeheader()  # Only write the header if the file does not already exist

            for participant in self.participants:
                writer.writerow({
                    'Delegate ID': participant['delegate_id'],
                    'Participant URL': participant['participant_url'],
                    'First Name': participant['first_name'],
                    'Last Name': participant['last_name'],
                    'Company Name': participant['company_name'],
                    'Company Website': participant['company_website'],
                    'Position': participant['position']
                })

    """ 
    TODO -> uncomment below code block when need to scrape the data through
        1 - Selenium
        2 - BeautifulSoup
    """

    # async def fetch_social_links(self, session: aiohttp.ClientSession, url: str) -> str:
    #     """Fetch social links from the participant's page"""
    #     # Initialize Selenium WebDriver with Chrome
    #     chrome_options = Options()
    #     chrome_options.add_argument("--headless")  # Run headless browser
    #     chrome_options.add_argument("--disable-gpu")
    #     chrome_options.add_argument("--no-sandbox")
    #     driver_service = ChromeService(ChromeDriverManager().install())
    #     driver = webdriver.Chrome(service=driver_service, options=chrome_options)
    #     try:
    #         driver.get(url)
    #         await asyncio.sleep(15)
    #         html_content = driver.page_source
    #         async with session.get(url) as response:
    #             if response.status == 200:
    #                 html_content = await response.text()
    #                 soup = BeautifulSoup(html_content, 'html.parser')
    #                 social_div = soup.find('div', class_='MuiBox-root css-0')
    #                 if social_div:
    #                     social_links = social_div.find_all('div', class_=lambda
    #                         x: x and 'MuiBox-root' in x and 'css-1uob2gb' in x)
    #                     return ', '.join([link.text for link in social_links])
    #             else:
    #                 print(f"Failed to retrieve data for URL {url} (status code: {response.status})")
    #     except aiohttp.ClientConnectionError as e:
    #         print(f"Connection error for URL {url}: {e}")
    #     return ''
    #
    # async def update_csv_with_social_links(self, input_file: str, output_file: str) -> None:
    #     """Update the CSV file with social links for each participant"""
    #     async with aiohttp.ClientSession() as session:
    #         updated_participants = []
    #         with open(input_file, mode='r', newline='', encoding='utf-8') as file:
    #             reader = csv.DictReader(file)
    #             fieldnames = reader.fieldnames + ['Social']
    #             for row in reader:
    #                 participant_url = row['Participant URL']
    #                 social_links = await self.fetch_social_links(session, participant_url)
    #                 row['Social'] = social_links
    #                 updated_participants.append(row)
    #                 self.count += 1
    #                 print('Processed participant:', self.count)
    #                 break
    #
    #         with open(output_file, mode='w', newline='', encoding='utf-8') as file:
    #             writer = csv.DictWriter(file, fieldnames=fieldnames)
    #             writer.writeheader()
    #             writer.writerows(updated_participants)

    async def fetch_from_url(self, session: aiohttp.ClientSession, url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        retries = 0
        while retries < self.max_retries:
            try:
                print(f'Fetching data from {url} with payload {payload}')
                if self.auth:
                    # If authentication is required, set the cookies
                    cookies = {
                        'PHPSESSID': ParticipantEnvLoader().get('PHPSESSID'),
                        'token': ParticipantEnvLoader().get('TOKEN')
                    }
                    headers = {'Cookie': '; '.join([f'{k}={v}' for k, v in cookies.items()])}
                    async with session.post(url, json=payload, headers=headers) as response:
                        return await self.handle_additionl_response(response, url)
                else:
                    async with session.post(url, json=payload) as response:
                        return await self.handle_additionl_response(response, url)
            except aiohttp.ClientConnectionError as e:
                print(f"Connection error for {url}: {e}")
                retries += 1
                wait_time = 2 ** retries  # Exponential backoff
                print(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)

        if retries == self.max_retries:
            print(f"Max retries reached for {url}. Skipping this request.")
        return {}

    async def handle_additionl_response(self, response, url):
        if response.status == 200:
            return await response.json()
        else:
            print(f"Failed to retrieve data from {url} (status code: {response.status})")
            return {}

    async def fetch_additional_info(self, session: aiohttp.ClientSession, delegate_id: str) -> Dict[str, str]:
        payload = {"id": delegate_id}
        data = await self.fetch_from_url(session, self.info_url, payload)
        keys_mapping = {
            'Country': 'Country',
            'Attendee Type': 'Attendee Type',
            'Company type': 'Company Type',
            'Twitter': 'Twitter',
            'Linkedin': 'Linkedin',
            'YouTube': 'YouTube',
            'Facebook': 'Facebook'
        }
        return self.extract_info(data, keys_mapping)

    def extract_info(self, data_items: Union[Dict[str, Any], List[Dict[str, Any]]], keys_mapping: Dict[str, str]) -> \
            Dict[str, str]:
        """Extract specific fields from data items."""
        result = {value: '' for value in keys_mapping.values()}
        if isinstance(data_items, dict):
            for key, value in keys_mapping.items():
                if key == 'Interests' or key == 'Activities':
                    items = data_items.get('data').get('list')
                    if not items:
                        return result
                    else:
                        result[value] = ', '.join(item.get('name', '') for item in items if 'name' in item)
                else:
                    items = data_items.get('data', [])
                    for item in items:
                        title = item.get('title')
                        values = item.get('values', [])
                        if title in keys_mapping:
                            result[keys_mapping[title]] = ', '.join(values)
        return result

    async def fetch_interests_info(self, session: aiohttp.ClientSession, delegate_id: str) -> Dict[str, str]:
        payload = {"id": delegate_id}
        data = await self.fetch_from_url(session, self.interests_url, payload)
        keys_mapping = {'Interests': 'Interests'}
        return self.extract_info(data, keys_mapping)

    async def fetch_activities_info(self, session: aiohttp.ClientSession, delegate_id: str) -> Dict[str, str]:
        payload = {"id": delegate_id}
        data = await self.fetch_from_url(session, self.activities_url, payload)
        keys_mapping = {'Activities': 'Activities'}
        return self.extract_info(data, keys_mapping)

    async def fetch_and_update_row(self, session: aiohttp.ClientSession, row: Dict[str, str], delegate_id: str) -> Dict[
        str, str]:
        info = await self.fetch_additional_info(session, delegate_id)
        row.update(info)
        interests = await self.fetch_interests_info(session, delegate_id)
        row.update(interests)
        activities = await self.fetch_activities_info(session, delegate_id)
        row.update(activities)
        return row

    async def update_csv_with_additional_info(self, input_file: str, output_file: str) -> None:
        updated_participants = []
        async with aiohttp.ClientSession() as session:
            with open(input_file, mode='r', newline='', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                fieldnames = reader.fieldnames + ['Country', 'Attendee Type', 'Company Type', 'Twitter', 'Linkedin',
                                                  'YouTube', 'Facebook', 'Interests', 'Activities']
                tasks = [self.fetch_and_update_row(session, row, row['Delegate ID']) for row in reader]
                updated_participants = await asyncio.gather(*tasks)

        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(updated_participants)

    def run(self, mode: str, file_name: str) -> None:
        if mode == "fetch":
            asyncio.run(self.fetch_data())
            self.save_to_csv(file_name)
            """
            TODO -> uncomment below code when need to scrape the data through 
            1 - Selenium
            2 - BeautifulSoup

            # asyncio.run(self.update_csv_with_social_links(file_name, "participants_with_social.csv"))
            # print("Data successfully saved to participants_with_social.csv")
            """
        elif mode == "update":
            asyncio.run(self.update_csv_with_additional_info(file_name, "final_auth_participants.csv"))
            print("Data successfully updated and saved to participants_updated.csv")
        else:
            print("Invalid mode. Use 'fetch' to fetch data or 'update' to update data.")


if __name__ == "__main__":
    # Define parameters
    BASE_URL = ParticipantEnvLoader().get('BASE_URL')
    TOTAL_PAGES = 26
    LIMIT = 60
    INFO_URL = ParticipantEnvLoader().get('INFO_URL')
    INTERESTS_URL = ParticipantEnvLoader().get('INTERESTS_URL')
    ACTIVITIES_URL = ParticipantEnvLoader().get('ACTIVITIES_URL')

    # Command-line argument for mode
    if len(sys.argv) != 3:
        print("Usage: python script.py <mode> <file_name>")
        print("Modes: 'fetch' to fetch data, 'update' to update data")
        sys.exit(1)

    mode = sys.argv[1]
    file_name = sys.argv[2]

    # Create an instance of ParticipantManager
    AUTH: bool = False  # change it accordingly
    manager = ParticipantManager(BASE_URL, TOTAL_PAGES, LIMIT, INFO_URL, INTERESTS_URL, ACTIVITIES_URL, auth=AUTH)
    # Run the manager with the specified mode and file name
    manager.run(mode, file_name)
