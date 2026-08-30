from fastapi import APIRouter, Query, Response, status

from .dependencies import OrganizationServiceDep, PersonnelAssignmentServiceDep, PersonnelServiceDep
from .schemas import (
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
    PersonnelAssignmentCreate,
    PersonnelAssignmentRead,
    PersonnelAssignmentUpdate,
    PersonnelCreate,
    PersonnelRead,
    PersonnelUpdate,
    PLGroupCreate,
    PLGroupRead,
    PLGroupUpdate,
    TMGroupCreate,
    TMGroupRead,
    TMGroupUpdate,
)

router = APIRouter(tags=["personnels"])


@router.post("/personnels", response_model=PersonnelRead, status_code=status.HTTP_201_CREATED)
async def create_personnel(payload: PersonnelCreate, service: PersonnelServiceDep):
    return await service.create(payload)


@router.get("/personnels", response_model=list[PersonnelRead])
async def list_personnels(
    service: PersonnelServiceDep,
    q: str | None = None,
    w3_account: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await service.list(q, w3_account, limit, offset)


@router.get("/personnels/{personnel_id}", response_model=PersonnelRead)
async def get_personnel(personnel_id: int, service: PersonnelServiceDep):
    return await service.get(personnel_id)


@router.patch("/personnels/{personnel_id}", response_model=PersonnelRead)
async def update_personnel(personnel_id: int, payload: PersonnelUpdate, service: PersonnelServiceDep):
    return await service.update(personnel_id, payload)


@router.delete("/personnels/{personnel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personnel(personnel_id: int, service: PersonnelServiceDep) -> Response:
    await service.delete(personnel_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/personnel-assignments", response_model=PersonnelAssignmentRead, status_code=status.HTTP_201_CREATED)
async def create_assignment(payload: PersonnelAssignmentCreate, service: PersonnelAssignmentServiceDep):
    return await service.create(payload)


@router.get("/personnel-assignments", response_model=list[PersonnelAssignmentRead])
async def list_assignments(
    service: PersonnelAssignmentServiceDep,
    q: str | None = None,
    personnel_id: int | None = None,
    tm_group_id: int | None = None,
    pl_group_id: int | None = None,
    department_id: int | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await service.list(q, personnel_id, tm_group_id, pl_group_id, department_id, limit, offset)


@router.get("/personnel-assignments/{assignment_id}", response_model=PersonnelAssignmentRead)
async def get_assignment(assignment_id: int, service: PersonnelAssignmentServiceDep):
    return await service.get(assignment_id)


@router.patch("/personnel-assignments/{assignment_id}", response_model=PersonnelAssignmentRead)
async def update_assignment(
    assignment_id: int, payload: PersonnelAssignmentUpdate, service: PersonnelAssignmentServiceDep
):
    return await service.update(assignment_id, payload)


@router.delete("/personnel-assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(assignment_id: int, service: PersonnelAssignmentServiceDep) -> Response:
    await service.delete(assignment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/tm-groups", response_model=TMGroupRead, status_code=status.HTTP_201_CREATED)
async def create_tm(payload: TMGroupCreate, service: OrganizationServiceDep):
    return await service.create_tm(payload)


@router.get("/tm-groups", response_model=list[TMGroupRead])
async def list_tms(
    service: OrganizationServiceDep,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await service.list_tms(q, limit, offset)


@router.get("/tm-groups/{entity_id}", response_model=TMGroupRead)
async def get_tm(entity_id: int, service: OrganizationServiceDep):
    return await service.get_tm(entity_id)


@router.patch("/tm-groups/{entity_id}", response_model=TMGroupRead)
async def update_tm(entity_id: int, payload: TMGroupUpdate, service: OrganizationServiceDep):
    return await service.update_tm(entity_id, payload)


@router.delete("/tm-groups/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tm(entity_id: int, service: OrganizationServiceDep) -> Response:
    await service.delete_tm(entity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/pl-groups", response_model=PLGroupRead, status_code=status.HTTP_201_CREATED)
async def create_pl(payload: PLGroupCreate, service: OrganizationServiceDep):
    return await service.create_pl(payload)


@router.get("/pl-groups", response_model=list[PLGroupRead])
async def list_pls(
    service: OrganizationServiceDep,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await service.list_pls(q, limit, offset)


@router.get("/pl-groups/{entity_id}", response_model=PLGroupRead)
async def get_pl(entity_id: int, service: OrganizationServiceDep):
    return await service.get_pl(entity_id)


@router.patch("/pl-groups/{entity_id}", response_model=PLGroupRead)
async def update_pl(entity_id: int, payload: PLGroupUpdate, service: OrganizationServiceDep):
    return await service.update_pl(entity_id, payload)


@router.delete("/pl-groups/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pl(entity_id: int, service: OrganizationServiceDep) -> Response:
    await service.delete_pl(entity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/departments", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
async def create_department(payload: DepartmentCreate, service: OrganizationServiceDep):
    return await service.create_department(payload)


@router.get("/departments", response_model=list[DepartmentRead])
async def list_departments(
    service: OrganizationServiceDep,
    q: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return await service.list_departments(q, limit, offset)


@router.get("/departments/{entity_id}", response_model=DepartmentRead)
async def get_department(entity_id: int, service: OrganizationServiceDep):
    return await service.get_department(entity_id)


@router.patch("/departments/{entity_id}", response_model=DepartmentRead)
async def update_department(entity_id: int, payload: DepartmentUpdate, service: OrganizationServiceDep):
    return await service.update_department(entity_id, payload)


@router.delete("/departments/{entity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(entity_id: int, service: OrganizationServiceDep) -> Response:
    await service.delete_department(entity_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
