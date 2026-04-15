# identity/repositories/aggregates/aggregate_repository.py


# identity_aggregate_repository.py

from typing import Optional, List, Dict, Any, Literal
from uuid import UUID
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from identity.models.accounts import User, UserRole
from identity.models.profiles import Student, Parent, StaffMember, Driver

from accounts.user_repository import UserRepository
from accounts.role_repository import RoleRepository
from accounts.user_role_repository import UserRoleRepository
from profiles.student_repository import StudentRepository
from profiles.parent_repository import ParentRepository
from profiles.staff_repository import StaffRepository
from profiles.driver_repository import DriverRepository


ProfileType = Literal["student", "parent", "staff", "driver"]


class IdentityAggregateRepository:
    """
    Transactional orchestration layer for multi-entity identity operations.
    Does NOT extend SchoolScopedRepository - composes existing repositories.
    Coordinates operations within a single database session passed from service layer.
    Never commits transactions - only flush operations.
    Purely a consistency and atomicity boundary.
    Zero business validation rules, permission logic, or domain policies.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        user_role_repo: UserRoleRepository,
        student_repo: StudentRepository,
        parent_repo: ParentRepository,
        staff_repo: StaffRepository,
        driver_repo: DriverRepository
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.user_role_repo = user_role_repo
        self.student_repo = student_repo
        self.parent_repo = parent_repo
        self.staff_repo = staff_repo
        self.driver_repo = driver_repo

    # =========================================
    # Atomic User + Profile Creation
    # =========================================

    def create_user_with_profile(
        self,
        db: Session,
        school_id: UUID,
        user_data: Dict[str, Any],
        profile_type: ProfileType,
        profile_data: Dict[str, Any],
        default_role_names: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """
        Atomically create a User together with exactly one domain profile.
        Assigns default roles during creation by locking Role rows before assignment.
        Ensures uniqueness validation via repository existence checks before insertion.
        Returns dict with 'user', 'profile', and 'user_roles' keys.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Validate uniqueness before insertion
        # -------------------------------------
        email = user_data.get('email')
        phone = user_data.get('phone')
        
        if email and self.user_repo.exists_email(db, school_id, email):
            raise ValueError(f"Email {email} already exists in school {school_id}")
        
        if phone and self.user_repo.exists_phone(db, school_id, phone):
            raise ValueError(f"Phone {phone} already exists in school {school_id}")

        # -------------------------------------
        # Step 2: Create User (locked for safety)
        # -------------------------------------
        user = User(
            school_id=school_id,
            email=email,
            phone=phone,
            password_hash=user_data.get('password_hash'),
            first_name=user_data.get('first_name'),
            last_name=user_data.get('last_name'),
            date_of_birth=user_data.get('date_of_birth'),
            is_active=user_data.get('is_active', True),
            is_deleted=False
        )
        db.add(user)
        db.flush()  # Get user.id

        # -------------------------------------
        # Step 3: Create Profile based on type
        # -------------------------------------
        profile = None
        
        if profile_type == "student":
            # Validate admission_number uniqueness
            admission_number = profile_data.get('admission_number')
            if admission_number and self.student_repo.exists_admission_number(
                db, school_id, admission_number
            ):
                
                raise ValueError(f"Admission number {admission_number} already exists")
            
            profile = Student(
                user_id=user.id,
                school_id=school_id,
                admission_number=admission_number,
                date_of_birth=profile_data.get('date_of_birth'),
                emergency_contact_name=profile_data.get('emergency_contact_name'),
                emergency_contact_phone=profile_data.get('emergency_contact_phone'),
                is_deleted=False
            )
        
        elif profile_type == "parent":
            profile = Parent(
                user_id=user.id,
                school_id=school_id,
                occupation=profile_data.get('occupation'),
                is_deleted=False
            )
        
        elif profile_type == "staff":
            # Validate employee_id uniqueness
            employee_id = profile_data.get('employee_id')
            if employee_id and self.staff_repo.exists_employee_id(
                db, school_id, employee_id
            ):
        
                raise ValueError(f"Employee ID {employee_id} already exists")
            
            profile = StaffMember(
                user_id=user.id,
                school_id=school_id,
                employee_id=employee_id,
                position=profile_data.get('position'),
                department=profile_data.get('department'),
                date_of_joining=profile_data.get('date_of_joining'),
                qualifications=profile_data.get('qualifications'),
                is_deleted=False
            )
        
        elif profile_type == "driver":
            # Validate license_number uniqueness
            license_number = profile_data.get('license_number')
            if license_number and self.driver_repo.exists_license_number(
                db, school_id, license_number
            ):
                
                raise ValueError(f"License number {license_number} already exists")
            
            profile = Driver(
                staff_member_id=profile_data.get('staff_member_id'),
                school_id=school_id,
                license_number=license_number,
                license_type=profile_data.get('license_type'),
                license_expiry=profile_data.get('license_expiry'),
                status=profile_data.get('status')
            )
        
        if profile:
            db.add(profile)
            db.flush()  # Get profile.id

        # -------------------------------------
        # Step 4: Assign default roles (with locking)
        # -------------------------------------
        assigned_roles = []
        
        if default_role_names:
            for role_name in default_role_names:
                # Lock role row to prevent race conditions
                role = self.role_repo.lock_by_name_for_update(db, school_id, role_name)
                
                if role:
                    # Check if assignment already exists (idempotency)
                    if not self.user_role_repo.exists_assignment(
                        db, school_id, user.id, role.id, active_only=False
                    ):
                        user_role = UserRole(
                            user_id=user.id,
                            role_id=role.id,
                            is_active=True
                        )
                        db.add(user_role)
                        assigned_roles.append(user_role)
        
        db.flush()  # Flush all role assignments

        return {
            'user': user,
            'profile': profile,
            'user_roles': assigned_roles
        }

    # =========================================
    # Cascade Deactivation
    # =========================================

    def deactivate_user_cascade(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Cascade-safe deactivation: lock User row, deactivate all UserRole records,
        and soft-delete or deactivate linked profiles in deterministic order.
        Returns dict with deactivation results.
        Only flushes - does not commit.
        """
        results = {
            'user_deactivated': False,
            'roles_deactivated': 0,
            'profile_deactivated': False,
            'profile_type': None
        }

        # -------------------------------------
        # Step 1: Lock User for update
        # -------------------------------------
        user = self.user_repo.lock_for_update(db, school_id, user_id)
        
        if not user:
            return results
        
        # -------------------------------------
        # Step 2: Deactivate User
        # -------------------------------------
        user.is_active = False
        db.flush()
        results['user_deactivated'] = True

        # -------------------------------------
        # Step 3: Deactivate all UserRole records
        # -------------------------------------
        role_deactivate_count = self.user_role_repo.bulk_deactivate_by_user(
            db, school_id, user_id
        )
        results['roles_deactivated'] = role_deactivate_count

        # -------------------------------------
        # Step 4: Soft-delete linked profile
        # -------------------------------------
        # Check for Student profile
        student = self.student_repo.get_by_user_id(db, school_id, user_id)
        if student:
            self.student_repo.soft_delete(db, school_id, student.id)
            results['profile_deactivated'] = True
            results['profile_type'] = 'student'
        else:
            # Check for Parent profile
            parent = self.parent_repo.get_by_user_id(db, school_id, user_id)
            if parent:
                self.parent_repo.soft_delete(db, school_id, parent.id)
                results['profile_deactivated'] = True
                results['profile_type'] = 'parent'
            else:
                # Check for Staff profile
                staff = self.staff_repo.get_by_user_id(db, school_id, user_id)
                if staff:
                    self.staff_repo.soft_delete(db, school_id, staff.id)
                    results['profile_deactivated'] = True
                    results['profile_type'] = 'staff'

        db.flush()
        return results

    # =========================================
    # Cascade Reactivation
    # =========================================

    def reactivate_user_cascade(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Reverse cascade while respecting soft-delete constraints.
        Restores User, reactivates UserRole records, and restores linked profiles.
        Only flushes - does not commit.
        """

        results = {
            'user_reactivated': False,
            'roles_reactivated': 0,
            'profile_reactivated': False,
            'profile_type': None
        }

        # -------------------------------------
        # Step 1: Lock User
        # -------------------------------------
        user = self.user_repo.lock_for_update(db, school_id, user_id)
        if not user:
            return results

        # -------------------------------------
        # Step 2: Reactivate User
        # -------------------------------------
        user.is_active = True
        db.flush()
        results['user_reactivated'] = True

        # -------------------------------------
        # Step 3: Reactivate ALL user role assignments
        # -------------------------------------
        user_roles = self.user_role_repo.list_by_user(
            db, school_id, user_id
        )

        role_ids = [ur.id for ur in user_roles]

        if role_ids:
            count = self.user_role_repo.bulk_activate_assignments(
                db, school_id, role_ids
            )
            results['roles_reactivated'] = count

        # -------------------------------------
        # Step 4: Restore linked profile (explicit tenant-safe select)
        # -------------------------------------

        # ---- Student
        stmt = (
            select(Student)
            .where(
                Student.user_id == user_id,
                Student.school_id == school_id,
                Student.is_deleted.is_(True)
            )
        )
        student = db.execute(stmt).scalar_one_or_none()

        if student:
            self.student_repo.restore(db, school_id, student.id)
            results['profile_reactivated'] = True
            results['profile_type'] = 'student'
            db.flush()
            return results

        # ---- Parent
        stmt = (
            select(Parent)
            .where(
                Parent.user_id == user_id,
                Parent.school_id == school_id,
                Parent.is_deleted.is_(True)
            )
        )
        parent = db.execute(stmt).scalar_one_or_none()

        if parent:
            self.parent_repo.restore(db, school_id, parent.id)
            results['profile_reactivated'] = True
            results['profile_type'] = 'parent'
            db.flush()
            return results

        # ---- Staff
        stmt = (
            select(StaffMember)
            .where(
                StaffMember.user_id == user_id,
                StaffMember.school_id == school_id,
                StaffMember.is_deleted.is_(True)
            )
        )
        staff = db.execute(stmt).scalar_one_or_none()

        if staff:
            self.staff_repo.restore(db, school_id, staff.id)
            results['profile_reactivated'] = True
            results['profile_type'] = 'staff'

            # ---- Driver (linked via staff_member_id)
            driver = self.driver_repo.get_by_staff_member_id(
                db, school_id, staff.id
            )
            if driver:
                # Driver has no soft delete — just ensure active status if needed
                pass

            db.flush()
            return results

        db.flush()
        return results

    # =========================================
    # Soft-Delete Orchestration
    # =========================================

    def soft_delete_user_cascade(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """
        Perform safe soft-delete orchestration across user, roles, and profiles
        without violating referential integrity.
        Returns dict with deletion results.
        Only flushes - does not commit.
        """
        results = {
            'user_deleted': False,
            'roles_deactivated': 0,
            'profile_deleted': False,
            'profile_type': None
        }

        # -------------------------------------
        # Step 1: Lock User for update
        # -------------------------------------
        user = self.user_repo.lock_for_update(db, school_id, user_id)
        
        if not user:
            return results
        
        # -------------------------------------
        # Step 2: Soft-delete User
        # -------------------------------------
        now = datetime.utcnow()
        user.is_deleted = True
        user.deleted_at = now
        db.flush()
        results['user_deleted'] = True

        # -------------------------------------
        # Step 3: Deactivate all UserRole records
        # -------------------------------------
        role_deactivate_count = self.user_role_repo.bulk_deactivate_by_user(
            db, school_id, user_id
        )
        results['roles_deactivated'] = role_deactivate_count

        # -------------------------------------
        # Step 4: Soft-delete linked profile
        # -------------------------------------
        # Check for Student profile
        student = self.student_repo.get_by_user_id(db, school_id, user_id)
        if student:
            self.student_repo.soft_delete(db, school_id, student.id)
            results['profile_deleted'] = True
            results['profile_type'] = 'student'
        else:
            # Check for Parent profile
            parent = self.parent_repo.get_by_user_id(db, school_id, user_id)
            if parent:
                self.parent_repo.soft_delete(db, school_id, parent.id)
                results['profile_deleted'] = True
                results['profile_type'] = 'parent'
            else:
                # Check for Staff profile
                staff = self.staff_repo.get_by_user_id(db, school_id, user_id)
                if staff:
                    self.staff_repo.soft_delete(db, school_id, staff.id)
                    results['profile_deleted'] = True
                    results['profile_type'] = 'staff'

        db.flush()
        return results

    # =========================================
    # Cross-Entity Reads (Tenant-Safe)
    # =========================================

    def get_user_with_profile_and_roles(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve User with linked profile and roles using explicit joins.
        All cross-entity reads use explicit tenant filters.
        No lazy loading - prevents cross-tenant leakage.
        Returns dict with 'user', 'profile', 'profile_type', 'roles' keys.
        """
        # -------------------------------------
        # Step 1: Get User (tenant-scoped)
        # -------------------------------------
        user = self.user_repo.get_by_id(db, school_id, user_id)
        
        if not user:
            return None

        # -------------------------------------
        # Step 2: Get Profile (explicit tenant filter)
        # -------------------------------------
        profile = None
        profile_type = None

        student = self.student_repo.get_by_user_id(db, school_id, user_id)
        if student:
            profile = student
            profile_type = 'student'
        else:
            parent = self.parent_repo.get_by_user_id(db, school_id, user_id)
            if parent:
                profile = parent
                profile_type = 'parent'
            else:
                staff = self.staff_repo.get_by_user_id(db, school_id, user_id)
                if staff:
                    profile = staff
                    profile_type = 'staff'

        # -------------------------------------
        # Step 3: Get Roles (explicit tenant filter via joins)
        # -------------------------------------
        user_roles = self.user_role_repo.list_active_assignments(
            db, school_id, user_id
        )

        roles = []
        for user_role in user_roles:
            role = self.role_repo.get_by_id(db, school_id, user_role.role_id)
            if role:
                roles.append({
                    'role': role,
                    'assigned_at': user_role.assigned_at,
                    'is_active': user_role.is_active
                })

        return {
            'user': user,
            'profile': profile,
            'profile_type': profile_type,
            'roles': roles
        }

    def get_user_by_email_with_profile(
        self,
        db: Session,
        school_id: UUID,
        email: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve User by email with linked profile using explicit tenant filters.
        No lazy loading - prevents cross-tenant leakage.
        Returns dict with 'user', 'profile', 'profile_type' keys.
        """
        # -------------------------------------
        # Step 1: Get User by email (tenant-scoped)
        # -------------------------------------
        user = self.user_repo.get_by_email(db, school_id, email)
        
        if not user:
            return None

        # -------------------------------------
        # Step 2: Get Profile (explicit tenant filter)
        # -------------------------------------
        profile = None
        profile_type = None

        student = self.student_repo.get_by_user_id(db, school_id, user.id)
        if student:
            profile = student
            profile_type = 'student'
        else:
            parent = self.parent_repo.get_by_user_id(db, school_id, user.id)
            if parent:
                profile = parent
                profile_type = 'parent'
            else:
                staff = self.staff_repo.get_by_user_id(db, school_id, user.id)
                if staff:
                    profile = staff
                    profile_type = 'staff'

        return {
            'user': user,
            'profile': profile,
            'profile_type': profile_type
        }

    # =========================================
    # Idempotent Role Assignment
    # =========================================

    def assign_role_to_user_idempotent(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        role_name: Any
    ) -> Optional[UserRole]:
        """
        Assign role to user idempotently.
        Locks Role row before assignment to prevent race conditions.
        Returns existing or newly created UserRole.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Lock User for update
        # -------------------------------------
        user = self.user_repo.lock_for_update(db, school_id, user_id)
        
        if not user:
            return None

        # -------------------------------------
        # Step 2: Lock Role by name for update
        # -------------------------------------
        role = self.role_repo.lock_by_name_for_update(db, school_id, role_name)
        
        if not role:
            return None

        # -------------------------------------
        # Step 3: Check existing assignment (idempotency)
        # -------------------------------------
        existing = self.user_role_repo.lock_by_user_and_role_for_update(
            db, school_id, user_id, role.id
        )

        if existing:
            # Reactivate if inactive
            if not existing.is_active:
                existing.is_active = True
                db.flush()
            return existing

        # -------------------------------------
        # Step 4: Create new assignment
        # -------------------------------------
        user_role = UserRole(
            user_id=user_id,
            role_id=role.id,
            is_active=True
        )
        db.add(user_role)
        db.flush()

        return user_role

    def revoke_role_from_user_idempotent(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        role_name: Any
    ) -> bool:
        """
        Revoke role from user idempotently.
        Locks Role row before revocation to prevent race conditions.
        Returns True if role was revoked, False if not found.
        Only flushes - does not commit.
        """
        # -------------------------------------
        # Step 1: Lock User for update
        # -------------------------------------
        user = self.user_repo.lock_for_update(db, school_id, user_id)
        
        if not user:
            return False

        # -------------------------------------
        # Step 2: Lock Role by name for update
        # -------------------------------------
        role = self.role_repo.lock_by_name_for_update(db, school_id, role_name)
        
        if not role:
            return False

        # -------------------------------------
        # Step 3: Revoke assignment (set is_active=False)
        # -------------------------------------
        return self.user_role_repo.revoke_role(db, school_id, user_id, role.id)

    # =========================================
    # Bulk Identity Operations
    # =========================================

    def bulk_assign_role_to_users(
        self,
        db: Session,
        school_id: UUID,
        user_ids: List[UUID],
        role_name: Any
    ) -> int:
        """
        Bulk assign role to multiple users idempotently.
        Locks Role row before assignment to prevent race conditions.
        Returns count of new assignments created.
        Only flushes - does not commit.
        """
        if not user_ids:
            return 0

        # -------------------------------------
        # Step 1: Lock Role by name for update
        # -------------------------------------
        role = self.role_repo.lock_by_name_for_update(db, school_id, role_name)
        
        if not role:
            return 0

        # -------------------------------------
        # Step 2: Create assignments for users without this role
        # -------------------------------------
        created_count = 0
        
        for user_id in user_ids:
            # Check if assignment already exists
            if not self.user_role_repo.exists_assignment(
                db, school_id, user_id, role.id, active_only=False
            ):
                user_role = UserRole(
                    user_id=user_id,
                    role_id=role.id,
                    is_active=True
                )
                db.add(user_role)
                created_count += 1

        db.flush()
        return created_count

    def bulk_deactivate_users(
        self,
        db: Session,
        school_id: UUID,
        user_ids: List[UUID]
    ) -> int:
        """
        Bulk deactivate multiple users with cascade to roles.
        Returns count of users deactivated.
        Only flushes - does not commit.
        """
        if not user_ids:
            return 0

        deactivated_count = 0

        for user_id in user_ids:
            result = self.deactivate_user_cascade(db, school_id, user_id)
            if result['user_deactivated']:
                deactivated_count += 1

        db.flush()
        return deactivated_count