from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmptyToNoneModel(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def empty_text_to_none(cls, value):
        return None if isinstance(value, str) and not value.strip() else value


class OrganizationNameModel(BaseModel):
    @field_validator("name", mode="before", check_fields=False)
    @classmethod
    def normalize_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class PersonnelCreate(EmptyToNoneModel):
    w3_account: str = Field(min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    employee_id: str | None = Field(default=None, min_length=1, max_length=32)


class PersonnelUpdate(EmptyToNoneModel):
    w3_account: str | None = Field(default=None, min_length=1, max_length=64)
    name: str | None = Field(default=None, min_length=1, max_length=100)
    employee_id: str | None = Field(default=None, min_length=1, max_length=32)


class PersonnelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    w3_account: str
    name: str | None
    employee_id: str | None


class OrganizationSummary(BaseModel):
    id: int
    name: str


class PersonnelAssignmentCreate(EmptyToNoneModel):
    personnel_id: int
    tm_group_id: int | None = None
    pl_group_id: int | None = None
    department_id: int | None = None
    start_time: date | None = None
    end_time: date | None = None
    creator: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class PersonnelAssignmentUpdate(EmptyToNoneModel):
    personnel_id: int | None = None
    tm_group_id: int | None = None
    pl_group_id: int | None = None
    department_id: int | None = None
    start_time: date | None = None
    end_time: date | None = None
    creator: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class PersonnelAssignmentRead(BaseModel):
    id: int
    personnel: PersonnelRead
    tm_group: OrganizationSummary | None
    pl_group: OrganizationSummary | None
    department: OrganizationSummary | None
    start_time: date | None
    end_time: date | None
    creator: str | None
    insert_time: datetime
    notes: str | None


class TMGroupCreate(OrganizationNameModel):
    name: str = Field(min_length=1, max_length=100)
    leader_personnel_id: int | None = None


class TMGroupUpdate(OrganizationNameModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    leader_personnel_id: int | None = None


class TMGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    leader_personnel_id: int | None


class PLGroupCreate(OrganizationNameModel):
    name: str = Field(min_length=1, max_length=100)
    leader_personnel_id: int | None = None


class PLGroupUpdate(OrganizationNameModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    leader_personnel_id: int | None = None


class PLGroupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    leader_personnel_id: int | None


class DepartmentCreate(OrganizationNameModel):
    name: str = Field(min_length=1, max_length=200)


class DepartmentUpdate(OrganizationNameModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
