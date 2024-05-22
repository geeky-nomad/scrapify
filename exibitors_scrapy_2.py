import csv
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup


# Function to extract information from a company page
def extract_company_info(company_url):
    try:
        # Fetch the HTML content of the company page
        company_response = requests.get(company_url)
        company_html_content = company_response.text
        company_soup = BeautifulSoup(company_html_content, "html.parser")
        if not company_soup:
            pass

        # Extract company description
        company_description_element = company_soup.find("div", class_="my-4 md:my-8 text-sm md:text-[16px] text-purple")
        company_description = company_description_element.text.strip() if company_description_element else ""

        # Extract company hashtags
        _hashtags_list = []
        company_hastags_element = company_soup.find_all("div",
                                                        class_="relative max-w-fit inline-flex items-center justify-between box-border whitespace-nowrap text-small rounded-full text-default-foreground bg-gradient-main opacity-80 h-5 xl:h-8 min-w-0 xl:min-w-8 p-[2px] before:content-[''] before:absolute before:bg-white before:w-[calc(100%-4px)] before:h-[calc(100%-4px)] before:rounded-large cursor-pointer")
        if company_hastags_element:
            for _single in company_hastags_element:
                _hashtags_list.append(_single.text.strip())
        _hashtags = ', '.join(_hashtags_list)  # remove list by string
        # Extract booth information
        booth_element = company_soup.find("div", class_="text-purple text-xs lg:text-base font-bold")
        booth_info = {"booth number": "", "booth schedule": ""}
        if booth_element:
            booth_number_element = booth_element.find("span", class_="ml-1 uppercase")
            booth_info["booth number"] = booth_number_element.text.strip() if booth_number_element else ""
            booth_schedule_span = booth_element.find("span", class_="ml-2")
            if booth_schedule_span:
                booth_info["booth schedule"] = booth_schedule_span.text.strip()

        # Extract location information
        location_element = company_soup.find("div", class_="mt-2 text-sm xl:text-md uppercase")
        location = location_element.text.strip() if location_element else ""

        # Extract Industry type
        industry_element = company_soup.find('span',
                                             class_='flex-1 p-0 font-bold bg-gradient-main bg-clip-text text-transparent')
        # Get the text inside the <span> tag
        industry_type = industry_element.text if industry_element else ""
        # Find script tags containing relevant data
        script_tags = company_soup.find_all("script", string=re.compile(
            "creation|employees|city|development level|fundraising amount|looking_for|website"))

        # Extract creation, employees, city, development level, fundraising amount, and founding year information
        creation, employees, city, fundraising_amount, official_company_website, development_level, looking_for, type, hashtags, linkedIn, instagram = "", "", "", "", "", "", "", "", "", "", ""
        for script in script_tags:
            script_text = script.get_text()
            # Extracting linkedin, instagram, and creation using regular expressions
            creation_match = re.search(r'\\"creation\\":\\"(.*?)\\"', script_text)
            employees_match = re.search(r'\\"employees\\":\\"(.*?)\\"', script_text)
            city_match = re.search(r'\\"city\\":\\"(.*?)\\"', script_text)
            fundraising_amount_match = re.search(r'\\"fundraising_amount\\":\\"(.*?)\\"', script_text)
            official_website_match = re.search(r'\\"website\\":\\"(.*?)\\"', script_text)
            development_level_match = re.search(r'\\"stage\\":\\"(.*?)\\"', script_text)
            looking_for_match = re.search(r'\\n24:\[(.*?)\]', script_text)
            type_of_company_match = re.search(r'\\"type\\":\\"(.*?)\\"', script_text)
            linkedin_match = re.search(r'\\"linkedin\\":\\"(.*?)\\"', script_text)
            instagram_match = re.search(r'\\"instagram\\":\\"(.*?)\\"', script_text)

            # Extracting values if found
            creation = creation_match.group(1) if creation_match else None
            employees = employees_match.group(1) if employees_match else None
            city = city_match.group(1) if city_match else None
            fundraising_amount = fundraising_amount_match.group(1) if fundraising_amount_match else None
            official_company_website = official_website_match.group(1) if official_website_match else None
            development_level = development_level_match.group(1) if development_level_match else None
            #
            looking = looking_for_match.group(1) if looking_for_match else None
            if looking:
                looking_for_value = looking.replace('\\', '')
                looking_for = looking_for_value.split('","')
            type = type_of_company_match.group(1) if type_of_company_match else None
            linkedIn = linkedin_match.group(1) if linkedin_match else None
            instagram = instagram_match.group(1) if instagram_match else None
            break

        # # Extract company website
        website_element = company_soup.find("a", string="Visit website")
        website = website_element.get("href") if website_element else ""

        # Extract industry information
        industry_element = company_soup.find("p", class_="text-gray text-[16px]", string="industry")
        industry = industry_element.find_next_sibling("p").text.strip() if industry_element else ""
        return {
            "company description": company_description,
            "booth number": booth_info["booth number"],
            "booth schedule": booth_info["booth schedule"],
            "location": location,
            "creation": creation,
            "employees": employees,
            "industry type": industry_type,
            "city": city,
            "fundraising amount": fundraising_amount,
            "official website": official_company_website,
            "development level": development_level,
            "looking for": looking_for,
            "type": type,
            "hashtags": _hashtags,
            "linkedIN": linkedIn,
            "instagram": instagram
        }
    except requests.exceptions.RequestException as e:
        # Skip to the next URL if a connection error occurs
        print(f"Skipping {company_url} due to connection error: {e}")
        return None  # Return None to indicate failure


# Initialize list to store company information
company_info = []
all_products_df = pd.read_csv('company_info_copy.csv')
unique_urls = all_products_df['Company Event URL'].tolist()

# Extract information for each company
count = 0
for url in unique_urls:
    print('Company Entry no------------->', count)
    # Company Name
    company_name = url.split("/")[-1]

    # Company URL
    company_url = f"https://vivatechnology.com/partners/{company_name}"

    # Extract the rest of the information from the company page
    company_info.append([company_name, company_url, extract_company_info(company_url)])
    count += 1
# Write company information to a CSV file
with open("company_info.csv", "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    # Write header
    writer.writerow([
        "Company Name", "Company Event URL", "Location", "Company Description", "Booth Number", "Booth Schedule",
        "Creation", "Employees", "Industry Type", "City",
        "Fundraising Amount",
        "Official Website", "Development Level", "Looking For", "Type of Company(Startup or Not)", "HashTags",
        "LinkedIN",
        "Instagram"
    ])
    # Write data rows
    for company in company_info:
        try:
            writer.writerow([
                company[0], company[1],
                company[2].get("location", ""),
                company[2].get("company description", ""),
                company[2].get("booth number", ""),
                company[2].get("booth schedule", ""),
                company[2].get("creation", ""),
                company[2].get("employees", ""),
                company[2].get("industry type", ""),
                company[2].get("city", ""),
                company[2].get("fundraising amount", ""),
                company[2].get("official website", ""),
                company[2].get("development level", ""),
                company[2].get("looking for", ""),
                company[2].get("type", ""),
                company[2].get("hashtags", ""),
                company[2].get("linkedIN", ""),
                company[2].get("instagram", "")
            ])
        except Exception as e:
            print(f"Error occurred while writing data for {company[0]}: {e}")

print("CSV file created successfully.")

url = "https://www.businesstravelshoweurope.com/exhibitors"
response = requests.get(url)
if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')
    main_div = soup.find('div', class_='js-library-list-outer')
    href_list = []
    if main_div:
        a_tags = main_div.find_all('a', class_='js-librarylink-entry')
        for tag in a_tags:
            href = tag.get('href')
            if href:
                href_list.append(href)
    print(href_list)
else:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
