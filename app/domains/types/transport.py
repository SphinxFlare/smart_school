# domains/types/transport.py


from enum import Enum


class BusStatus(str, Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    DECOMMISSIONED = "decommissioned"


class RouteStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class DriverStatus(str, Enum):
    ACTIVE = "active"
    ON_LEAVE = "on_leave"
    SUSPENDED = "suspended"


class AssignmentStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class StudentTransportStatus(str, Enum):
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    DISCONTINUED = "discontinued"


class TripType(str, Enum):
    PICKUP = "pickup"
    DROP = "drop"


class TripStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransportNotificationType(str, Enum):
    PICKUP_CONFIRMED = "pickup_confirmed"
    DROP_CONFIRMED = "drop_confirmed"
    DELAY_ALERT = "delay_alert"
    ETA_UPDATE = "eta_update"


class MaintenanceType(str, Enum):
    ROUTINE = "routine"
    REPAIR = "repair"
    INSPECTION = "inspection"
