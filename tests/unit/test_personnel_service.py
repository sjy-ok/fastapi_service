from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.exc import IntegrityError

from app.core.exceptions import BadRequestError, ConflictError
from app.modules.personnels.model import Personnel, PersonnelAssignment
from app.modules.personnels.schemas import PersonnelAssignmentCreate, PersonnelCreate
from app.modules.personnels.service import PersonnelAssignmentService, PersonnelService


async def test_personnel_create_and_duplicate():
    db = Mock(commit=AsyncMock(), rollback=AsyncMock())
    repository = Mock(
        get_by_w3_account_exact=AsyncMock(return_value=None),
        get_by_employee_id=AsyncMock(return_value=None),
        add=AsyncMock(),
    )
    service = PersonnelService(db, repository)
    result = await service.create(PersonnelCreate(w3_account="u", name="User", employee_id="E"))
    assert result.name == "User"
    repository.get_by_w3_account_exact.return_value = Personnel(id=1, w3_account="u", name="User", employee_id="E")
    with pytest.raises(ConflictError):
        await service.create(PersonnelCreate(w3_account="u", name="Other", employee_id="E2"))


async def test_personnel_delete_integrity_error_becomes_conflict():
    db = Mock(commit=AsyncMock(side_effect=IntegrityError("delete", {}, Exception())), rollback=AsyncMock())
    entity = Personnel(id=1, w3_account="u", name="User", employee_id="E")
    repository = Mock(get_by_id=AsyncMock(return_value=entity), delete=AsyncMock())
    with pytest.raises(ConflictError, match="in use"):
        await PersonnelService(db, repository).delete(1)
    db.rollback.assert_awaited_once()


async def test_assignment_default_time_and_validation():
    db = Mock(commit=AsyncMock(), rollback=AsyncMock())

    async def add_with_id(entity):
        entity.id = 1

    assignments = Mock(add=AsyncMock(side_effect=add_with_id), get_by_id=AsyncMock())
    personnel = Personnel(id=1, w3_account="u", name="User", employee_id="E")
    personnels = Mock(get_by_id=AsyncMock(return_value=personnel))
    organizations = Mock()
    service = PersonnelAssignmentService(db, assignments, personnels, organizations)
    assignments.get_by_id.side_effect = lambda assignment_id: (
        PersonnelAssignment(id=assignment_id, personnel_id=1, start_time=None, insert_time=datetime.now(UTC)),
        personnel,
        None,
        None,
        None,
    )
    result = await service.create(PersonnelAssignmentCreate(personnel_id=1))
    assert result.start_time is None
    service._validate_time(date(2025, 2, 25), date(2025, 2, 25))
    with pytest.raises(BadRequestError, match="End date"):
        service._validate_time(date(2025, 2, 26), date(2025, 2, 25))
