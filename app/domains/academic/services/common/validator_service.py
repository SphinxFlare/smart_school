# academic/services/common/validator_service.py

from datetime import datetime
from typing import Optional


class ValidationError(Exception):
    pass


class ValidatorService:

    def validate_date_range(self, start_date: datetime, end_date: datetime, *, allow_equal: bool = True):
        if not start_date or not end_date:
            raise ValidationError("Start date and end date are required")

        if allow_equal:
            if start_date > end_date:
                raise ValidationError("Start date cannot be after end date")
        else:
            if start_date >= end_date:
                raise ValidationError("Start date must be before end date")

    def validate_not_past(self, date: datetime, *, reference: Optional[datetime] = None):
        ref = reference or datetime.utcnow()
        if date < ref:
            raise ValidationError("Date cannot be in the past")

    def validate_positive(self, value: float, field_name: str = "value", *, allow_zero: bool = False):
        if value is None:
            raise ValidationError(f"{field_name} is required")

        if allow_zero:
            if value < 0:
                raise ValidationError(f"{field_name} cannot be negative")
        else:
            if value <= 0:
                raise ValidationError(f"{field_name} must be greater than zero")

    def validate_range(self, value: float, min_value: float, max_value: float, field_name: str = "value"):
        if value < min_value or value > max_value:
            raise ValidationError(f"{field_name} must be between {min_value} and {max_value}")

    def validate_required_string(self, value: str, field_name: str = "field"):
        if not value or not value.strip():
            raise ValidationError(f"{field_name} is required")

    def validate_length(self, value: str, field_name: str, *, min_length: int = 0, max_length: Optional[int] = None):
        if value is None:
            return

        length = len(value)

        if length < min_length:
            raise ValidationError(f"{field_name} must be at least {min_length} characters")

        if max_length is not None and length > max_length:
            raise ValidationError(f"{field_name} must be at most {max_length} characters")

    def validate_required(self, value, field_name: str = "field"):
        if value is None:
            raise ValidationError(f"{field_name} is required")

    def validate_enum(self, value, enum_class, field_name: str = "field"):
        if value not in enum_class:
            raise ValidationError(f"Invalid {field_name}")