def score_job(text, keywords):

    text = text.lower()

    score = 0
    matched = []

    strong_matches = 0

    for keyword, weight in keywords.items():

        if keyword.lower() in text:

            matched.append(keyword)

            score += weight

            if weight >= 20:
                strong_matches += 1

    if strong_matches >= 2:
        score += 20

    if strong_matches >= 4:
        score += 40

    return score, matched