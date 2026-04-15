# domains/types/types.py


from enum import Enum
from sqlalchemy import TypeDecorator, TEXT
import json

# ======================
# PREDEFINED ENUMS
# ======================

class FeatureKey(str, Enum):
    ATTENDANCE = "attendance"
    EXAM = "exam"
    TRANSPORT = "transport"
    FINANCE = "finance"
    HOMEWORK = "homework"
    
    
class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class StaffAttendanceStatus(str, Enum):
    PRESENT = "present"
    HALF_DAY = "half_day"
    ABSENT = "absent"
    ON_LEAVE = "on_leave"
    HOLIDAY = "holiday"
    WEEK_OFF = "week_off"

class ConcernType(str, Enum):
    STUDIES = "studies"
    BEHAVIOUR = "behaviour"
    ATTENTION = "attention"
    HEALTH = "health"
    SAFETY = "safety"
    OTHER = "other"

class ExamType(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"

class FeeType(str, Enum):
    YEARLY = "yearly"
    EXAM = "exam"
    SPECIAL = "special"
    OTHER = "other"

class TransportEventType(str, Enum):
    PICKUP_CONFIRMED = "pickup_confirmed"
    DROP_CONFIRMED = "drop_confirmed"
    DELAY_REPORTED = "delay_reported"
    SPEEDING = "speeding"
    HARSH_BRAKING = "harsh_braking"
    AGGRESSIVE_DRIVING = "aggressive_driving"

class UserRoleType(str, Enum):
    STUDENT = "student"
    PARENT = "parent"
    TEACHER = "teacher"
    DRIVER = "driver"
    ADMIN = "admin"
    COUNSELOR = "counselor"
    STAFF = "staff"  # Non-teaching staff

class PunchType(str, Enum):
    CHECK_IN = "check_in"
    CHECK_OUT = "check_out"

# ======================
# CUSTOM TYPE HANDLER
# ======================
class CustomTypeField(TypeDecorator):
    """Enables user-defined types with fallback to system enums"""
    impl = TEXT
    cache_ok = True

    def process_bind_param(self, value, dialect):
        return json.dumps(value) if isinstance(value, dict) else value

    def process_result_value(self, value, dialect):
        if value and isinstance(value, str):
            try:
                return json.loads(value)
            except:
                return {"type": value, "label": value}
        return value