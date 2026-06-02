import json
import os


def load_seen_jobs(filepath):
    if not os.path.exists(filepath):
        os.makedirs(
            os.path.dirname(filepath),
            exist_ok=True,
        )

        with open(
            filepath,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump({}, f)

    with open(
        filepath,
        "r",
        encoding="utf-8",
    ) as f:
        return json.load(f)


def save_seen_jobs(filepath, data):
    sorted_data = dict(
        sorted(
            data.items(),
            key=lambda item: (
                item[1].get("first_seen", ""),
                item[1].get("posted_date", ""),
            ),
            reverse=True,
        )
    )

    with open(
        filepath,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            sorted_data,
            f,
            indent=4,
        )
