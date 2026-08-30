from typing import Annotated

from fastapi import Depends

from app.api.deps import DbSession

from .repository import OrganizationRepository, PersonnelAssignmentRepository, PersonnelRepository
from .service import OrganizationService, PersonnelAssignmentService, PersonnelService


def get_personnel_service(db: DbSession) -> PersonnelService:
    return PersonnelService(db, PersonnelRepository(db))


def get_assignment_service(db: DbSession) -> PersonnelAssignmentService:
    return PersonnelAssignmentService(
        db, PersonnelAssignmentRepository(db), PersonnelRepository(db), OrganizationRepository(db)
    )


def get_organization_service(db: DbSession) -> OrganizationService:
    return OrganizationService(db, OrganizationRepository(db), PersonnelRepository(db))


PersonnelServiceDep = Annotated[PersonnelService, Depends(get_personnel_service)]
PersonnelAssignmentServiceDep = Annotated[PersonnelAssignmentService, Depends(get_assignment_service)]
OrganizationServiceDep = Annotated[OrganizationService, Depends(get_organization_service)]
