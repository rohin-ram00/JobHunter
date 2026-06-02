# crawlers/detector.py

def detect_portal(url):

    url = url.lower()

    if "workday" in url:
        return "workday"

    if "successfactors" in url:
        return "successfactors"

    if "greenhouse" in url:
        return "greenhouse"

    if "smartrecruiters" in url:
        return "smartrecruiters"

    return "generic"