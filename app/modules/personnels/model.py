from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Personnel(Base):
    __tablename__ = "personnels"
    id: Mapped[int] = mapped_column(primary_key=True)
    w3_account: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employee_id: Mapped[str | None] = mapped_column(String(32), unique=True, index=True, nullable=True)


class TMGroup(Base):
    __tablename__ = "tm_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    leader_personnel_id: Mapped[int | None] = mapped_column(ForeignKey("personnels.id"), nullable=True, index=True)


class PLGroup(Base):
    __tablename__ = "pl_groups"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    leader_personnel_id: Mapped[int | None] = mapped_column(ForeignKey("personnels.id"), nullable=True, index=True)


class Department(Base):
    __tablename__ = "departments"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)


class PersonnelAssignment(Base):
    __tablename__ = "personnel_assignments"
    id: Mapped[int] = mapped_column(primary_key=True)
    personnel_id: Mapped[int] = mapped_column(ForeignKey("personnels.id"), index=True)
    tm_group_id: Mapped[int | None] = mapped_column(ForeignKey("tm_groups.id"), nullable=True)
    pl_group_id: Mapped[int | None] = mapped_column(ForeignKey("pl_groups.id"), nullable=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    start_time: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_time: Mapped[date | None] = mapped_column(Date, nullable=True)
    creator: Mapped[str | None] = mapped_column(String(64), nullable=True)
    insert_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
