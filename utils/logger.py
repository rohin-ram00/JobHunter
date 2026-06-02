from datetime import datetime
import os


LOG_FILE = "outputs/logs.txt"


def log(message):
    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    line = f"[{timestamp}] {message}"

    print(line)

    os.makedirs(
        os.path.dirname(LOG_FILE),
        exist_ok=True,
    )

    with open(
        LOG_FILE,
        "a",
        encoding="utf-8",
    ) as f:
        f.write(line + "\n")
