# ==========================================
# TITLE FILTERS
# ==========================================

NOISE_PATTERNS = [

    # Authentication
    "sign in",
    "signin",
    "login",
    "log in",
    "register",
    "create account",

    # Legal
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

    # Company pages
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
    "Startseite",
    "page_title",
    "Careers",

    # Student / graduate noise
    "student",
    "students",
    "graduate",
    "graduates",
    "internship",
    "intern",
    "working student",

    # German student noise
    "praktikum",
    "praktikant",
    "werkstudent",
    "abschlussarbeit",
    "ausbildung",
    "duales studium",
    "studium",

    # Social
    "instagram",
    "facebook",
    "linkedin",
    "youtube",

    # Generic garbage
    "sitemap",
    "search results",
    "page not found",
    "404",
]

# ==========================================
# URL FILTERS
# ==========================================

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
    "Startseite",
    "Karriere",
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

# ==========================================
# LOW VALUE JOBS
# ==========================================

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

    # German
    "lager",
    "produktion",
    "fertigungsmitarbeiter",
    "gabelstapler",
]

# ==========================================
# HIGH VALUE JOBS
# ==========================================

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

# ==========================================
# FUNCTIONS
# ==========================================

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


def is_noise(title):

    title = title.lower()

    return any(
        pattern in title
        for pattern in NOISE_PATTERNS
    )
