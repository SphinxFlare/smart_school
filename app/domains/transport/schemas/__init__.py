# transport/schemas/__init__.py


from .base import DomainBase, TimestampSchema
from .bus import (
    BusBase, BusCreate, BusUpdate, BusResponse, BusReference,
    BusMaintenanceBase, BusMaintenanceCreate, BusMaintenanceResponse
)
from .route import (
    RouteBase, RouteCreate, RouteUpdate, RouteResponse, RouteReference,
    RouteStopBase, RouteStopCreate, RouteStopUpdate, RouteStopResponse,
    RouteOptimizationRequest
)
from .driver import (
    DriverBase, DriverCreate, DriverUpdate, DriverResponse, DriverReference,
    DriverPerformanceMetrics, DriverAssignmentSummary
)
from .trip import (
    BusAssignmentBase, BusAssignmentCreate, BusAssignmentUpdate, BusAssignmentResponse,
    TransportTripBase, TransportTripCreate, TransportTripUpdate, TransportTripResponse,
    TransportTripSummary, StudentTripStatus, TripAnalytics, TripCancellationRequest
)
from .event import (
    TransportEventBase, TransportEventCreate, TransportEventResponse,
    LiveLocationUpdate, ETACalculationRequest, ETAResponse
)
from .notification import (
    TransportNotificationBase, TransportNotificationCreate, TransportNotificationUpdate,
    TransportNotificationResponse, NotificationPreferences, NotificationStatistics
)

__all__ = [
    # Base
    "DomainBase", "TimestampSchema",
    
    # Bus
    "BusBase", "BusCreate", "BusUpdate", "BusResponse", "BusReference",
    "BusMaintenanceBase", "BusMaintenanceCreate", "BusMaintenanceResponse",
    
    # Route
    "RouteBase", "RouteCreate", "RouteUpdate", "RouteResponse", "RouteReference",
    "RouteStopBase", "RouteStopCreate", "RouteStopUpdate", "RouteStopResponse",
    "RouteOptimizationRequest",
    
    # Driver
    "DriverBase", "DriverCreate", "DriverUpdate", "DriverResponse", "DriverReference",
    "DriverPerformanceMetrics", "DriverAssignmentSummary",
    
    # Trip
    "BusAssignmentBase", "BusAssignmentCreate", "BusAssignmentUpdate", "BusAssignmentResponse",
    "TransportTripBase", "TransportTripCreate", "TransportTripUpdate", "TransportTripResponse",
    "TransportTripSummary", "StudentTripStatus", "TripAnalytics", "TripCancellationRequest",
    
    # Event
    "TransportEventBase", "TransportEventCreate", "TransportEventResponse",
    "LiveLocationUpdate", "ETACalculationRequest", "ETAResponse",
    
    # Notification
    "TransportNotificationBase", "TransportNotificationCreate", "TransportNotificationUpdate",
    "TransportNotificationResponse", "NotificationPreferences", "NotificationStatistics",
]