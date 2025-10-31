from django.db import models
from users.models import Users
from courses.models import Subjects

# Create your models here.

class Doubts(models.Model):
    doubtid = models.AutoField(db_column='doubtId', primary_key=True)  # Field name made lowercase.
    subjectid = models.ForeignKey('courses.Subjects', models.DO_NOTHING, db_column='subjectId')  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId')  # Field name made lowercase.
    doubttext = models.TextField(db_column='doubtText', db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    created_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'doubts'
        

class Solutions(models.Model):
    solutionid = models.AutoField(db_column='solutionId', primary_key=True)  # Field name made lowercase.
    doubtid = models.ForeignKey(Doubts, models.DO_NOTHING, db_column='doubtId')  # Field name made lowercase.
    solution = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS')
    created_at = models.DateTimeField(blank=True, null=True)
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId', blank=True, null=True)  # Field name made lowercase.
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'solutions'
