from django.db import models
from users.models import Users
from courses.models import Courses

class Batches(models.Model):
    batchid = models.AutoField(db_column='batchId', primary_key=True) 
    batchname = models.CharField(db_column='batchName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS') 
    courseid = models.ForeignKey('courses.Courses', models.DO_NOTHING, db_column='courseId') 
    is_active = models.BooleanField(blank=True, null=True)
    
    # --- New Fields by saurabh ---
    start_date = models.DateField(db_column='startDate', blank=True, null=True)
    timing = models.CharField(db_column='timing', max_length=100, blank=True, null=True) # e.g., "10:00 AM - 12:00 PM"
    mode = models.CharField(db_column='mode', max_length=50, blank=True, null=True) # e.g., "Online", "Offline", "Hybrid"

    class Meta:
        managed = False
        db_table = 'batches'


class TrainerBatches(models.Model):
    trainerbatchid = models.AutoField(db_column='trainerBatchId', primary_key=True)
    batchid = models.ForeignKey(Batches, models.DO_NOTHING, db_column='batchId', blank=True, null=True)
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'trainer_batches'


class StudentBatches(models.Model):
    studentbatchid = models.AutoField(db_column='studentBatchId', primary_key=True)
    batchid = models.ForeignKey(Batches, models.DO_NOTHING, db_column='batchId')
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId')

    class Meta:
        managed = False
        db_table = 'student_batches'