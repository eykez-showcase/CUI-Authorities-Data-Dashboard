from bs4 import BeautifulSoup
import pandas as pd
import time
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

import os

# Ensure 'data/' folder exists
os.makedirs("data", exist_ok=True)

chrome_options = Options()
chrome_options.add_argument("--headless")

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

base_url = "https://www.archives.gov"
main_url = "https://www.archives.gov/cui/registry/category-list"
driver.get(main_url)
time.sleep(2)

# --- Parse Main Table ---
soup = BeautifulSoup(driver.page_source, 'html.parser')
table = soup.find('table', id='fd-table-1')
rows = table.find('tbody').find_all('tr')

data = []

for row in rows:
    tds = row.find_all('td')
    if len(tds) < 2:
        continue
    org_index = tds[0].get_text(strip=True)
    for li in tds[1].find_all('li'):
        a = li.find('a')
        if not a:
            continue
        cui_name = a.get_text(strip=True)
        cui_link = urljoin(base_url, a['href'])

        # Visit detail page
        driver.get(cui_link)
        time.sleep(1.5)
        detail_soup = BeautifulSoup(driver.page_source, 'html.parser')

        # Extract authorities from tables
        tables = detail_soup.find_all("table")
        for table in tables:
            for tr in table.find_all("tr")[1:]:  # skip header
                tds_inner = tr.find_all("td")
                if len(tds_inner) >= 4:
                    authority = tds_inner[0].get_text(strip=True)
                    basic_specified = tds_inner[1].get_text(strip=True)
                    safeguarding = tds_inner[2].get_text(strip=True)
                    sanctions = tds_inner[3].get_text(strip=True)

                    data.append({
                        "Safeguarding and/or Dissemination Authority": safeguarding,
                        "Organizational Category": org_index,
                        "Authority": authority,
                        "Basic/Specified": basic_specified,
                        "Category": cui_name,
                        "Sanctions": sanctions,
                        "Detail Page": cui_link
                    })

driver.quit()

# --- Save to Excel ---
df = pd.DataFrame(data)
excel_path = "data/cui_authorities_full.xlsx"
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="CUI Authorities")
    df.groupby("Category").size().reset_index(name="Source Count") \
        .to_excel(writer, sheet_name="Sources Per Category", index=False)
    df[df["Sanctions"] != ""].groupby("Category").size().reset_index(name="Sanction Count") \
        .to_excel(writer, sheet_name="Sanctions Per Category", index=False)
    pd.DataFrame([{"Total Sources": len(df)}]).to_excel(writer, sheet_name="Metadata", index=False)

print(f"✅ Full scrape complete. Excel saved to {excel_path}")
