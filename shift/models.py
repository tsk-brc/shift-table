from django.db import models

# Create your models here.

class Employee(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ShiftType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Shift(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField()
    shift_type = models.ForeignKey(ShiftType, on_delete=models.PROTECT)

    class Meta:
        unique_together = ('employee', 'date')

    def __str__(self):
        return f"{self.date} {self.employee.name} {self.shift_type.name}"
