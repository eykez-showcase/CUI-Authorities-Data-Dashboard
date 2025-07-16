import requests
from bs4 import BeautifulSoup
import pandas as pd

base_url = "https://www.archives.gov"
category_list_url = f"{base_url}/cui/registry/category-list"

print("📥 Scraping category list...")
r = requests.get(category_list_url)
soup = BeautifulSoup(r.text, "html.parser")

categories = []
current_org = ""

# Loop through content under #block-cui-content (reliable container)
content = soup.select_one("#block-cui-content")
for el in content.find_all(["h3", "li"]):
    if el.name == "h3":
        current_org = el.get_text(strip=True)
    elif el.name == "li":
        a_tag = el.find("a")
        if a_tag:
            name = a_tag.get_text(strip=True)
            url = base_url + a_tag["href"]
            categories.append((name, url, current_org))

print(f"✅ Found {len(categories)} categories.")

# Now scrape details from each category
data = []
for name, url, org in categories:
    print(f"🔍 Scraping: {name}")
    try:
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
    except Exception as e:
        print(f"⚠️ Failed to scrape {name}: {e}")

# Convert and save
df = pd.DataFrame(data)
print(f"📊 Total rows scraped: {len(df)}")

excel_file = "CUI_Authorities.xlsx"
with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
    df.to_excel(writer, index=False, sheet_name="CUI Authorities")

    if not df.empty:
        df.groupby("Category").size().reset_index(name="Source Count").to_excel(writer, sheet_name="Sources Per Category", index=False)
        df[df["Sanctions"] != ""].groupby("Category").size().reset_index(name="Sanction Count").to_excel(writer, sheet_name="Sanctions Per Category", index=False)
        pd.DataFrame([{"Total Sources": len(df)}]).to_excel(writer, sheet_name="Metadata", index=False)
    else:
        pd.DataFrame([{"Error": "No data scraped"}]).to_excel(writer, sheet_name="Metadata", index=False)

print(f"💾 Done! Saved to {excel_file}")
