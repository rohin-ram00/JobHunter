# ==========================================
# TITLE FILTERS
# ==========================================

NOISE_PATTERNS = [
    "sign in",
    "signin",
    "login",
    "log in",
    "register",
    "create account",
    "privacy",
    "privacy policy",
    "cookie",
    "cookie settings",
    "terms",
    "terms of use",
    "terms and conditions",
    "legal",
    "impressum",
    "accessibility",
    "about us",
    "about",
    "contact",
    "locations",
    "location",
    "our culture",
    "diversity",
    "benefits",
    "why join",
    "career events",
    "events",
    "news",
    "press",
    "media",
    "startseite",
    "page_title",
    "careers",
    "student",
    "students",
    "graduate",
    "graduates",
    "internship",
    "intern",
    "working student",
    "praktikum",
    "praktikant",
    "werkstudent",
    "abschlussarbeit",
    "ausbildung",
    "duales studium",
    "studium",
    "instagram",
    "facebook",
    "linkedin",
    "youtube",
    "sitemap",
    "search results",
    "page not found",
    "404",
]

BAD_URL_PATTERNS = [
    "privacy",
    "cookie",
    "terms",
    "legal",
    "facebook",
    "linkedin",
    "instagram",
    "youtube",
    "news",
    "press",
    "media",
    "startseite",
    "karriere",
    "contact",
    "locations",
    "location",
    "events",
    "career-events",
    "recruiting-events",
    "faq",
    "graduates",
    "students",
    "internship",
    "internships",
    "benefits",
    "diversity",
    "why-join",
    "search?",
    "search=",
]

LOW_PRIORITY_PATTERNS = [
    "assembly",
    "production operator",
    "warehouse",
    "forklift",
    "cleaner",
    "kitchen",
    "cook",
    "sales assistant",
    "retail",
    "lager",
    "produktion",
    "fertigungsmitarbeiter",
    "gabelstapler",
]

HIGH_VALUE_PATTERNS = [
    "cfd",
    "simulation",
    "aerodynamics",
    "aeroelasticity",
    "openfoam",
    "starccm",
    "ansys",
    "fsi",
    "fluid",
    "research engineer",
    "simulation engineer",
    "development engineer",
    "aeronautical",
    "flight dynamics",
    "r&d",
    "research",
    "numerical",
    "modelling",
    "modeling",
]


def is_noise(text):
    text = text.lower()

    return any(
        pattern in text
        for pattern in NOISE_PATTERNS
    )


def bad_url(url):
    url = url.lower()

    return any(
        pattern in url
        for pattern in BAD_URL_PATTERNS
    )


def low_value_job(title):
    title = title.lower()

    return any(
        pattern in title
        for pattern in LOW_PRIORITY_PATTERNS
    )


def high_value_job(title):
    title = title.lower()

    return any(
        pattern in title
        for pattern in HIGH_VALUE_PATTERNS
    )
