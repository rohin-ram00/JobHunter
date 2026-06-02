import pandas as pd
import os
from datetime import datetime

from playwright.sync_api import sync_playwright
from crawlers.detector import detect_portal
from crawlers.workday import get_workday_jobs
from utils.scoring import score_job
from utils.filters import is_noise
from utils.storage import (
    load_seen_jobs,
    save_seen_jobs
)
from utils.notifications import (
    notify_completion
)

from crawlers.generic import (
    extract_job_links
)

# ==================================================
# CONFIG
# ==================================================

EXCEL_FILE = "data/JobDataBank.ods"
KEYWORDS_FILE = "keywords.txt"
LOCATIONS_FILE = "locations.txt"
SEEN_FILE = "seen_jobs.json"
OUTPUT_DIR = "outputs"

# ==================================================
# LOAD DATA
# ==================================================
LOCATION_PRIORITY = {

    "Germany": 10,
    "Netherlands": 8,
    "Austria": 7,
    "France": 6,
    "Italy": 5,
    "UK": 5,
    "England": 5,
    "Australia": 3
}

print("Loading job database...")

df = pd.read_excel(
    EXCEL_FILE,
    engine="odf"
)
print(df.columns.tolist())
KEYWORDS = {}

with open(
    KEYWORDS_FILE,
    "r",
    encoding="utf-8"
) as f:

    for line in f:

        line = line.strip()

        if not line:
            continue

        if "|" not in line:
            continue

        keyword, weight = line.split("|")

        KEYWORDS[keyword.strip()] = int(weight)
with open(
    LOCATIONS_FILE,
    "r",
    encoding="utf-8"
) as f:

    LOCATIONS = [
        l.strip()
        for l in f
        if l.strip()
    ]
def find_locations(text):

    text = text.lower()

    found = []

    for location in LOCATIONS:

        if location.lower() in text:

            found.append(
                location
            )

    return found
seen_jobs = load_seen_jobs(
    SEEN_FILE
)

matches = []

# ==================================================
# CRAWL
# ==================================================

with sync_playwright() as p:

    browser = p.chromium.launch(
        headless=True
    )

    page = browser.new_page()

    total_companies = len(df)

    for idx, row in df.iterrows():

        company = str(
            row["Company"]
        )

        country = str(
            row["Country"]
        )

        job_type = str(
    row.get(
        "Type",
        ""
    )
)

        url = str(
            row["Career_URL"]
        )
        if not url or url == "nan":
            continue
        print(
            f"\n[{idx+1}/{total_companies}] "
            f"Scanning {company}"
        )

        try:

            page.goto(
                url,
                timeout=30000
            )

            page.wait_for_load_state(
                "domcontentloaded"
            )

            portal = detect_portal(
                url
            )

            print(
                    f"{company} -> {portal}"
                )

            if portal == "workday":

                links = get_workday_jobs(
                    page,
                    url
                )

            else:

                links = extract_job_links(
                    page,
                    url
                )

            print(
                f"Found {len(links)} "
                f"potential job links"
            )

            for link in links:

                if link in seen_jobs:
                    continue

                try:

                    page.goto(
                        link,
                        timeout=30000
                    )

                    page.wait_for_load_state(
                        "domcontentloaded"
                    )

                    visible_text = page.locator("body").inner_text()

                    score, matched = score_job(
                        visible_text,
                        KEYWORDS
                    )

                    title = page.title()
                    from utils.filters import (
                        is_noise,
                        low_value_job,
                        high_value_job
                    )

                    if is_noise(title):
                        continue

                    if low_value_job(title):
                        score -= 15

                    if high_value_job(title):
                        score += 25
                    combined_text = (
                        title + " " + visible_text
                    )

                    locations_found = find_locations(
                        combined_text
                    )
                    for loc in locations_found:
                        score += LOCATION_PRIORITY.get(
                            loc,
                            0
                        )
                    MIN_SCORE = 45

                    if score < MIN_SCORE:
                        continue
                    title = page.title()
                    
                    if is_noise(title):
                        continue
                    print(
                        f"Match: {title} "
                        f"| Score={score}"
                    )

                    matches.append({

                        "Date":
                            str(
                                datetime.today().date()
                            ),

                        "Company":
                            company,

                        "Country":
                            country,

                        "Type":
                            job_type,

                        "Title":
                            title,

                        "URL":
                            link,

                        "Score":
                            score,

                        "Keywords":
                            ", ".join(
                                matched
                            ),

                        "Locations":
                            ", ".join(
                                locations_found
                            )
                    })

                    seen_jobs[link] = {

                        "title":
                            title,

                        "first_seen":
                            str(
                                datetime.today().date()
                            )
                    }

                except Exception as e:

                    print(
                        f"Failed job page: "
                        f"{link}"
                    )

                    print(e)

        except Exception as e:

            print(
                f"Failed company page: "
                f"{company}"
            )

            print(e)

    browser.close()


# ==================================================
# SAVE RESULTS
# ==================================================

os.makedirs(
    OUTPUT_DIR,
    exist_ok=True
)

results = pd.DataFrame(
    matches
)

today = str(
    datetime.today().date()
)

excel_out = os.path.join(
    OUTPUT_DIR,
    "JobMatches.xlsx"
)

txt_out = os.path.join(
    OUTPUT_DIR,
    "matches.txt"
)

if len(results) > 0:

    results = results.sort_values(
        "Score",
        ascending=False
    )

    if os.path.exists(
        excel_out
    ):

        with pd.ExcelWriter(
            excel_out,
            engine="openpyxl",
            mode="a",
            if_sheet_exists="replace"
        ) as writer:

            results.to_excel(
                writer,
                sheet_name=today,
                index=False
            )

    else:

        with pd.ExcelWriter(
            excel_out,
            engine="openpyxl"
        ) as writer:

            results.to_excel(
                writer,
                sheet_name=today,
                index=False
            )

    results.to_csv(
        txt_out,
        sep="\t",
        index=False
    )

    notify_completion(
        len(results)
    )

    print(
        f"\nSUCCESS: "
        f"{len(results)} matches found"
    )

else:

    print(
        "\nNo new matching jobs found."
    )

# ==================================================
# SAVE SEEN JOBS
# ==================================================

save_seen_jobs(
    SEEN_FILE,
    seen_jobs
)

print(
    "\nRun completed."
)

