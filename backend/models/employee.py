"""
NoblePort Employee Model

Internal staff and field crews. Roles map to the Field Operations layer's
user types (PMs, superintendents, foremen, sales inspectors).
"""

from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DateTime, Enum, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.config.database import Base
from backend.models.base import TimestampMixin, UUIDMixin


class EmployeeRole(str, PyEnum):
    PROJECT_MANAGER = "project_manager"
    SUPERINTENDENT = "superintendent"
    FOREMAN = "foreman"
    SALES_INSPECTOR = "sales_inspector"
    ESTIMATOR = "estimator"
    ADMIN = "admin"
    EXECUTIVE = "executive"
    OTHER = "other"


class EmployeeStatus(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"


class Employee(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "employees"

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    role: Mapped[EmployeeRole] = mapped_column(
        Enum(EmployeeRole), default=EmployeeRole.OTHER, nullable=False
    )
    status: Mapped[EmployeeStatus] = mapped_column(
        Enum(EmployeeStatus), default=EmployeeStatus.ACTIVE, nullable=False
    )

    hire_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    hourly_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    labor_burden_rate: Mapped[float | None] = mapped_column(Float, nullable=True)

    certifications: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Employee {self.first_name} {self.last_name} ({self.role.value})>"
