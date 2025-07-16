# cui_scraper.py
import requests
from bs4 import BeautifulSoup
import pandas as pd

base_url = "https://www.archives.gov"
category_list_url = f"{base_url}/cui/registry/category-list"

r = requests.get(category_list_url)
soup = BeautifulSoup(r.text, "html.parser")

categories = []
current_org = ""

for block in soup.select(".field-content"):
    if block.find("h3"):
        current_org = block.text.strip()
    elif block.find("a"):
        a = block.find("a")
        name = a.text.strip()
        url = base_url + a["href"]
        categories.append((name, url, current_org))

data = []
for name, url, org in categories:
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    tables = soup.select("table")

    for table in tables:
        for row in table.select("tr")[1:]:
            cols = row.find_all("td")
            if len(cols) >= 4:
                authority = cols[0].text.strip()
                basic_specified = cols[1].text.strip()
                safeguarding = cols[2].text.strip()
                sanctions = cols[3].text.strip()

                data.append({
                    "Safeguarding and/or Dissemination Authority": safeguarding,
                    "Organizational Category": org,
                    "Authority": authority,
                    "Basic/Specified": basic_specified,
                    "Category": name,
                    "Sanctions": sanctions
                })

df = pd.DataFrame(data)
with pd.ExcelWriter("CUI_Authorities.xlsx", engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="CUI Authorities")
    df.groupby("Category").size().to_excel(writer, sheet_name="Sources Per Category")
    df[df["Sanctions"] != ""].groupby("Category").size().to_excel(writer, sheet_name="Sanctions Per Category")
    pd.DataFrame([{"Total Sources": len(df)}]).to_excel(writer, sheet_name="Metadata")

print("✅ Scraping complete. Excel saved as CUI_Authorities.xlsx")
