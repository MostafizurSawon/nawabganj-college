from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin, Group, Permission
)
from django.db import models
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Phone number must be provided')

        phone_number = str(phone_number).strip()
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)  # PK তৈরি হবে
        return user

    def create_superuser(self, phone_number, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError('Superuser must have is_staff=True.')
        if not extra_fields.get('is_superuser'):
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)


def _get_yearly_base():
    """
    2025 -> 2500000, 2026 -> 2600000, ...
    """
    year = timezone.now().year
    return (year % 100) * 100000


class User(AbstractBaseUser, PermissionsMixin):
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    ROLE_CHOICES = (
        ('student', 'Student'),
        ('accountant', 'Accountant'),
        ('headteacher', 'Head Teacher'),
        ('teacher', 'Teacher'),
        ('assistant', 'Assistant'),
        ('sub_admin', 'Sub Admin'),
        ('admin', 'Admin'),
        ('master_admin', 'Master Admin'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    # OTP fields
    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    # Rate limiting
    otp_last_sent = models.DateTimeField(blank=True, null=True)
    otp_send_count = models.PositiveIntegerField(default=0)
    otp_send_count_reset = models.DateTimeField(blank=True, null=True)

    # === New field: Customer-style ID ===
    cus_id = models.PositiveBigIntegerField(
        unique=True, blank=True, null=True, db_index=True, editable=False
    )

    # Custom config
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    # Avoid conflicts with auth.User
    groups = models.ManyToManyField(
        Group,
        related_name="customuser_set",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="customuser_permissions",
        blank=True
    )

    def __str__(self):
        return self.phone_number

    def save(self, *args, **kwargs):
        """
        প্রথম সেভে PK (id) তৈরি হলে, cus_id = (YY*100000) + id সেট করে দেই
        যেমন: 2025 ও id=50 -> 2500000 + 50 = 2500050
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)  # আগে PK নিশ্চিত করা

        # শুধুমাত্র তখনই সেট করুন যখন cus_id এখনো ফাঁকা
        if self.cus_id is None:
            base = _get_yearly_base()
            self.cus_id = base + self.id
            super().save(update_fields=['cus_id'])