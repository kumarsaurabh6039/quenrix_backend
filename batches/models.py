from django.db import models
from users.models import Users
from courses.models import Courses

# Create your models here.

class Batches(models.Model):
    batchid = models.AutoField(db_column='batchId', primary_key=True)  # Field name made lowercase.
    batchname = models.CharField(db_column='batchName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    courseid = models.ForeignKey('courses.Courses', models.DO_NOTHING, db_column='courseId')  # Field name made lowercase.
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'batches'


class TrainerBatches(models.Model):
    trainerbatchid = models.AutoField(db_column='trainerBatchId', primary_key=True)  # Field name made lowercase.
    batchid = models.ForeignKey(Batches, models.DO_NOTHING, db_column='batchId', blank=True, null=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'trainer_batches'


class StudentBatches(models.Model):
    studentbatchid = models.AutoField(db_column='studentBatchId', primary_key=True)  # Field name made lowercase.
    batchid = models.ForeignKey(Batches, models.DO_NOTHING, db_column='batchId')  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'student_batches'


