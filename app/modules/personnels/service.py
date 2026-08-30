from datetime import date

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ConflictError, NotFoundError

from .model import Department, Personnel, PersonnelAssignment, PLGroup, TMGroup
from .repository import AssignmentRow, OrganizationRepository, PersonnelAssignmentRepository, PersonnelRepository
from .schemas import (
    DepartmentCreate,
    DepartmentUpdate,
    OrganizationSummary,
    PersonnelAssignmentCreate,
    PersonnelAssignmentRead,
    PersonnelAssignmentUpdate,
    PersonnelCreate,
    PersonnelRead,
    PersonnelUpdate,
    PLGroupCreate,
    PLGroupUpdate,
    TMGroupCreate,
    TMGroupUpdate,
)


class ServiceBase:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def _commit(self, message: str) -> None:
        try:
            await self.db.commit()
        except IntegrityError as exc:
            await self.db.rollback()
            raise ConflictError(message) from exc

    @staticmethod
    def _apply(entity: object, payload: BaseModel) -> None:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(entity, field, value)


class PersonnelService(ServiceBase):
    def __init__(self, db: AsyncSession, repository: PersonnelRepository) -> None:
        super().__init__(db)
        self.repository = repository

    async def create(self, payload: PersonnelCreate) -> Personnel:
        await self._validate_unique(payload.w3_account, payload.employee_id)
        entity = Personnel(**payload.model_dump())
        await self.repository.add(entity)
        await self._commit("Personnel already exists")
        return entity

    async def list(
        self, q: str | None = None, w3_account: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[Personnel]:
        return await self.repository.list(q, w3_account, limit, offset)

    async def get(self, personnel_id: int) -> Personnel:
        entity = await self.repository.get_by_id(personnel_id)
        if not entity:
            raise NotFoundError("Personnel not found")
        return entity

    async def update(self, personnel_id: int, payload: PersonnelUpdate) -> Personnel:
        entity = await self.get(personnel_id)
        if "w3_account" in payload.model_fields_set and payload.w3_account != entity.w3_account:
            found = await self.repository.get_by_w3_account_exact(payload.w3_account)
            if found:
                raise ConflictError("W3 account already exists")
        if (
            "employee_id" in payload.model_fields_set
            and payload.employee_id is not None
            and payload.employee_id != entity.employee_id
        ):
            found = await self.repository.get_by_employee_id(payload.employee_id)
            if found:
                raise ConflictError("Employee ID already exists")
        self._apply(entity, payload)
        await self._commit("Personnel already exists")
        return entity

    async def delete(self, personnel_id: int) -> None:
        entity = await self.get(personnel_id)
        await self.repository.delete(entity)
        await self._commit("Personnel is in use")

    async def _validate_unique(self, w3_account: str, employee_id: str | None) -> None:
        if await self.repository.get_by_w3_account_exact(w3_account):
            raise ConflictError("W3 account already exists")
        if employee_id is not None and await self.repository.get_by_employee_id(employee_id):
            raise ConflictError("Employee ID already exists")


class PersonnelAssignmentService(ServiceBase):
    def __init__(
        self,
        db: AsyncSession,
        repository: PersonnelAssignmentRepository,
        personnels: PersonnelRepository,
        organizations: OrganizationRepository,
    ) -> None:
        super().__init__(db)
        self.repository = repository
        self.personnels = personnels
        self.organizations = organizations

    async def create(self, payload: PersonnelAssignmentCreate) -> PersonnelAssignmentRead:
        await self._validate_relations(
            payload.personnel_id, payload.tm_group_id, payload.pl_group_id, payload.department_id
        )
        self._validate_time(payload.start_time, payload.end_time)
        entity = PersonnelAssignment(**payload.model_dump())
        await self.repository.add(entity)
        await self._commit("Unable to create personnel assignment")
        return await self.get(entity.id)

    async def get(self, assignment_id: int) -> PersonnelAssignmentRead:
        row = await self.repository.get_by_id(assignment_id)
        if not row:
            raise NotFoundError("Personnel assignment not found")
        return self._read(row)

    async def list(
        self,
        q: str | None = None,
        personnel_id: int | None = None,
        tm_group_id: int | None = None,
        pl_group_id: int | None = None,
        department_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PersonnelAssignmentRead]:
        rows = await self.repository.list(q, personnel_id, tm_group_id, pl_group_id, department_id, limit, offset)
        return [self._read(row) for row in rows]

    async def update(self, assignment_id: int, payload: PersonnelAssignmentUpdate) -> PersonnelAssignmentRead:
        entity = await self.repository.get_entity_by_id(assignment_id)
        if not entity:
            raise NotFoundError("Personnel assignment not found")
        values = payload.model_dump(exclude_unset=True)
        personnel_id = values.get("personnel_id", entity.personnel_id)
        tm_id = values.get("tm_group_id", entity.tm_group_id)
        pl_id = values.get("pl_group_id", entity.pl_group_id)
        department_id = values.get("department_id", entity.department_id)
        await self._validate_relations(personnel_id, tm_id, pl_id, department_id)
        self._validate_time(values.get("start_time", entity.start_time), values.get("end_time", entity.end_time))
        self._apply(entity, payload)
        await self._commit("Unable to update personnel assignment")
        return await self.get(entity.id)

    async def delete(self, assignment_id: int) -> None:
        entity = await self.repository.get_entity_by_id(assignment_id)
        if not entity:
            raise NotFoundError("Personnel assignment not found")
        await self.repository.delete(entity)
        await self._commit("Unable to delete personnel assignment")

    async def _validate_relations(
        self, personnel_id: int, tm_id: int | None, pl_id: int | None, department_id: int | None
    ) -> None:
        if not await self.personnels.get_by_id(personnel_id):
            raise BadRequestError("Personnel does not exist")
        if tm_id is not None and not await self.organizations.get_tm_by_id(tm_id):
            raise BadRequestError("TM group does not exist")
        if pl_id is not None and not await self.organizations.get_pl_by_id(pl_id):
            raise BadRequestError("PL group does not exist")
        if department_id is not None and not await self.organizations.get_department_by_id(department_id):
            raise BadRequestError("Department does not exist")

    @staticmethod
    def _validate_time(start: date | None, end: date | None) -> None:
        if start is not None and end is not None and end < start:
            raise BadRequestError("End date must not be earlier than start date")

    @staticmethod
    def _read(row: AssignmentRow) -> PersonnelAssignmentRead:
        assignment, personnel, tm, pl, department = row
        summary = lambda value: OrganizationSummary(id=value.id, name=value.name) if value else None
        return PersonnelAssignmentRead(
            id=assignment.id,
            personnel=PersonnelRead.model_validate(personnel),
            tm_group=summary(tm),
            pl_group=summary(pl),
            department=summary(department),
            start_time=assignment.start_time,
            end_time=assignment.end_time,
            creator=assignment.creator,
            insert_time=assignment.insert_time,
            notes=assignment.notes,
        )


class OrganizationService(ServiceBase):
    def __init__(self, db: AsyncSession, repository: OrganizationRepository, personnels: PersonnelRepository) -> None:
        super().__init__(db)
        self.repository = repository
        self.personnels = personnels

    async def list_tms(self, q=None, limit=50, offset=0):
        return await self.repository.list_tms(q, limit, offset)

    async def list_pls(self, q=None, limit=50, offset=0):
        return await self.repository.list_pls(q, limit, offset)

    async def list_departments(self, q=None, limit=50, offset=0):
        return await self.repository.list_departments(q, limit, offset)

    async def get_tm(self, entity_id: int) -> TMGroup:
        return await self._get(self.repository.get_tm_by_id, entity_id, "TM group")

    async def get_pl(self, entity_id: int) -> PLGroup:
        return await self._get(self.repository.get_pl_by_id, entity_id, "PL group")

    async def get_department(self, entity_id: int) -> Department:
        return await self._get(self.repository.get_department_by_id, entity_id, "Department")

    async def create_tm(self, payload: TMGroupCreate) -> TMGroup:
        await self._validate_leader(payload.leader_personnel_id)
        if await self.repository.get_tm_by_name(payload.name):
            raise ConflictError("TM group already exists")
        entity = TMGroup(**payload.model_dump())
        await self.repository.add_tm(entity)
        await self._commit("TM group already exists")
        return entity

    async def create_pl(self, payload: PLGroupCreate) -> PLGroup:
        await self._validate_leader(payload.leader_personnel_id)
        if await self.repository.get_pl_by_name(payload.name):
            raise ConflictError("PL group already exists")
        entity = PLGroup(**payload.model_dump())
        await self.repository.add_pl(entity)
        await self._commit("PL group already exists")
        return entity

    async def create_department(self, payload: DepartmentCreate) -> Department:
        if await self.repository.get_department_by_name(payload.name):
            raise ConflictError("Department already exists")
        entity = Department(**payload.model_dump())
        await self.repository.add_department(entity)
        await self._commit("Department already exists")
        return entity

    async def update_tm(self, entity_id: int, payload: TMGroupUpdate) -> TMGroup:
        entity = await self.get_tm(entity_id)
        if (
            "name" in payload.model_fields_set
            and payload.name != entity.name
            and await self.repository.get_tm_by_name(payload.name)
        ):
            raise ConflictError("TM group already exists")
        if "leader_personnel_id" in payload.model_fields_set:
            await self._validate_leader(payload.leader_personnel_id)
        self._apply(entity, payload)
        await self._commit("TM group already exists")
        return entity

    async def update_pl(self, entity_id: int, payload: PLGroupUpdate) -> PLGroup:
        entity = await self.get_pl(entity_id)
        if (
            "name" in payload.model_fields_set
            and payload.name != entity.name
            and await self.repository.get_pl_by_name(payload.name)
        ):
            raise ConflictError("PL group already exists")
        if "leader_personnel_id" in payload.model_fields_set:
            await self._validate_leader(payload.leader_personnel_id)
        self._apply(entity, payload)
        await self._commit("PL group already exists")
        return entity

    async def update_department(self, entity_id: int, payload: DepartmentUpdate) -> Department:
        entity = await self.get_department(entity_id)
        if (
            "name" in payload.model_fields_set
            and payload.name != entity.name
            and await self.repository.get_department_by_name(payload.name)
        ):
            raise ConflictError("Department already exists")
        self._apply(entity, payload)
        await self._commit("Department already exists")
        return entity

    async def delete_tm(self, entity_id: int) -> None:
        await self.repository.delete_tm(await self.get_tm(entity_id))
        await self._commit("TM group is in use")

    async def delete_pl(self, entity_id: int) -> None:
        await self.repository.delete_pl(await self.get_pl(entity_id))
        await self._commit("PL group is in use")

    async def delete_department(self, entity_id: int) -> None:
        await self.repository.delete_department(await self.get_department(entity_id))
        await self._commit("Department is in use")

    async def _validate_leader(self, personnel_id: int | None) -> None:
        if personnel_id is not None and not await self.personnels.get_by_id(personnel_id):
            raise BadRequestError("Leader personnel does not exist")

    @staticmethod
    async def _get(getter, entity_id: int, label: str):
        entity = await getter(entity_id)
        if not entity:
            raise NotFoundError(f"{label} not found")
        return entity
