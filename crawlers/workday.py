import re
from urllib.parse import urljoin


def get_workday_jobs(page, url):

    jobs = []

    try:

        page.goto(
            url,
            timeout=30000
        )

        page.wait_for_load_state(
            "networkidle"
        )

        html = page.content()

        matches = re.findall(

            r'href="([^"]+job[^"]+)"',

            html,

            flags=re.IGNORECASE
        )

        for match in matches:

            jobs.append(
                urljoin(
                    url,
                    match
                )
            )

    except Exception as e:

        print(
            f"Workday crawler failed: {e}"
        )

    return sorted(
        list(set(jobs))
    )