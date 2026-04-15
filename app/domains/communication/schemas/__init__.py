# communication/schemas/__init__.py


from .base import DomainBase, TimestampSchema
from .notification import (
    NotificationChannel, NotificationBase, NotificationCreate, NotificationUpdate,
    NotificationResponse, NotificationFilter, NotificationStatistics,
    BulkNotificationCreate, NotificationPreferenceUpdate, NotificationDeliveryLog
)
from .announcement import (
    AnnouncementAttachment, AnnouncementBase, AnnouncementCreate, AnnouncementUpdate,
    AnnouncementResponse, AnnouncementSummary, AnnouncementAcknowledgment,
    BulkAnnouncementCreate, AnnouncementAnalytics
)
from .feed import (
    FeedItemBase, FeedItemCreate, FeedItemUpdate, FeedItemResponse,
    FeedItemSummary, UserFeedPreferences, FeedFilter, FeedAnalytics,
    FeedItemInteraction, BirthdayFeedItem
)
from .message import (
    MessageAttachment, MessageBase, MessageCreate, MessageReplyCreate,
    MessageRecipientStatus, MessageResponse, MessageWithReplies,
    MessageReplyResponse, MessageFilter, MessageStatistics
)

__all__ = [
    # Base
    "DomainBase", "TimestampSchema",
    
    # Notification
    "NotificationChannel", "NotificationBase", "NotificationCreate", "NotificationUpdate",
    "NotificationResponse", "NotificationFilter", "NotificationStatistics",
    "BulkNotificationCreate", "NotificationPreferenceUpdate", "NotificationDeliveryLog",
    
    # Announcement
    "AnnouncementAttachment", "AnnouncementBase", "AnnouncementCreate", "AnnouncementUpdate",
    "AnnouncementResponse", "AnnouncementSummary", "AnnouncementAcknowledgment",
    "BulkAnnouncementCreate", "AnnouncementAnalytics",
    
    # Feed
    "FeedItemBase", "FeedItemCreate", "FeedItemUpdate", "FeedItemResponse",
    "FeedItemSummary", "UserFeedPreferences", "FeedFilter", "FeedAnalytics",
    "FeedItemInteraction", "BirthdayFeedItem",
    
    # Message
    "MessageAttachment", "MessageBase", "MessageCreate", "MessageReplyCreate",
    "MessageRecipientStatus", "MessageResponse", "MessageWithReplies",
    "MessageReplyResponse", "MessageFilter", "MessageStatistics",
]