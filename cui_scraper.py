import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Setup ---
os.makedirs("data", exist_ok=True)
chrome_options = Options()
chrome_options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

base_url = "https://www.archives.gov"
main_url = f"{base_url}/cui/registry/category-list"
driver.get(main_url)
time.sleep(2)

# --- Parse main table ---
soup = BeautifulSoup(driver.page_source, 'html.parser')
table = soup.find('table', id='fd-table-1')
rows = table.find('tbody').find_all('tr')

categories = []

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
        categories.append((org_index, cui_name, cui_link))

print(f"✅ Found {len(categories)} categories.")

# --- Scrape each category page ---
data = []

for i, (org, name, url) in enumerate(categories):
    print(f"🔍 [{i+1}/{len(categories)}] Scraping: {name}")
    try:
        driver.get(url)
        time.sleep(1)
        detail_soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = detail_soup.find_all("table")

        for table in tables:
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if len(headers) >= 4 and "authority" in headers[0] and "basic" in headers[1]:
                for tr in table.find_all("tr")[1:]:
                    tds = tr.find_all("td")
                    if len(tds) >= 4:
                        authority = tds[0].get_text(strip=True)
                        basic_specified = tds[1].get_text(strip=True)
                        safeguarding = tds[2].get_text(strip=True)
                        sanctions = tds[3].get_text(strip=True)

                        data.append({
                            "Safeguarding and/or Dissemination Authority": safeguarding,
                            "Organizational Category": org,
                            "Authority": authority,
                            "Basic/Specified": basic_specified,
                            "Category": name,
                            "Sanctions": sanctions,
                            "Detail Page": url
                        })
    except Exception as e:
        print(f"⚠️ Failed to scrape {name}: {e}")

driver.quit()

# --- Save to Excel ---
df = pd.DataFrame(data)
print(f"📊 Total rows scraped: {len(df)}")

print(df.head())
df.to_csv("data/debug_dump.csv", index=False)

excel_path = "data/cui_authorities_full.xlsx"
with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="CUI Authorities")

    if not df.empty:
        df.groupby("Category").size().reset_index(name="Source Count") \
            .to_excel(writer, sheet_name="Sources Per Category", index=False)
        df[df["Sanctions"] != ""].groupby("Category").size().reset_index(name="Sanction Count") \
            .to_excel(writer, sheet_name="Sanctions Per Category", index=False)
        pd.DataFrame([{"Total Sources": len(df)}]).to_excel(writer, sheet_name="Metadata", index=False)
    else:
        pd.DataFrame([{"Error": "No data scraped"}]).to_excel(writer, sheet_name="Metadata", index=False)

print(f"✅ Full scrape complete. Excel saved to {excel_path}")
