# crawlers/generic.py

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from utils.filters import bad_url
JOB_PATTERNS = [
    "job",
    "jobs",
    "career",
    "careers",
    "vacancy",
    "vacancies",
    "opening",
    "position"
]


def extract_job_links(
    page,
    company_url
):

    html = page.content()

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    links = []

    for a in soup.find_all(
        "a",
        href=True
    ):

        href = a["href"]

        if any(
            p in href.lower()
            for p in JOB_PATTERNS
        ):

            full_link = urljoin(
                company_url,
                href
            )
            if bad_url(full_link):
                continue
            links.append(
                full_link
            )

    return sorted(
        list(set(links))
    )