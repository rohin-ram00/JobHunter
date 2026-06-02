try:
    from plyer import notification
except ModuleNotFoundError:
    notification = None

try:
    import winsound
except ModuleNotFoundError:
    winsound = None


def notify_completion(num_matches):
    if notification is not None:
        notification.notify(
            title="Job Hunter Finished",
            message=f"{num_matches} new jobs found",
            timeout=20,
        )

    if winsound is not None:
        winsound.PlaySound(
            "SystemExclamation",
            winsound.SND_ALIAS,
        )
