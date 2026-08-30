from sqlalchemy import Select, String, cast, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .model import Department, Personnel, PersonnelAssignment, PLGroup, TMGroup

AssignmentRow = tuple[PersonnelAssignment, Personnel, TMGroup | None, PLGroup | None, Department | None]


class PersonnelRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, personnel_id: int) -> Personnel | None:
        return await self.db.get(Personnel, personnel_id)

    async def get_by_w3_account_exact(self, value: str) -> Personnel | None:
        return await self.db.scalar(select(Personnel).where(Personnel.w3_account == value))

    async def get_by_employee_id(self, value: str) -> Personnel | None:
        return await self.db.scalar(select(Personnel).where(Personnel.employee_id == value))

    async def list(
        self, q: str | None = None, w3_account: str | None = None, limit: int = 50, offset: int = 0
    ) -> list[Personnel]:
        statement = select(Personnel)
        if q:
            pattern = f"%{q}%"
            statement = statement.where(
                or_(
                    Personnel.w3_account.ilike(pattern),
                    Personnel.name.ilike(pattern),
                    Personnel.employee_id.ilike(pattern),
                )
            )
        if w3_account:
            statement = statement.where(Personnel.w3_account.ilike(f"%{w3_account}%"))
        statement = statement.order_by(Personnel.w3_account, Personnel.id).limit(limit).offset(offset)
        return list(await self.db.scalars(statement))

    async def add(self, entity: Personnel) -> None:
        self.db.add(entity)

    async def delete(self, entity: Personnel) -> None:
        await self.db.delete(entity)


class PersonnelAssignmentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    @staticmethod
    def _joined() -> Select:
        return (
            select(PersonnelAssignment, Personnel, TMGroup, PLGroup, Department)
            .join(Personnel, Personnel.id == PersonnelAssignment.personnel_id)
            .outerjoin(TMGroup, TMGroup.id == PersonnelAssignment.tm_group_id)
            .outerjoin(PLGroup, PLGroup.id == PersonnelAssignment.pl_group_id)
            .outerjoin(Department, Department.id == PersonnelAssignment.department_id)
        )

    async def get_by_id(self, assignment_id: int) -> AssignmentRow | None:
        row = (await self.db.execute(self._joined().where(PersonnelAssignment.id == assignment_id))).one_or_none()
        return tuple(row) if row else None

    async def get_entity_by_id(self, assignment_id: int) -> PersonnelAssignment | None:
        return await self.db.get(PersonnelAssignment, assignment_id)

    async def list(
        self,
        q: str | None = None,
        personnel_id: int | None = None,
        tm_group_id: int | None = None,
        pl_group_id: int | None = None,
        department_id: int | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AssignmentRow]:
        statement = self._joined()
        for column, value in (
            (PersonnelAssignment.personnel_id, personnel_id),
            (PersonnelAssignment.tm_group_id, tm_group_id),
            (PersonnelAssignment.pl_group_id, pl_group_id),
            (PersonnelAssignment.department_id, department_id),
        ):
            if value is not None:
                statement = statement.where(column == value)
        if q:
            pattern = f"%{q}%"
            statement = statement.where(
                or_(
                    Personnel.w3_account.ilike(pattern),
                    Personnel.name.ilike(pattern),
                    Personnel.employee_id.ilike(pattern),
                    TMGroup.name.ilike(pattern),
                    PLGroup.name.ilike(pattern),
                    Department.name.ilike(pattern),
                    PersonnelAssignment.creator.ilike(pattern),
                    PersonnelAssignment.notes.ilike(pattern),
                    cast(PersonnelAssignment.start_time, String).ilike(pattern),
                    cast(PersonnelAssignment.end_time, String).ilike(pattern),
                    cast(PersonnelAssignment.insert_time, String).ilike(pattern),
                )
            )
        statement = statement.order_by(PersonnelAssignment.insert_time.desc()).limit(limit).offset(offset)
        rows = (await self.db.execute(statement)).all()
        return [tuple(row) for row in rows]

    async def add(self, entity: PersonnelAssignment) -> None:
        self.db.add(entity)

    async def delete(self, entity: PersonnelAssignment) -> None:
        await self.db.delete(entity)


class OrganizationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_tm_by_id(self, entity_id: int) -> TMGroup | None:
        return await self.db.get(TMGroup, entity_id)

    async def get_tm_by_name(self, name: str) -> TMGroup | None:
        return await self.db.scalar(select(TMGroup).where(TMGroup.name == name))

    async def list_tms(self, q: str | None = None, limit: int = 50, offset: int = 0) -> list[TMGroup]:
        statement = select(TMGroup)
        if q:
            statement = statement.where(TMGroup.name.ilike(f"%{q}%"))
        return list(await self.db.scalars(statement.order_by(TMGroup.name).limit(limit).offset(offset)))

    async def add_tm(self, entity: TMGroup) -> None:
        self.db.add(entity)

    async def delete_tm(self, entity: TMGroup) -> None:
        await self.db.delete(entity)

    async def get_pl_by_id(self, entity_id: int) -> PLGroup | None:
        return await self.db.get(PLGroup, entity_id)

    async def get_pl_by_name(self, name: str) -> PLGroup | None:
        return await self.db.scalar(select(PLGroup).where(PLGroup.name == name))

    async def list_pls(self, q: str | None = None, limit: int = 50, offset: int = 0) -> list[PLGroup]:
        statement = select(PLGroup)
        if q:
            statement = statement.where(PLGroup.name.ilike(f"%{q}%"))
        return list(await self.db.scalars(statement.order_by(PLGroup.name).limit(limit).offset(offset)))

    async def add_pl(self, entity: PLGroup) -> None:
        self.db.add(entity)

    async def delete_pl(self, entity: PLGroup) -> None:
        await self.db.delete(entity)

    async def get_department_by_id(self, entity_id: int) -> Department | None:
        return await self.db.get(Department, entity_id)

    async def get_department_by_name(self, name: str) -> Department | None:
        return await self.db.scalar(select(Department).where(Department.name == name))

    async def list_departments(self, q: str | None = None, limit: int = 50, offset: int = 0) -> list[Department]:
        statement = select(Department)
        if q:
            statement = statement.where(Department.name.ilike(f"%{q}%"))
        return list(await self.db.scalars(statement.order_by(Department.name).limit(limit).offset(offset)))

    async def add_department(self, entity: Department) -> None:
        self.db.add(entity)

    async def delete_department(self, entity: Department) -> None:
        await self.db.delete(entity)
