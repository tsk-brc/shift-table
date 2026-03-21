"""
Factories for creating test data.
"""

import factory
from django.contrib.auth.models import User
from .models import (
    Employee,
    ShiftType,
    CompanyHoliday,
    LaborLawSettings,
    Shift,
    Role,
    ShiftTypeRoleMinWorker,
)
from datetime import date, timedelta
import random


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")
    is_staff = True
    is_superuser = True


class RoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Role

    name = factory.Sequence(lambda n: f"役割{n}")


class EmployeeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Employee

    name = factory.Sequence(lambda n: f"従業員{n}")

    @factory.post_generation
    def roles(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for role in extracted:
                self.roles.add(role)


class ShiftTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShiftType

    name = factory.Sequence(lambda n: f"シフト{n}")
    is_work = True
    color = "#ffffff"
    min_workers = 1
    max_workers = None


class WorkShiftTypeFactory(ShiftTypeFactory):
    name = factory.Sequence(lambda n: f"出勤{n}")
    is_work = True


class RestShiftTypeFactory(ShiftTypeFactory):
    name = factory.Sequence(lambda n: f"休み{n}")
    is_work = False


class ShiftTypeRoleMinWorkerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ShiftTypeRoleMinWorker

    shift_type = factory.SubFactory(ShiftTypeFactory)
    role = factory.SubFactory(RoleFactory)
    min_workers = 1


class CompanyHolidayFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CompanyHoliday

    date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=random.randint(1, 30))
    )
    name = factory.Sequence(lambda n: f"会社休日{n}")
    description = factory.Faker("text", max_nb_chars=200)


class LaborLawSettingsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LaborLawSettings

    max_consecutive_work_days = 6
    min_workers = 2


class ShiftFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Shift

    employee = factory.SubFactory(EmployeeFactory)
    date = factory.LazyFunction(
        lambda: date.today() + timedelta(days=random.randint(0, 30))
    )
    shift_type = factory.SubFactory(WorkShiftTypeFactory)


class RestShiftFactory(ShiftFactory):
    shift_type = factory.SubFactory(RestShiftTypeFactory)
