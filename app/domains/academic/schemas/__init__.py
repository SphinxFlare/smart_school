# academic/schemas/__init__.py


# Academic domain public schema interface
from .base import DomainBase, TimestampSchema
from .attendance import (
    AttendanceBase, StudentAttendanceCreate, StudentAttendanceUpdate,
    StudentAttendanceResponse, AttendanceSummary, AttendanceHistoryResponse,
    BulkAttendanceCreate, AttendanceFilter, MonthlyAttendanceReport,
    AttendanceAlert, AttendanceExportFormat
)
from .subject import (
    SubjectBase, SubjectCreate, SubjectUpdate, SubjectResponse, SubjectReference,
    SubjectTeachingAssignment
)
from .timetable import (
    ClassTimetableBase, ClassTimetableCreate, ClassTimetableUpdate,
    ClassTimetableResponse, TimetablePeriod, DailyScheduleResponse
)
from .exam import (
    ExamBase, ExamCreate, ExamUpdate, ExamResponse,
    ExamScheduleBase, ExamScheduleCreate, ExamScheduleUpdate, ExamScheduleResponse,
    ExamResultSummary
)
from .homework import (
    Attachment, SubmissionAttachment,
    HomeworkBase, HomeworkCreate, HomeworkUpdate, HomeworkResponse,
    HomeworkSubmissionBase, HomeworkSubmissionCreate, HomeworkSubmissionUpdate,
    HomeworkSubmissionResponse, HomeworkWithSubmissions, StudentHomeworkSummary
)

__all__ = [
    # Base schemas
    "DomainBase", "TimestampSchema",
    
    # Attendance
    "AttendanceBase", "StudentAttendanceCreate", "StudentAttendanceUpdate",
    "StudentAttendanceResponse", "AttendanceSummary", "AttendanceHistoryResponse",
    "BulkAttendanceCreate", "AttendanceFilter", "MonthlyAttendanceReport",
    "AttendanceAlert", "AttendanceExportFormat",
    
    # Subject
    "SubjectBase", "SubjectCreate", "SubjectUpdate", "SubjectResponse",
    "SubjectReference", "SubjectTeachingAssignment",
    
    # Timetable
    "ClassTimetableBase", "ClassTimetableCreate", "ClassTimetableUpdate",
    "ClassTimetableResponse", "TimetablePeriod", "DailyScheduleResponse",
    
    # Exam
    "ExamBase", "ExamCreate", "ExamUpdate", "ExamResponse",
    "ExamScheduleBase", "ExamScheduleCreate", "ExamScheduleUpdate", "ExamScheduleResponse",
    "ExamResultSummary",
    
    # Homework
    "Attachment", "SubmissionAttachment",
    "HomeworkBase", "HomeworkCreate", "HomeworkUpdate", "HomeworkResponse",
    "HomeworkSubmissionBase", "HomeworkSubmissionCreate", "HomeworkSubmissionUpdate",
    "HomeworkSubmissionResponse", "HomeworkWithSubmissions", "StudentHomeworkSummary",
]