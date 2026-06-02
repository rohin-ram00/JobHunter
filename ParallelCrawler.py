import argparse
import asyncio
import os
import re
from datetime import datetime, timedelta
from html.parser import HTMLParser
from urllib.parse import urljoin

import pandas as pd

from crawlers.detector import detect_portal
from utils.filters import bad_url, high_value_job, is_noise, low_value_job
from utils.scoring import score_job
from utils.storage import load_seen_jobs, save_seen_jobs

try:
    from utils.notifications import notify_completion
except ModuleNotFoundError:
    def notify_completion(num_matches):
        print(
            f"Notification skipped: {num_matches} new jobs found"
        )


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USERS_DIR = os.path.join(BASE_DIR, "users")

EXCEL_FILE = os.path.join(BASE_DIR, "data", "JobDataBank.ods")
KEYWORDS_FILE = os.path.join(BASE_DIR, "users", "Rohin", "keywords.txt")
LOCATIONS_FILE = os.path.join(BASE_DIR, "users", "Rohin", "locations.txt")
SEEN_FILE = os.path.join(BASE_DIR, "users", "Rohin", "seen_jobs.json")
OUTPUT_DIR = os.path.join(BASE_DIR, "users", "Rohin", "outputs")
POTENTIAL_JOBS_FILE = os.path.join(OUTPUT_DIR, "PotentialJobs.xlsx")
POTENTIAL_JOBS_TXT_FILE = os.path.join(OUTPUT_DIR, "potential_jobs.txt")

DEFAULT_CONCURRENCY = 5
DEFAULT_TIMEOUT_MS = 30000
DEFAULT_MIN_SCORE = 45
MAX_JOB_LINKS_PER_COMPANY = 80
JOB_PAGE_CONCURRENCY_PER_COMPANY = 5

LOCATION_PRIORITY = {
    "Germany": 10,
    "Netherlands": 8,
    "Austria": 7,
    "France": 6,
    "Italy": 5,
    "UK": 5,
    "England": 5,
    "Australia": 3,
}

JOB_PATTERNS = [
    "job",
    "jobs",
    "career",
    "careers",
    "vacancy",
    "vacancies",
    "opening",
    "position",
]

POSTED_DATE_PATTERNS = [
    r"posted\s+on\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
    r"posted\s+on\s+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
    r"posted\s+on\s+(\d{4}[./-]\d{1,2}[./-]\d{1,2})",
    r"date\s+posted\s*[:\-]?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
    r"date\s+posted\s*[:\-]?\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
    r"published\s+on\s+([A-Za-z]+\s+\d{1,2},?\s+\d{4})",
    r"published\s+on\s+(\d{1,2}[./-]\d{1,2}[./-]\d{2,4})",
]


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return

        for name, value in attrs:
            if name.lower() == "href" and value:
                self.links.append(value)


def load_keywords(filepath):
    keywords = {}

    with open(
        filepath,
        "r",
        encoding="utf-8",
    ) as f:
        for line in f:
            line = line.strip()

            if not line or "|" not in line:
                continue

            keyword, weight = line.split(
                "|",
                1,
            )

            keywords[keyword.strip()] = int(weight)

    return keywords


def load_locations(filepath):
    with open(
        filepath,
        "r",
        encoding="utf-8",
    ) as f:
        return [
            line.strip()
            for line in f
            if line.strip()
        ]


def find_locations(text, locations):
    text = text.lower()

    return [
        location
        for location in locations
        if location.lower() in text
    ]


def extract_generic_job_links(html, company_url):
    parser = LinkExtractor()
    parser.feed(html)

    links = []

    for href in parser.links:
        if any(pattern in href.lower() for pattern in JOB_PATTERNS):
            full_link = urljoin(
                company_url,
                href,
            )

            if bad_url(full_link):
                continue

            links.append(full_link)

    return sorted(set(links))


def extract_workday_job_links(html, company_url):
    matches = re.findall(
        r'href="([^"]+job[^"]+)"',
        html,
        flags=re.IGNORECASE,
    )

    return sorted(
        {
            urljoin(
                company_url,
                match,
            )
            for match in matches
        }
    )


def parse_date_value(value):
    parsed = pd.to_datetime(
        value,
        errors="coerce",
        dayfirst=True,
    )

    if pd.isna(parsed):
        return ""

    return str(parsed.date())


def extract_posted_date(text):
    text = re.sub(
        r"\s+",
        " ",
        text,
    )
    lower_text = text.lower()
    today = datetime.today().date()

    relative_match = re.search(
        r"posted\s+(\d{1,3})\s+days?\s+ago",
        lower_text,
    )
    if relative_match:
        days = int(relative_match.group(1))
        return str(today - timedelta(days=days))

    if re.search(r"posted\s+(today|heute)", lower_text):
        return str(today)

    if re.search(r"posted\s+(yesterday|gestern)", lower_text):
        return str(today - timedelta(days=1))

    german_relative_match = re.search(
        r"vor\s+(\d{1,3})\s+tagen?",
        lower_text,
    )
    if german_relative_match:
        days = int(german_relative_match.group(1))
        return str(today - timedelta(days=days))

    for pattern in POSTED_DATE_PATTERNS:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
        if match:
            posted_date = parse_date_value(
                match.group(1)
            )

            if posted_date:
                return posted_date

    return ""


async def collect_job_links(page, company_url):
    portal = detect_portal(company_url)

    await page.goto(
        company_url,
        timeout=DEFAULT_TIMEOUT_MS,
        wait_until="domcontentloaded",
    )

    html = await page.content()

    if portal == "workday":
        links = extract_workday_job_links(
            html,
            company_url,
        )
    else:
        links = extract_generic_job_links(
            html,
            company_url,
        )

    return portal, links[:MAX_JOB_LINKS_PER_COMPANY]


async def score_job_page(
    context,
    link,
    company,
    country,
    job_type,
    keywords,
    locations,
    min_score,
):
    page = await context.new_page()

    try:
        await page.goto(
            link,
            timeout=DEFAULT_TIMEOUT_MS,
            wait_until="domcontentloaded",
        )

        visible_text = await page.locator("body").inner_text()
        title = await page.title()

        score, matched = score_job(
            visible_text,
            keywords,
        )

        posted_date = extract_posted_date(
            visible_text
        )

        if is_noise(title):
            return {
                "CrawlDate": str(datetime.today().date()),
                "PostedDate": posted_date,
                "Company": company,
                "Country": country,
                "Type": job_type,
                "Title": title,
                "URL": link,
                "Score": score,
                "Keywords": ", ".join(matched),
                "Locations": "",
                "Matched": False,
                "Decision": "Skipped noise",
            }

        if low_value_job(title):
            score -= 15

        if high_value_job(title):
            score += 25

        locations_found = find_locations(
            f"{title} {visible_text}",
            locations,
        )

        for location in locations_found:
            score += LOCATION_PRIORITY.get(
                location,
                0,
            )

        return {
            "Date": str(datetime.today().date()),
            "CrawlDate": str(datetime.today().date()),
            "PostedDate": posted_date,
            "Company": company,
            "Country": country,
            "Type": job_type,
            "Title": title,
            "URL": link,
            "Score": score,
            "Keywords": ", ".join(matched),
            "Locations": ", ".join(locations_found),
            "Matched": score >= min_score,
            "Decision": "Matched" if score >= min_score else "Below threshold",
        }

    finally:
        await page.close()


async def scan_company(
    browser,
    row,
    idx,
    total_companies,
    seen_links,
    keywords,
    locations,
    min_score,
):
    company = str(row["Company"])
    country = str(row["Country"])
    job_type = str(
        row.get(
            "Type",
            "",
        )
    )
    company_url = str(row["Career_URL"])

    if not company_url or company_url == "nan":
        return []

    print(
        f"\n[{idx + 1}/{total_companies}] Scanning {company}"
    )

    context = await browser.new_context()
    page = await context.new_page()

    try:
        portal, links = await collect_job_links(
            page,
            company_url,
        )

        print(
            f"{company} -> {portal}; found {len(links)} potential job links"
        )

        fresh_links = [
            link
            for link in links
            if link not in seen_links
        ]

        job_page_semaphore = asyncio.Semaphore(
            JOB_PAGE_CONCURRENCY_PER_COMPANY
        )

        async def bounded_score(link):
            async with job_page_semaphore:
                return await score_job_page(
                    context,
                    link,
                    company,
                    country,
                    job_type,
                    keywords,
                    locations,
                    min_score,
                )

        tasks = [
            bounded_score(link)
            for link in fresh_links
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        scored_jobs = []

        for result in results:
            if isinstance(result, Exception):
                print(
                    f"Failed job page for {company}: {result}"
                )
                continue

            if result:
                if result["Matched"]:
                    print(
                        f"Match: {result['Title']} | Score={result['Score']}"
                    )
                scored_jobs.append(result)

        return scored_jobs

    except Exception as e:
        print(
            f"Failed company page: {company}"
        )
        print(e)
        return []

    finally:
        await context.close()


async def run_parallel_crawl(args):
    from playwright.async_api import async_playwright

    configure_user_paths(args)

    print("Loading job database...")

    companies = pd.read_excel(
        EXCEL_FILE,
        engine="odf",
    )

    keywords = load_keywords(KEYWORDS_FILE)
    locations = load_locations(LOCATIONS_FILE)
    seen_jobs = load_seen_jobs(SEEN_FILE)
    seen_links = set(seen_jobs.keys())

    scored_jobs = []
    total_companies = len(companies)
    semaphore = asyncio.Semaphore(args.concurrency)

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
        )

        async def bounded_scan(idx, row):
            async with semaphore:
                return await scan_company(
                    browser,
                    row,
                    idx,
                    total_companies,
                    seen_links,
                    keywords,
                    locations,
                    args.min_score,
                )

        tasks = [
            bounded_scan(
                idx,
                row,
            )
            for idx, row in companies.iterrows()
        ]

        company_results = await asyncio.gather(*tasks)

        await browser.close()

    for company_jobs in company_results:
        scored_jobs.extend(company_jobs)

    matched_jobs = [
        job
        for job in scored_jobs
        if job["Matched"]
    ]

    save_results(
        matched_jobs,
        scored_jobs,
    )

    for match in matched_jobs:
        seen_jobs[match["URL"]] = {
            "title": match["Title"],
            "first_seen": str(datetime.today().date()),
            "posted_date": match.get("PostedDate", ""),
            "score": match["Score"],
            "company": match["Company"],
        }

    save_seen_jobs(
        SEEN_FILE,
        seen_jobs,
    )

    print("\nRun completed.")


def save_results(matches, scored_jobs):
    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    results = pd.DataFrame(matches)
    potential_results = pd.DataFrame(scored_jobs)
    today = str(datetime.today().date())

    excel_out = os.path.join(
        OUTPUT_DIR,
        "JobMatches.xlsx",
    )
    txt_out = os.path.join(
        OUTPUT_DIR,
        "matches.txt",
    )

    if len(potential_results) > 0:
        potential_results = potential_results.sort_values(
            ["PostedDate", "Score"],
            ascending=[False, False],
        )

        if os.path.exists(POTENTIAL_JOBS_FILE):
            with pd.ExcelWriter(
                POTENTIAL_JOBS_FILE,
                engine="openpyxl",
                mode="a",
                if_sheet_exists="replace",
            ) as writer:
                potential_results.to_excel(
                    writer,
                    sheet_name=today,
                    index=False,
                )
        else:
            with pd.ExcelWriter(
                POTENTIAL_JOBS_FILE,
                engine="openpyxl",
            ) as writer:
                potential_results.to_excel(
                    writer,
                    sheet_name=today,
                    index=False,
                )

        potential_results.to_csv(
            POTENTIAL_JOBS_TXT_FILE,
            sep="\t",
            index=False,
        )

    if len(results) == 0:
        print("\nNo new matching jobs found.")
        return

    results = results.sort_values(
        "Score",
        ascending=False,
    )

    if os.path.exists(excel_out):
        with pd.ExcelWriter(
            excel_out,
            engine="openpyxl",
            mode="a",
            if_sheet_exists="replace",
        ) as writer:
            results.to_excel(
                writer,
                sheet_name=today,
                index=False,
            )
    else:
        with pd.ExcelWriter(
            excel_out,
            engine="openpyxl",
        ) as writer:
            results.to_excel(
                writer,
                sheet_name=today,
                index=False,
            )

    results.to_csv(
        txt_out,
        sep="\t",
        index=False,
    )

    notify_completion(len(results))

    print(
        f"\nSUCCESS: {len(results)} matches found"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scan company career sites in parallel.",
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Number of company websites to scan at the same time.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=DEFAULT_MIN_SCORE,
        help="Minimum score required to save a job match.",
    )
    parser.add_argument(
        "--user",
        default="Rohin",
        help="User folder inside users/ to load preferences and save results.",
    )
    parser.add_argument(
        "--data-file",
        default=EXCEL_FILE,
        help="Shared company database file to crawl.",
    )

    return parser.parse_args()


def resolve_user_dir(user):
    requested = user.strip()
    exact_path = os.path.join(
        USERS_DIR,
        requested,
    )

    if os.path.isdir(exact_path):
        return exact_path

    if os.path.isdir(USERS_DIR):
        for existing_user in os.listdir(USERS_DIR):
            if existing_user.lower() == requested.lower():
                return os.path.join(
                    USERS_DIR,
                    existing_user,
                )

    raise FileNotFoundError(
        f"User folder not found: {exact_path}"
    )


def configure_user_paths(args):
    global EXCEL_FILE
    global KEYWORDS_FILE
    global LOCATIONS_FILE
    global SEEN_FILE
    global OUTPUT_DIR
    global POTENTIAL_JOBS_FILE
    global POTENTIAL_JOBS_TXT_FILE

    user_dir = resolve_user_dir(args.user)

    EXCEL_FILE = os.path.abspath(args.data_file)
    KEYWORDS_FILE = os.path.join(user_dir, "keywords.txt")
    LOCATIONS_FILE = os.path.join(user_dir, "locations.txt")
    SEEN_FILE = os.path.join(user_dir, "seen_jobs.json")
    OUTPUT_DIR = os.path.join(user_dir, "outputs")
    POTENTIAL_JOBS_FILE = os.path.join(OUTPUT_DIR, "PotentialJobs.xlsx")
    POTENTIAL_JOBS_TXT_FILE = os.path.join(OUTPUT_DIR, "potential_jobs.txt")

    print(f"Using user profile: {os.path.basename(user_dir)}")
    print(f"Company database: {EXCEL_FILE}")


def main():
    asyncio.run(
        run_parallel_crawl(
            parse_args()
        )
    )


if __name__ == "__main__":
    main()
