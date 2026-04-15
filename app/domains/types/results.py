# types/results.py


from enum import Enum


class ResultStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WITHHELD = "withheld"


class GradeLetter(str, Enum):
    A_PLUS = "A+"
    A = "A"
    B_PLUS = "B+"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class RankType(str, Enum):
    CLASS = "class"
    SECTION = "section"


class SubmissionStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    LATE = "late"
    GRADED = "graded"
    MISSING = "missing"