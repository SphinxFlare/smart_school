# communication/events/topics.py

"""
Central definition of communication domain event topics.
"""


class CommunicationTopics:
    # ---------------------------------------------------------
    # Message
    # ---------------------------------------------------------
    MESSAGE_SENT = "communication.message.sent"

    # ---------------------------------------------------------
    # Notification
    # ---------------------------------------------------------
    NOTIFICATION_DISPATCH = "communication.notification.dispatch"

    # ---------------------------------------------------------
    # Announcement
    # ---------------------------------------------------------
    ANNOUNCEMENT_PUBLISHED = "communication.announcement.published"