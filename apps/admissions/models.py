from django.db import models

# Create your models here.
class HscFeeType(models.Model):
    fee_type = models.CharField(max_length=50, unique=True)
    amount = models.IntegerField()

    def __str__(self):
        return f"{self.fee_type} - {self.amount} BDT"



class HscSession(models.Model):
    session = models.CharField(max_length=9, unique=True)
    fee = models.ForeignKey(HscFeeType, on_delete=models.CASCADE, related_name='hsc_sessions_fee', null=True, blank=True)

    def __str__(self):
        return f"{self.session}"


class HscAdmissionScience(models.Model):
    program = models.CharField(max_length=20, default='HSC', editable=False)
    type = models.CharField(max_length=10, default='Science', editable=False)
    ssc_roll = models.IntegerField(unique=True)
    hsc_session = models.ForeignKey(HscSessionForPayment, on_delete=models.CASCADE)
    class_roll = models.IntegerField(unique=True)
    merit_position = models.IntegerField()
    name = models.CharField(max_length=100)
    name_bangla = models.CharField(max_length=100, null=True, blank=True)
    mobile = models.CharField(max_length=11, validators=[numeric_validator])
    blood_group = models.CharField(max_length=3, choices=[
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
    ])
    birth_certificate_no = models.CharField(max_length=50)
    birthdate = models.DateField()
    marital_status = models.CharField(max_length=10, choices=[
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
    ])
    gender = models.CharField(max_length=10, choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ])
    nationality = models.CharField(max_length=50)
    religion = models.CharField(max_length=20, choices=[
        ('Islam', 'Islam'),
        ('Hindu', 'Hindu'),
        ('Christian', 'Christian'),
        ('Buddhist', 'Buddhist'),
        ('Other', 'Other'),
    ])
    photo = models.ImageField(upload_to='hsc-science/')

    def __str__(self):
        return f"Name: {self.name} | Group: Science | Class Roll: {self.class_roll} | Session: {self.hsc_session.session}"
