# welfare/repositories/aggregate/welfare_aggregate_repository.py


from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID
from datetime import datetime, date

from sqlalchemy.orm import Session, aliased
from sqlalchemy import select, func, and_, or_, case

from welfare.models.wellness import StudentObservation, WellnessCheck
from welfare.models.meetings import (
    Meeting, MeetingParticipant, MeetingAgenda, MeetingOutcome, MeetingAttendance
)
from welfare.models.complaints import (
    Concern, ConcernAssignment, ConcernComment, ConcernHistory, Escalation
)


class WelfareAggregateRepository:
    """
    Read-only aggregation repository for welfare domain.
    Does NOT extend any base repository - queries models directly.
    Provides cross-table, tenant-safe read queries for dashboards, reports, timelines.
    NO business logic, NO writes, NO updates, NO deletes, NO locking.
    All queries enforce school_id at top level when root entity contains it.
    Child tables without school_id are scoped through parent table joins.
    Does NOT call other repositories internally - operates directly on models.
    """

    def __init__(self):
        pass

    # =========================================
    # Dashboard Summaries
    # =========================================

    def get_welfare_dashboard_summary(
        self,
        db: Session,
        school_id: UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive welfare dashboard summary for a school.
        Includes counts for concerns, meetings, wellness checks, observations.
        All counts are null-safe and tenant-scoped.
        """
        # -------------------------------------
        # Concern Counts
        # -------------------------------------
        concern_counts = self._get_concern_counts(db, school_id)
        
        # -------------------------------------
        # Meeting Counts
        # -------------------------------------
        meeting_counts = self._get_meeting_counts(db, school_id)
        
        # -------------------------------------
        # Wellness Check Counts
        # -------------------------------------
        wellness_counts = self._get_wellness_counts(db, school_id)
        
        # -------------------------------------
        # Observation Counts
        # -------------------------------------
        observation_counts = self._get_observation_counts(db, school_id)

        return {
            'concerns': concern_counts,
            'meetings': meeting_counts,
            'wellness_checks': wellness_counts,
            'observations': observation_counts
        }

    def _get_concern_counts(
        self,
        db: Session,
        school_id: UUID
    ) -> Dict[str, Any]:
        """
        Get concern-related counts for dashboard.
        Tenant-scoped with soft-delete filtering.
        """
        # Total concerns (excluding deleted)
        total_stmt = (
            select(func.count(Concern.id))
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False)
            )
        )
        total = db.execute(total_stmt).scalar() or 0

        # Counts by status
        status_stmt = (
            select(Concern.status, func.count(Concern.id))
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False)
            )
            .group_by(Concern.status)
        )
        status_result = db.execute(status_stmt)
        by_status = {row[0]: row[1] for row in status_result}

        # Counts by severity
        severity_stmt = (
            select(Concern.severity, func.count(Concern.id))
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False)
            )
            .group_by(Concern.severity)
        )
        severity_result = db.execute(severity_stmt)
        by_severity = {row[0]: row[1] for row in severity_result}

        # Pending assignments
        pending_assignment_stmt = (
            select(func.count(ConcernAssignment.id))
            .join(Concern, ConcernAssignment.concern_id == Concern.id)
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
                ConcernAssignment.status == 'pending'
            )
        )
        pending_assignments = db.execute(pending_assignment_stmt).scalar() or 0

        # Pending escalations
        pending_escalation_stmt = (
            select(func.count(Escalation.id))
            .join(Concern, Escalation.concern_id == Concern.id)
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
                Escalation.status == 'pending'
            )
        )
        pending_escalations = db.execute(pending_escalation_stmt).scalar() or 0

        return {
            'total': total,
            'by_status': dict(by_status),
            'by_severity': dict(by_severity),
            'pending_assignments': pending_assignments,
            'pending_escalations': pending_escalations
        }

    def _get_meeting_counts(
        self,
        db: Session,
        school_id: UUID
    ) -> Dict[str, Any]:
        """
        Get meeting-related counts for dashboard.
        Tenant-scoped with soft-delete filtering.
        """
        # Total meetings (excluding deleted)
        total_stmt = (
            select(func.count(Meeting.id))
            .where(
                Meeting.school_id == school_id,
                Meeting.is_deleted.is_(False)
            )
        )
        total = db.execute(total_stmt).scalar() or 0

        # Counts by status
        status_stmt = (
            select(Meeting.status, func.count(Meeting.id))
            .where(
                Meeting.school_id == school_id,
                Meeting.is_deleted.is_(False)
            )
            .group_by(Meeting.status)
        )
        status_result = db.execute(status_stmt)
        by_status = {row[0]: row[1] for row in status_result}

        # Counts by meeting type
        type_stmt = (
            select(Meeting.meeting_type, func.count(Meeting.id))
            .where(
                Meeting.school_id == school_id,
                Meeting.is_deleted.is_(False)
            )
            .group_by(Meeting.meeting_type)
        )
        type_result = db.execute(type_stmt)
        by_type = {row[0]: row[1] for row in type_result}

        # Upcoming meetings
        now = datetime.utcnow()
        upcoming_stmt = (
            select(func.count(Meeting.id))
            .where(
                Meeting.school_id == school_id,
                Meeting.is_deleted.is_(False),
                Meeting.scheduled_at >= now,
                Meeting.status.in_(['scheduled', 'confirmed'])
            )
        )
        upcoming = db.execute(upcoming_stmt).scalar() or 0

        return {
            'total': total,
            'by_status': dict(by_status),
            'by_type': dict(by_type),
            'upcoming': upcoming
        }

    def _get_wellness_counts(
        self,
        db: Session,
        school_id: UUID
    ) -> Dict[str, Any]:
        """
        Get wellness check-related counts for dashboard.
        Note: WellnessCheck does not have school_id - scoped through student join.
        """
        # Import Student model for join
        from identity.models.profiles import Student
        
        # Total wellness checks (excluding deleted)
        total_stmt = (
            select(func.count(WellnessCheck.id))
            .join(Student, WellnessCheck.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                WellnessCheck.is_deleted.is_(False)
            )
        )
        total = db.execute(total_stmt).scalar() or 0

        # Requiring follow-up
        follow_up_stmt = (
            select(func.count(WellnessCheck.id))
            .join(Student, WellnessCheck.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                WellnessCheck.is_deleted.is_(False),
                WellnessCheck.follow_up_required.is_(True)
            )
        )
        requiring_follow_up = db.execute(follow_up_stmt).scalar() or 0

        # Upcoming follow-ups
        now = datetime.utcnow()
        upcoming_follow_up_stmt = (
            select(func.count(WellnessCheck.id))
            .join(Student, WellnessCheck.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                WellnessCheck.is_deleted.is_(False),
                WellnessCheck.follow_up_required.is_(True),
                WellnessCheck.follow_up_date >= now,
                WellnessCheck.follow_up_date.is_not(None)
            )
        )
        upcoming_follow_ups = db.execute(upcoming_follow_up_stmt).scalar() or 0

        return {
            'total': total,
            'requiring_follow_up': requiring_follow_up,
            'upcoming_follow_ups': upcoming_follow_ups
        }

    def _get_observation_counts(
        self,
        db: Session,
        school_id: UUID
    ) -> Dict[str, Any]:
        """
        Get observation-related counts for dashboard.
        Note: StudentObservation does not have school_id - scoped through student/class join.
        """
        # Import Student model for join
        from identity.models.profiles import Student
        
        # Total observations (excluding deleted)
        total_stmt = (
            select(func.count(StudentObservation.id))
            .join(Student, StudentObservation.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                StudentObservation.is_deleted.is_(False)
            )
        )
        total = db.execute(total_stmt).scalar() or 0

        # Counts by category
        category_stmt = (
            select(StudentObservation.category, func.count(StudentObservation.id))
            .join(Student, StudentObservation.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                StudentObservation.is_deleted.is_(False)
            )
            .group_by(StudentObservation.category)
        )
        category_result = db.execute(category_stmt)
        by_category = {row[0]: row[1] for row in category_result}

        # Counts by severity
        severity_stmt = (
            select(StudentObservation.severity, func.count(StudentObservation.id))
            .join(Student, StudentObservation.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                StudentObservation.is_deleted.is_(False),
                StudentObservation.severity.is_not(None)
            )
            .group_by(StudentObservation.severity)
        )
        severity_result = db.execute(severity_stmt)
        by_severity = {row[0]: row[1] for row in severity_result}

        # Shared with parents
        shared_stmt = (
            select(func.count(StudentObservation.id))
            .join(Student, StudentObservation.student_id == Student.id)
            .where(
                Student.school_id == school_id,
                StudentObservation.is_deleted.is_(False),
                StudentObservation.shared_with_parents.is_(True)
            )
        )
        shared_with_parents = db.execute(shared_stmt).scalar() or 0

        return {
            'total': total,
            'by_category': dict(by_category),
            'by_severity': dict(by_severity),
            'shared_with_parents': shared_with_parents
        }

    # =========================================
    # Student Welfare Timeline
    # =========================================

    def get_student_welfare_timeline(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get combined welfare timeline for a student.

        Includes concerns, wellness checks, observations, and meetings.

        Tenant safety:
        - Concern scoped by school_id
        - WellnessCheck scoped through Student join
        - StudentObservation scoped through Student join
        - Meeting scoped by school_id

        Read-only aggregation.
        Deterministic ordering by event_date DESC.
        """

        from identity.models.profiles import Student

        timeline = []

        # -----------------------------
        # Concerns
        # -----------------------------
        stmt = (
            select(
                Concern.id,
                Concern.reported_at.label("event_date"),
                func.literal("concern").label("event_type"),
                Concern.title,
                Concern.status,
                Concern.severity,
            )
            .where(
                Concern.student_id == student_id,
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
            )
        )

        if start_date:
            stmt = stmt.where(Concern.reported_at >= start_date)

        if end_date:
            stmt = stmt.where(Concern.reported_at <= end_date)

        for r in db.execute(stmt):
            timeline.append(dict(r._mapping))


        # -----------------------------
        # Wellness checks
        # -----------------------------
        stmt = (
            select(
                WellnessCheck.id,
                WellnessCheck.check_date.label("event_date"),
                func.literal("wellness_check").label("event_type"),
                func.literal("Wellness Check").label("title"),
                func.literal(None).label("status"),
                func.literal(None).label("severity"),
            )
            .join(Student, WellnessCheck.student_id == Student.id)
            .where(
                WellnessCheck.student_id == student_id,
                WellnessCheck.is_deleted.is_(False),
                Student.school_id == school_id,
            )
        )

        if start_date:
            stmt = stmt.where(WellnessCheck.check_date >= start_date)

        if end_date:
            stmt = stmt.where(WellnessCheck.check_date <= end_date)

        for r in db.execute(stmt):
            timeline.append(dict(r._mapping))


        # -----------------------------
        # Observations
        # -----------------------------
        stmt = (
            select(
                StudentObservation.id,
                StudentObservation.observation_date.label("event_date"),
                func.literal("observation").label("event_type"),
                StudentObservation.description.label("title"),
                func.literal(None).label("status"),
                StudentObservation.severity,
            )
            .join(Student, StudentObservation.student_id == Student.id)
            .where(
                StudentObservation.student_id == student_id,
                StudentObservation.is_deleted.is_(False),
                Student.school_id == school_id,
            )
        )

        if start_date:
            stmt = stmt.where(StudentObservation.observation_date >= start_date)

        if end_date:
            stmt = stmt.where(StudentObservation.observation_date <= end_date)

        for r in db.execute(stmt):
            timeline.append(dict(r._mapping))


        # -----------------------------
        # Meetings
        # -----------------------------
        stmt = (
            select(
                Meeting.id,
                Meeting.scheduled_at.label("event_date"),
                func.literal("meeting").label("event_type"),
                Meeting.title,
                Meeting.status,
                func.literal(None).label("severity"),
            )
            .join(MeetingParticipant, Meeting.id == MeetingParticipant.meeting_id)
            .where(
                Meeting.school_id == school_id,
                Meeting.is_deleted.is_(False),
                MeetingParticipant.user_id == student_id,
            )
        )

        if start_date:
            stmt = stmt.where(Meeting.scheduled_at >= start_date)

        if end_date:
            stmt = stmt.where(Meeting.scheduled_at <= end_date)

        for r in db.execute(stmt):
            timeline.append(dict(r._mapping))


        timeline.sort(key=lambda x: x["event_date"], reverse=True)

        return timeline[skip: skip + limit]

    # =========================================
    # Concern Detail with Relations
    # =========================================

    def get_concern_with_relations(
        self,
        db: Session,
        school_id: UUID,
        concern_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get concern with all related data (assignments, comments, escalations, history).
        Tenant-scoped with soft-delete filtering.
        Returns unified concern detail view.
        """
        # -------------------------------------
        # Get Concern
        # -------------------------------------
        concern_stmt = (
            select(Concern)
            .where(
                Concern.id == concern_id,
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False)
            )
        )
        concern = db.execute(concern_stmt).scalar_one_or_none()
        
        if not concern:
            return None

        # -------------------------------------
        # Get Assignments
        # -------------------------------------
        assignment_stmt = (
            select(ConcernAssignment)
            .where(ConcernAssignment.concern_id == concern_id)
            .order_by(ConcernAssignment.assigned_at.desc())
        )
        assignments = db.execute(assignment_stmt).scalars().all()

        # -------------------------------------
        # Get Comments (excluding deleted)
        # -------------------------------------
        comment_stmt = (
            select(ConcernComment)
            .where(
                ConcernComment.concern_id == concern_id,
                ConcernComment.is_deleted.is_(False)
            )
            .order_by(ConcernComment.created_at.asc())
        )
        comments = db.execute(comment_stmt).scalars().all()

        # -------------------------------------
        # Get Escalations
        # -------------------------------------
        escalation_stmt = (
            select(Escalation)
            .where(Escalation.concern_id == concern_id)
            .order_by(Escalation.escalated_at.desc())
        )
        escalations = db.execute(escalation_stmt).scalars().all()

        # -------------------------------------
        # Get History (audit trail)
        # -------------------------------------
        history_stmt = (
            select(ConcernHistory)
            .where(ConcernHistory.concern_id == concern_id)
            .order_by(ConcernHistory.changed_at.asc())
        )
        history = db.execute(history_stmt).scalars().all()

        return {
            'concern': concern,
            'assignments': list(assignments),
            'comments': list(comments),
            'escalations': list(escalations),
            'history': list(history)
        }

    # =========================================
    # Meeting Detail with Relations
    # =========================================

    def get_meeting_with_relations(
        self,
        db: Session,
        school_id: UUID,
        meeting_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get meeting with all related data (participants, agenda, outcomes, attendance).
        Tenant-scoped with soft-delete filtering.
        Returns unified meeting detail view.
        """
        # -------------------------------------
        # Get Meeting
        # -------------------------------------
        meeting_stmt = (
            select(Meeting)
            .where(
                Meeting.id == meeting_id,
                Meeting.school_id == school_id,
                Meeting.is_deleted.is_(False)
            )
        )
        meeting = db.execute(meeting_stmt).scalar_one_or_none()
        
        if not meeting:
            return None

        # -------------------------------------
        # Get Participants
        # -------------------------------------
        participant_stmt = (
            select(MeetingParticipant)
            .where(MeetingParticipant.meeting_id == meeting_id)
            .order_by(MeetingParticipant.invited_at.desc())
        )
        participants = db.execute(participant_stmt).scalars().all()

        # -------------------------------------
        # Get Agenda Items
        # -------------------------------------
        agenda_stmt = (
            select(MeetingAgenda)
            .where(MeetingAgenda.meeting_id == meeting_id)
            .order_by(MeetingAgenda.item_order.asc())
        )
        agenda = db.execute(agenda_stmt).scalars().all()

        # -------------------------------------
        # Get Outcomes
        # -------------------------------------
        outcome_stmt = (
            select(MeetingOutcome)
            .where(MeetingOutcome.meeting_id == meeting_id)
            .order_by(MeetingOutcome.recorded_at.desc())
        )
        outcomes = db.execute(outcome_stmt).scalars().all()

        # -------------------------------------
        # Get Attendance Records
        # -------------------------------------
        attendance_stmt = (
            select(MeetingAttendance)
            .where(MeetingAttendance.meeting_id == meeting_id)
            .order_by(MeetingAttendance.check_in_time.asc().nulls_last())
        )
        attendance = db.execute(attendance_stmt).scalars().all()

        return {
            'meeting': meeting,
            'participants': list(participants),
            'agenda': list(agenda),
            'outcomes': list(outcomes),
            'attendance': list(attendance)
        }

    # =========================================
    # Wellness Check with Observations
    # =========================================

    def get_wellness_check_with_observations(
        self,
        db: Session,
        school_id: UUID,
        check_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get wellness check with recent observations.

        Tenant safety:
        - WellnessCheck scoped through Student join
        - Observations scoped through Student join

        Read-only aggregation.
        """

        from identity.models.profiles import Student

        check_stmt = (
            select(WellnessCheck)
            .join(Student, WellnessCheck.student_id == Student.id)
            .where(
                WellnessCheck.id == check_id,
                WellnessCheck.is_deleted.is_(False),
                Student.school_id == school_id,
            )
        )

        check = db.execute(check_stmt).scalar_one_or_none()

        if not check:
            return None


        observation_stmt = (
            select(StudentObservation)
            .join(Student, StudentObservation.student_id == Student.id)
            .where(
                StudentObservation.student_id == check.student_id,
                StudentObservation.is_deleted.is_(False),
                Student.school_id == school_id,
            )
            .order_by(StudentObservation.observation_date.desc())
            .limit(10)
        )

        observations = db.execute(observation_stmt).scalars().all()

        return {
            "wellness_check": check,
            "recent_observations": list(observations),
        }

    # =========================================
    # Assignment & Escalation Workloads
    # =========================================

    def get_staff_member_welfare_workload(
        self,
        db: Session,
        school_id: UUID,
        staff_member_id: UUID
    ) -> Dict[str, Any]:
        """
        Get welfare workload summary for a staff member.
        Includes pending assignments, escalations, upcoming meetings.
        Tenant-scoped.
        """
        pending_assignments = db.execute(
            select(func.count(ConcernAssignment.id))
            .join(Concern, ConcernAssignment.concern_id == Concern.id)
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
                ConcernAssignment.assigned_to_id == staff_member_id,
                ConcernAssignment.status == "pending",
            )
        ).scalar() or 0

        pending_escalations = db.execute(
            select(func.count(Escalation.id))
            .join(Concern, Escalation.concern_id == Concern.id)
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
                Escalation.escalated_to_id == staff_member_id,
                Escalation.status == "pending",
            )
        ).scalar() or 0

        now = datetime.utcnow()

        upcoming_meetings = db.execute(
            select(func.count(Meeting.id))
            .join(MeetingParticipant, Meeting.id == MeetingParticipant.meeting_id)
            .where(
                Meeting.school_id == school_id,
                Meeting.is_deleted.is_(False),
                MeetingParticipant.user_id == staff_member_id,
                Meeting.scheduled_at >= now,
                Meeting.status.in_(["scheduled", "confirmed"]),
            )
        ).scalar() or 0

        total_concerns = db.execute(
            select(func.count(func.distinct(ConcernAssignment.concern_id)))
            .join(Concern, ConcernAssignment.concern_id == Concern.id)
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
                ConcernAssignment.assigned_to_id == staff_member_id,
            )
        ).scalar() or 0

        return {
            "pending_assignments": pending_assignments,
            "pending_escalations": pending_escalations,
            "upcoming_meetings": upcoming_meetings,
            "total_concerns_handled": total_concerns,
        }

    def get_pending_escalations_list(
        self,
        db: Session,
        school_id: UUID,
        escalated_to_id: Optional[UUID] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get list of pending escalations with concern details.
        Tenant-scoped with optional filter by escalated_to user.
        Deterministic ordering by priority and escalated_at.
        """
        # -------------------------------------
        # Build Query
        # -------------------------------------
        stmt = (
            select(
                Escalation.id,
                Escalation.escalated_at,
                Escalation.priority,
                Escalation.reason,
                Escalation.due_date,
                Concern.id.label('concern_id'),
                Concern.title.label('concern_title'),
                Concern.severity.label('concern_severity'),
                Concern.status.label('concern_status')
            )
            .join(Concern, Escalation.concern_id == Concern.id)
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
                Escalation.status == 'pending'
            )
        )
        
        if escalated_to_id:
            stmt = stmt.where(Escalation.escalated_to_id == escalated_to_id)
        
        # Order by priority (urgent first) then escalated_at
        stmt = stmt.order_by(
            case(
                (Escalation.priority == 'urgent', 1),
                (Escalation.priority == 'high', 2),
                (Escalation.priority == 'medium', 3),
                (Escalation.priority == 'low', 4),
                else_=5
            ),
            Escalation.escalated_at.asc()
        )
        
        stmt = stmt.offset(skip).limit(limit)
        
        result = db.execute(stmt)
        
        return [
            {
                'escalation_id': str(row.id),
                'escalated_at': row.escalated_at,
                'priority': row.priority,
                'reason': row.reason,
                'due_date': row.due_date,
                'concern_id': str(row.concern_id),
                'concern_title': row.concern_title,
                'concern_severity': row.concern_severity,
                'concern_status': row.concern_status
            }
            for row in result
        ]

    # =========================================
    # Meeting Participation Reports
    # =========================================

    def get_meeting_participation_report(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get meeting participation report for a user.
        Includes meeting details, attendance status, role.
        Tenant-scoped.
        """
        # -------------------------------------
        # Build Query
        # -------------------------------------
        stmt = (
            select(
                Meeting.id.label('meeting_id'),
                Meeting.title,
                Meeting.scheduled_at,
                Meeting.meeting_type,
                Meeting.status.label('meeting_status'),
                MeetingParticipant.role,
                MeetingParticipant.invitation_status,
                MeetingParticipant.attendance_status,
                MeetingParticipant.attendance_confirmed_at
            )
            .join(MeetingParticipant, Meeting.id == MeetingParticipant.meeting_id)
            .where(
                Meeting.school_id == school_id,
                Meeting.is_deleted.is_(False),
                MeetingParticipant.user_id == user_id
            )
        )
        
        if start_date:
            stmt = stmt.where(Meeting.scheduled_at >= start_date)
        if end_date:
            stmt = stmt.where(Meeting.scheduled_at <= end_date)
        
        stmt = stmt.order_by(
            Meeting.scheduled_at.desc(),
            Meeting.id.desc()
        )
        
        stmt = stmt.offset(skip).limit(limit)
        
        result = db.execute(stmt)
        
        return [
            {
                'meeting_id': str(row.meeting_id),
                'title': row.title,
                'scheduled_at': row.scheduled_at,
                'meeting_type': row.meeting_type,
                'meeting_status': row.meeting_status,
                'role': row.role,
                'invitation_status': row.invitation_status,
                'attendance_status': row.attendance_status,
                'attendance_confirmed_at': row.attendance_confirmed_at
            }
            for row in result
        ]

    # =========================================
    # Comment & History Timelines
    # =========================================

    def get_concern_activity_timeline(
        self,
        db: Session,
        school_id: UUID,
        concern_id: UUID,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get unified activity timeline for a concern.
        Combines comments and history into single chronological view.
        Tenant-scoped with soft-delete filtering for comments.
        """
        timeline = []

        # -------------------------------------
        # Comments
        # -------------------------------------
        comment_stmt = (
            select(
                ConcernComment.id,
                ConcernComment.created_at.label("activity_date"),
                func.literal("comment").label("activity_type"),
                ConcernComment.user_id,
                ConcernComment.comment.label("content"),
                ConcernComment.is_internal,
                func.literal(None).label("action"),
                func.literal(None).label("previous_value"),
                func.literal(None).label("new_value"),
            )
            .join(Concern, ConcernComment.concern_id == Concern.id)
            .where(
                Concern.id == concern_id,
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
                ConcernComment.is_deleted.is_(False),
            )
        )

        for row in db.execute(comment_stmt):
            timeline.append({
                "id": str(row.id),
                "activity_date": row.activity_date,
                "activity_type": row.activity_type,
                "user_id": str(row.user_id) if row.user_id else None,
                "content": row.content,
                "is_internal": row.is_internal,
                "action": row.action,
                "previous_value": row.previous_value,
                "new_value": row.new_value,
            })

        # -------------------------------------
        # History
        # -------------------------------------
        history_stmt = (
            select(
                ConcernHistory.id,
                ConcernHistory.changed_at.label("activity_date"),
                func.literal("history").label("activity_type"),
                ConcernHistory.changed_by_id.label("user_id"),
                func.literal(None).label("content"),
                func.literal(None).label("is_internal"),
                ConcernHistory.action,
                ConcernHistory.previous_value,
                ConcernHistory.new_value,
            )
            .join(Concern, ConcernHistory.concern_id == Concern.id)
            .where(
                Concern.id == concern_id,
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
            )
        )

        for row in db.execute(history_stmt):
            timeline.append({
                "id": str(row.id),
                "activity_date": row.activity_date,
                "activity_type": row.activity_type,
                "user_id": str(row.user_id) if row.user_id else None,
                "content": row.content,
                "is_internal": row.is_internal,
                "action": row.action,
                "previous_value": row.previous_value,
                "new_value": row.new_value,
            })

        timeline.sort(key=lambda x: x["activity_date"], reverse=True)

        return timeline[skip: skip + limit]

    # =========================================
    # Bulk Count Queries (Dashboard Optimized)
    # =========================================

    def get_school_wide_welfare_metrics(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get school-wide welfare metrics for reporting.
        Optimized for dashboard with minimal queries.
        All counts are null-safe and tenant-scoped.
        """
        metrics = {}

        # -------------------------------------
        # Concern Metrics
        # -------------------------------------
        concern_base_filter = and_(
            Concern.school_id == school_id,
            Concern.is_deleted.is_(False)
        )
        
        if academic_year_id:
            # Would need academic_year_id on Concern model if filtering by year
            pass
        
        metrics['concerns'] = {
            'total': db.execute(
                select(func.count(Concern.id)).where(concern_base_filter)
            ).scalar() or 0,
            'resolved': db.execute(
                select(func.count(Concern.id)).where(
                    concern_base_filter, Concern.status == 'resolved'
                )
            ).scalar() or 0,
            'critical': db.execute(
                select(func.count(Concern.id)).where(
                    concern_base_filter, Concern.severity == 'critical'
                )
            ).scalar() or 0,
        }

        # -------------------------------------
        # Meeting Metrics
        # -------------------------------------
        meeting_base_filter = and_(
            Meeting.school_id == school_id,
            Meeting.is_deleted.is_(False)
        )
        
        now = datetime.utcnow()
        
        metrics['meetings'] = {
            'total': db.execute(
                select(func.count(Meeting.id)).where(meeting_base_filter)
            ).scalar() or 0,
            'upcoming': db.execute(
                select(func.count(Meeting.id)).where(
                    meeting_base_filter,
                    Meeting.scheduled_at >= now,
                    Meeting.status.in_(['scheduled', 'confirmed'])
                )
            ).scalar() or 0,
            'completed': db.execute(
                select(func.count(Meeting.id)).where(
                    meeting_base_filter, Meeting.status == 'completed'
                )
            ).scalar() or 0,
        }

        # -------------------------------------
        # Wellness Check Metrics
        # -------------------------------------
        from identity.models.profiles import Student
        
        wellness_base_filter = and_(
            Student.school_id == school_id,
            WellnessCheck.is_deleted.is_(False)
        )
        
        metrics['wellness_checks'] = {
            'total': db.execute(
                select(func.count(WellnessCheck.id))
                .join(Student, WellnessCheck.student_id == Student.id)
                .where(wellness_base_filter)
            ).scalar() or 0,
            'requiring_follow_up': db.execute(
                select(func.count(WellnessCheck.id))
                .join(Student, WellnessCheck.student_id == Student.id)
                .where(
                    wellness_base_filter,
                    WellnessCheck.follow_up_required.is_(True)
                )
            ).scalar() or 0,
        }

        # -------------------------------------
        # Observation Metrics
        # -------------------------------------
        observation_base_filter = and_(
            Student.school_id == school_id,
            StudentObservation.is_deleted.is_(False)
        )
        
        metrics['observations'] = {
            'total': db.execute(
                select(func.count(StudentObservation.id))
                .join(Student, StudentObservation.student_id == Student.id)
                .where(observation_base_filter)
            ).scalar() or 0,
            'concerning': db.execute(
                select(func.count(StudentObservation.id))
                .join(Student, StudentObservation.student_id == Student.id)
                .where(
                    observation_base_filter,
                    StudentObservation.severity == 'concerning'
                )
            ).scalar() or 0,
        }

        return metrics

    # =========================================
    # Export-Ready Queries
    # =========================================

    def export_concerns_for_school(
        self,
        db: Session,
        school_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Export concern data for reporting.

        Tenant safe.
        Uses DISTINCT counts to avoid duplication due to joins.
        """

        stmt = (
            select(
                Concern.id,
                Concern.student_id,
                Concern.type,
                Concern.title,
                Concern.description,
                Concern.severity,
                Concern.status,
                Concern.reported_at,
                Concern.resolved_at,
                Concern.resolution_notes,
                Concern.is_anonymous,
                func.count(func.distinct(ConcernAssignment.id)).label("assignment_count"),
                func.count(func.distinct(ConcernComment.id)).label("comment_count"),
                func.count(func.distinct(Escalation.id)).label("escalation_count"),
            )
            .outerjoin(
                ConcernAssignment,
                Concern.id == ConcernAssignment.concern_id,
            )
            .outerjoin(
                ConcernComment,
                Concern.id == ConcernComment.concern_id,
            )
            .outerjoin(
                Escalation,
                Concern.id == Escalation.concern_id,
            )
            .where(
                Concern.school_id == school_id,
                Concern.is_deleted.is_(False),
            )
            .group_by(Concern.id)
        )

        if start_date:
            stmt = stmt.where(Concern.reported_at >= start_date)

        if end_date:
            stmt = stmt.where(Concern.reported_at <= end_date)

        stmt = stmt.order_by(Concern.reported_at.desc())

        result = db.execute(stmt)

        return [dict(r._mapping) for r in result]
    

    def export_meetings_for_school(
        self,
        db: Session,
        school_id: UUID,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Export meeting data for reporting.

        Tenant safe.
        Uses DISTINCT counts to avoid join multiplication.
        """

        stmt = (
            select(
                Meeting.id,
                Meeting.title,
                Meeting.purpose,
                Meeting.meeting_type,
                Meeting.status,
                Meeting.scheduled_at,
                Meeting.duration_minutes,
                Meeting.location,
                func.count(func.distinct(MeetingParticipant.id)).label("participant_count"),
                func.count(func.distinct(MeetingAgenda.id)).label("agenda_count"),
                func.count(func.distinct(MeetingOutcome.id)).label("outcome_count"),
            )
            .outerjoin(
                MeetingParticipant,
                Meeting.id == MeetingParticipant.meeting_id,
            )
            .outerjoin(
                MeetingAgenda,
                Meeting.id == MeetingAgenda.meeting_id,
            )
            .outerjoin(
                MeetingOutcome,
                Meeting.id == MeetingOutcome.meeting_id,
            )
            .where(
                Meeting.school_id == school_id,
                Meeting.is_deleted.is_(False),
            )
            .group_by(Meeting.id)
        )

        if start_date:
            stmt = stmt.where(Meeting.scheduled_at >= start_date)

        if end_date:
            stmt = stmt.where(Meeting.scheduled_at <= end_date)

        stmt = stmt.order_by(Meeting.scheduled_at.desc())

        result = db.execute(stmt)

        return [dict(r._mapping) for r in result]