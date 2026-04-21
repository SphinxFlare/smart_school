# communication/api/router.py

from fastapi import APIRouter

from communication.api.message import message, recipient, reply
from communication.api.broadcast import announcement, bulletin, feed
from communication.api.notification import notification, preference


router = APIRouter()

# Message
router.include_router(message.router)
router.include_router(recipient.router)
router.include_router(reply.router)

# Broadcast
router.include_router(announcement.router)
router.include_router(bulletin.router)
router.include_router(feed.router)

# Notification
router.include_router(notification.router)
router.include_router(preference.router)