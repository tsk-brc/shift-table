from django.db import models

# Create your models here.

class Employee(models.Model):
    name = models.CharField('氏名', max_length=100)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '従業員'
        verbose_name_plural = '従業員'

class ShiftType(models.Model):
    name = models.CharField('シフト種別名', max_length=50, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'シフト種別'
        verbose_name_plural = 'シフト種別'

class CompanyHoliday(models.Model):
    date = models.DateField('日付', unique=True)
    name = models.CharField('休日名', max_length=100)
    description = models.TextField('説明', blank=True)

    def __str__(self):
        return f"{self.date} {self.name}"

    class Meta:
        verbose_name = '会社休日'
        verbose_name_plural = '会社休日'
        ordering = ['date']

class Shift(models.Model):
    employee = models.ForeignKey(Employee, verbose_name='従業員', on_delete=models.CASCADE)
    date = models.DateField('日付')
    shift_type = models.ForeignKey(ShiftType, verbose_name='シフト種別', on_delete=models.PROTECT)

    class Meta:
        unique_together = ('employee', 'date')
        verbose_name = 'シフト'
        verbose_name_plural = 'シフト'

    def __str__(self):
        return f"{self.date} {self.employee.name} {self.shift_type.name}"
