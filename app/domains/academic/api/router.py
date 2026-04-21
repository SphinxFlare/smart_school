# domains/academic/api/router.py

from fastapi import APIRouter

# -------------------------
# Infrastructure
# -------------------------
from .infrastructure.classes import router as class_router 
from .infrastructure.school import router as school_router
from .infrastructure.academic_year import router as academic_year_router
from .infrastructure.section import router as section_router
from .infrastructure.feature import router as feature_router

# -------------------------
# Curriculum
# -------------------------
from .curriculum.subject import router as subject_router
from .curriculum.assignment import router as assignment_router
from .curriculum.timetable import router as timetable_router

# -------------------------
# Assessment
# -------------------------
from .assessment.exam import router as exam_router
from .assessment.schedule import router as schedule_router
from .assessment.marks import router as marks_router
from .assessment.result import router as result_router
from .assessment.homework import router as homework_router
from .assessment.submission import router as submission_router

# -------------------------
# Attendance
# -------------------------
from .attendance.student_attendance import router as student_attendance_router
from .attendance.staff_attendance import router as staff_attendance_router


router = APIRouter(
    prefix="/academic",
    tags=["Academic"],
)

# -------------------------
# Infrastructure
# -------------------------
router.include_router(school_router)
router.include_router(academic_year_router)
router.include_router(class_router)
router.include_router(section_router)
router.include_router(feature_router)

# -------------------------
# Curriculum
# -------------------------
router.include_router(subject_router)
router.include_router(assignment_router)
router.include_router(timetable_router)

# -------------------------
# Assessment
# -------------------------
router.include_router(exam_router)
router.include_router(schedule_router)
router.include_router(marks_router)
router.include_router(result_router)
router.include_router(homework_router)
router.include_router(submission_router)

# -------------------------
# Attendance
# -------------------------
router.include_router(student_attendance_router)
router.include_router(staff_attendance_router)