# utils/notifications.py

from plyer import notification
import winsound


def notify_completion(num_matches):

    notification.notify(
        title="Job Hunter Finished",
        message=f"{num_matches} new jobs found",
        timeout=20
    )

    winsound.PlaySound(
        "SystemExclamation",
        winsound.SND_ALIAS
    )