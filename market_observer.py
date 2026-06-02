import argparse
import os
import re
from collections import Counter, defaultdict
from datetime import datetime

import pandas as pd


OUTPUT_DIR = "outputs"
MATCHES_FILE = os.path.join(OUTPUT_DIR, "matches.txt")
EXCEL_MATCHES_FILE = os.path.join(OUTPUT_DIR, "JobMatches.xlsx")
POTENTIAL_FILE = os.path.join(OUTPUT_DIR, "potential_jobs.txt")
EXCEL_POTENTIAL_FILE = os.path.join(OUTPUT_DIR, "PotentialJobs.xlsx")
OBS_TXT_FILE = os.path.join(OUTPUT_DIR, "market_observations.txt")
OBS_XLSX_FILE = os.path.join(OUTPUT_DIR, "MarketObservations.xlsx")

DEFAULT_MIN_SCORE = 45
DEFAULT_WATCHLIST_SCORE = 25
TOP_N = 10

SENIORITY_PATTERNS = {
    "Internship / student": [
        "intern",
        "internship",
        "working student",
        "student",
        "graduate",
        "trainee",
    ],
    "Junior": [
        "junior",
        "entry level",
        "associate",
    ],
    "Mid-level": [
        "engineer",
        "specialist",
        "consultant",
    ],
    "Senior": [
        "senior",
        "lead",
        "principal",
        "staff",
        "expert",
    ],
    "Manager / head": [
        "manager",
        "head of",
        "director",
    ],
}


def normalize_roles(roles):
    if roles.empty:
        return roles

    for column in [
        "Date",
        "CrawlDate",
        "PostedDate",
        "Company",
        "Country",
        "Type",
        "Title",
        "Keywords",
        "Locations",
        "URL",
        "Matched",
        "Decision",
        "Source",
    ]:
        if column not in roles.columns:
            roles[column] = ""

        roles[column] = roles[column].fillna("").astype(str)

    if "Score" in roles.columns:
        roles["Score"] = pd.to_numeric(
            roles["Score"],
            errors="coerce",
        ).fillna(0)
    else:
        roles["Score"] = 0

    roles["PostedDateParsed"] = pd.to_datetime(
        roles["PostedDate"],
        errors="coerce",
    )
    roles["CrawlDateParsed"] = pd.to_datetime(
        roles["CrawlDate"].where(
            roles["CrawlDate"] != "",
            roles["Date"],
        ),
        errors="coerce",
    )
    roles["SortDate"] = roles["PostedDateParsed"].fillna(
        roles["CrawlDateParsed"]
    )

    roles["Matched"] = roles["Matched"].replace(
        {
            "True": True,
            "False": False,
            "true": True,
            "false": False,
            "": False,
        }
    )

    return roles


def load_role_exports():
    frames = []

    if os.path.exists(EXCEL_MATCHES_FILE):
        sheets = pd.read_excel(
            EXCEL_MATCHES_FILE,
            sheet_name=None,
            engine="openpyxl",
        )

        for sheet_name, sheet in sheets.items():
            sheet = sheet.copy()
            sheet["Source"] = f"{os.path.basename(EXCEL_MATCHES_FILE)}:{sheet_name}"
            sheet["Matched"] = True
            frames.append(sheet)

    if os.path.exists(MATCHES_FILE) and os.path.getsize(MATCHES_FILE) > 0:
        txt_matches = pd.read_csv(
            MATCHES_FILE,
            sep="\t",
        )
        txt_matches["Source"] = os.path.basename(MATCHES_FILE)
        txt_matches["Matched"] = True
        frames.append(txt_matches)

    if os.path.exists(EXCEL_POTENTIAL_FILE):
        sheets = pd.read_excel(
            EXCEL_POTENTIAL_FILE,
            sheet_name=None,
            engine="openpyxl",
        )

        for sheet_name, sheet in sheets.items():
            sheet = sheet.copy()
            sheet["Source"] = f"{os.path.basename(EXCEL_POTENTIAL_FILE)}:{sheet_name}"
            frames.append(sheet)

    if os.path.exists(POTENTIAL_FILE) and os.path.getsize(POTENTIAL_FILE) > 0:
        txt_potential = pd.read_csv(
            POTENTIAL_FILE,
            sep="\t",
        )
        txt_potential["Source"] = os.path.basename(POTENTIAL_FILE)
        frames.append(txt_potential)

    if not frames:
        return pd.DataFrame()

    roles = pd.concat(
        frames,
        ignore_index=True,
    )

    roles = roles.drop_duplicates(
        subset=["URL"],
        keep="last",
    )

    return normalize_roles(roles)


def split_terms(value):
    return [
        term.strip()
        for term in str(value).split(",")
        if term.strip()
    ]


def detect_seniority(title):
    title = title.lower()

    for seniority, patterns in SENIORITY_PATTERNS.items():
        if any(pattern in title for pattern in patterns):
            return seniority

    return "Unclear"


def count_terms(series):
    counter = Counter()

    for value in series:
        counter.update(split_terms(value))

    return counter


def make_table(counter, value_name):
    rows = [
        {
            value_name: key,
            "Count": count,
        }
        for key, count in counter.most_common()
    ]

    return pd.DataFrame(rows)


def make_observations(matches, min_score):
    relevant = matches[
        matches["Score"] >= min_score
    ].copy()

    if relevant.empty:
        return relevant, pd.DataFrame()

    relevant["Seniority"] = relevant["Title"].apply(detect_seniority)

    keyword_counts = count_terms(relevant["Keywords"])
    location_counts = count_terms(relevant["Locations"])
    country_counts = Counter(relevant["Country"])
    type_counts = Counter(relevant["Type"])
    seniority_counts = Counter(relevant["Seniority"])
    company_counts = Counter(relevant["Company"])

    keyword_scores = defaultdict(float)
    company_scores = defaultdict(float)
    location_scores = defaultdict(float)

    for _, row in relevant.iterrows():
        for keyword in split_terms(row["Keywords"]):
            keyword_scores[keyword] += row["Score"]

        for location in split_terms(row["Locations"]):
            location_scores[location] += row["Score"]

        company_scores[row["Company"]] += row["Score"]

    observations = []

    def add_observation(category, signal, count, evidence, priority):
        observations.append(
            {
                "Category": category,
                "Signal": signal,
                "Count": count,
                "Priority": round(priority, 2),
                "Evidence": evidence,
            }
        )

    for keyword, count in keyword_counts.most_common(TOP_N):
        add_observation(
            "Skill demand",
            keyword,
            count,
            f"Appears in {count} relevant roles",
            keyword_scores[keyword],
        )

    for location, count in location_counts.most_common(TOP_N):
        add_observation(
            "Location demand",
            location,
            count,
            f"Appears in {count} relevant roles",
            location_scores[location],
        )

    for company, count in company_counts.most_common(TOP_N):
        add_observation(
            "Active company",
            company,
            count,
            f"{count} relevant roles found",
            company_scores[company],
        )

    for seniority, count in seniority_counts.most_common():
        add_observation(
            "Seniority signal",
            seniority,
            count,
            f"{count} matching job titles",
            count,
        )

    for country, count in country_counts.most_common(TOP_N):
        add_observation(
            "Country signal",
            country,
            count,
            f"{count} relevant roles found",
            count,
        )

    for job_type, count in type_counts.most_common(TOP_N):
        if job_type:
            add_observation(
                "Company type signal",
                job_type,
                count,
                f"{count} relevant roles found",
                count,
            )

    observations_df = pd.DataFrame(observations)

    observations_df = observations_df.sort_values(
        ["Priority", "Count"],
        ascending=False,
    )

    return relevant, observations_df


def make_highlights(roles, relevant, min_score, watchlist_score):
    highest_ranked = roles.sort_values(
        "Score",
        ascending=False,
    ).head(10)

    latest_postings = roles[
        roles["PostedDateParsed"].notna()
    ].sort_values(
        ["PostedDateParsed", "Score"],
        ascending=[False, False],
    ).head(25)

    recent_postings = roles.sort_values(
        ["SortDate", "Score"],
        ascending=[False, False],
    )

    near_misses = roles[
        (roles["Score"] >= watchlist_score)
        & (roles["Score"] < min_score)
        & (roles["Decision"] != "Skipped noise")
    ].sort_values(
        ["Score", "SortDate"],
        ascending=[False, False],
    )

    rows = []

    if not highest_ranked.empty:
        row = highest_ranked.iloc[0]
        rows.append(
            {
                "Highlight": "Highest ranked job",
                "Title": row["Title"],
                "Company": row["Company"],
                "Score": row["Score"],
                "PostedDate": row["PostedDate"],
                "URL": row["URL"],
            }
        )

    if not latest_postings.empty:
        row = latest_postings.iloc[0]
        rows.append(
            {
                "Highlight": "Latest job posting",
                "Title": row["Title"],
                "Company": row["Company"],
                "Score": row["Score"],
                "PostedDate": row["PostedDate"],
                "URL": row["URL"],
            }
        )

    return (
        pd.DataFrame(rows),
        highest_ranked,
        latest_postings,
        recent_postings,
        near_misses,
    )


def public_columns(dataframe):
    columns = [
        "PostedDate",
        "CrawlDate",
        "Date",
        "Company",
        "Country",
        "Type",
        "Title",
        "Score",
        "Matched",
        "Decision",
        "Keywords",
        "Locations",
        "URL",
        "Source",
    ]

    return dataframe[
        [
            column
            for column in columns
            if column in dataframe.columns
        ]
    ]


def write_text_report(
    roles,
    relevant,
    observations,
    highlights,
    highest_ranked,
    latest_postings,
    near_misses,
    min_score,
):
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines = [
        "Market Observations",
        f"Generated: {generated_at}",
        f"Minimum score: {min_score}",
        "",
        f"Total saved roles: {len(roles)}",
        f"Relevant roles: {len(relevant)}",
        f"Near misses: {len(near_misses)}",
        "",
    ]

    if not highlights.empty:
        lines.append("Highlights:")

        for _, row in highlights.iterrows():
            lines.append(
                "- "
                f"{row['Highlight']}: {row['Title']} "
                f"at {row['Company']} "
                f"(score={row['Score']}, posted={row['PostedDate'] or 'unknown'})"
            )

        lines.append("")

    if roles.empty:
        lines.append("No relevant roles found at the selected threshold.")
    else:
        lines.append("Top observations:")

        for _, row in observations.head(25).iterrows():
            lines.append(
                "- "
                f"{row['Category']}: {row['Signal']} "
                f"(count={row['Count']}, priority={row['Priority']}) - "
                f"{row['Evidence']}"
            )

        lines.extend(
            [
                "",
                "Highest scoring roles:",
            ]
        )

        for _, row in relevant.sort_values(
            "Score",
            ascending=False,
        ).head(15).iterrows():
            clean_title = re.sub(
                r"\s+",
                " ",
                row["Title"],
            ).strip()

            lines.append(
                "- "
                f"{row['Score']}: {clean_title} "
                f"at {row['Company']} "
                f"({row['Country']})"
            )

        if not latest_postings.empty:
            lines.extend(
                [
                    "",
                    "Latest known postings:",
                ]
            )

            for _, row in latest_postings.head(10).iterrows():
                clean_title = re.sub(
                    r"\s+",
                    " ",
                    row["Title"],
                ).strip()

                lines.append(
                    "- "
                    f"{row['PostedDate']}: {clean_title} "
                    f"at {row['Company']} "
                    f"(score={row['Score']})"
                )

    os.makedirs(
        OUTPUT_DIR,
        exist_ok=True,
    )

    with open(
        OBS_TXT_FILE,
        "w",
        encoding="utf-8",
    ) as f:
        f.write(
            "\n".join(lines)
        )


def write_excel_report(
    relevant,
    observations,
    highlights,
    highest_ranked,
    latest_postings,
    recent_postings,
    near_misses,
):
    with pd.ExcelWriter(
        OBS_XLSX_FILE,
        engine="openpyxl",
    ) as writer:
        highlights.to_excel(
            writer,
            sheet_name="Highlights",
            index=False,
        )

        public_columns(recent_postings).to_excel(
            writer,
            sheet_name="Recent Postings",
            index=False,
        )

        public_columns(highest_ranked).to_excel(
            writer,
            sheet_name="Highest Ranked",
            index=False,
        )

        public_columns(latest_postings).to_excel(
            writer,
            sheet_name="Latest Postings",
            index=False,
        )

        public_columns(near_misses).to_excel(
            writer,
            sheet_name="Near Misses",
            index=False,
        )

        observations.to_excel(
            writer,
            sheet_name="Observations",
            index=False,
        )

        public_columns(
            relevant.sort_values(
                "Score",
                ascending=False,
            )
        ).to_excel(
            writer,
            sheet_name="Relevant Roles",
            index=False,
        )

        make_table(
            count_terms(relevant["Keywords"]),
            "Keyword",
        ).to_excel(
            writer,
            sheet_name="Keyword Counts",
            index=False,
        )

        make_table(
            count_terms(relevant["Locations"]),
            "Location",
        ).to_excel(
            writer,
            sheet_name="Location Counts",
            index=False,
        )


def main():
    parser = argparse.ArgumentParser(
        description="Extract market observations from saved job matches.",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=DEFAULT_MIN_SCORE,
        help="Only roles at or above this score are included.",
    )
    parser.add_argument(
        "--watchlist-score",
        type=int,
        default=DEFAULT_WATCHLIST_SCORE,
        help="Below-threshold roles at or above this score go into Near Misses.",
    )

    args = parser.parse_args()

    roles = load_role_exports()

    if roles.empty:
        print(
            "No saved role exports found. Run ParallelCrawler.py first."
        )
        return

    relevant, observations = make_observations(
        roles,
        args.min_score,
    )
    (
        highlights,
        highest_ranked,
        latest_postings,
        recent_postings,
        near_misses,
    ) = make_highlights(
        roles,
        relevant,
        args.min_score,
        args.watchlist_score,
    )

    write_text_report(
        roles,
        relevant,
        observations,
        highlights,
        highest_ranked,
        latest_postings,
        near_misses,
        args.min_score,
    )

    write_excel_report(
        relevant,
        observations,
        highlights,
        highest_ranked,
        latest_postings,
        recent_postings,
        near_misses,
    )

    print(
        f"Market observations saved to {OBS_TXT_FILE} "
        f"and {OBS_XLSX_FILE}"
    )


if __name__ == "__main__":
    main()
