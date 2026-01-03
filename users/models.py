from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.hashers import make_password, check_password
from django.db.models import IntegerField
from django.db.models.functions import Cast, Substr


class Roles(models.Model):
    roleid = models.AutoField(db_column='roleId', primary_key=True)
    rolename = models.CharField(db_column='roleName', max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS')
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'roles'

    def __str__(self):
        return self.rolename or f"Role {self.roleid}"


class Users(models.Model):
    userid = models.CharField(
        db_column='userId', primary_key=True, max_length=20,
        db_collation='SQL_Latin1_General_CP1_CI_AS'
    )
    username = models.CharField(
        max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS',
        blank=True, null=True
    )
    password = models.CharField(
        max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS',
        blank=True, null=True
    )
    roleid = models.ForeignKey(
        Roles, models.DO_NOTHING, db_column='roleId', blank=True, null=True
    )
    is_active = models.BooleanField(blank=True, null=True, default=True)

    # ✅ ADD THESE PROPERTIES FOR COMPATIBILITY
    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    class Meta:
        managed = False  # keep since table already exists
        db_table = 'users'

    def __str__(self):
        return self.username or self.userid

    def clean(self):
        """Ensure username is a valid email"""
        super().clean()
        if self.username:
            try:
                validate_email(self.username)
            except ValidationError:
                raise ValidationError({'username': 'Enter a valid email address.'})

    def set_password(self, raw_password):
        """Hashes password securely before saving"""
        if raw_password:
            self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """Validates a raw password against stored hash"""
        return check_password(raw_password, self.password)

    def save(self, *args, **kwargs):
        """Auto-generate userId like USR001, USR002..."""
        if not self.userid:
            last_user = (
                Users.objects.filter(userid__startswith='USR')
                .annotate(num_part=Cast(Substr('userid', 4), IntegerField()))
                .order_by('-num_part')
                .first()
            )

            last_number = int(last_user.userid[3:]) if last_user else 0
            new_number = last_number + 1
            self.userid = f"USR{new_number:03d}"
        if self.password and not self.password.startswith('pbkdf2_'):
            self.password = make_password(self.password)

        # Validate email format
        self.full_clean()
        super().save(*args, **kwargs)