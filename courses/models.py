from django.db import models

# Create your models here.

class Content(models.Model):
    contentid = models.AutoField(db_column='contentId', primary_key=True)  # Field name made lowercase.
    contentname = models.CharField(db_column='contentName', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    contenturl = models.CharField(db_column='contentUrl', max_length=500, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'content'

class Subjects(models.Model):
    subjectid = models.AutoField(db_column='subjectId', primary_key=True)  # Field name made lowercase.
    subjectname = models.CharField(db_column='subjectName', unique=True, max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    created_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'subjects'


class Courses(models.Model):
    courseid = models.AutoField(db_column='courseId', primary_key=True)  # Field name made lowercase.
    coursename = models.CharField(db_column='courseName', unique=True, max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    contentid = models.ForeignKey(Content, models.DO_NOTHING, db_column='contentId', blank=True, null=True)  # Field name made lowercase.
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'courses'
        

class CourseSubjects(models.Model):
    coursesubjectid = models.AutoField(db_column='courseSubjectId', primary_key=True)  # Field name made lowercase.
    courseid = models.ForeignKey('Courses', models.DO_NOTHING, db_column='courseId')  # Field name made lowercase.
    subjectid = models.ForeignKey('courses.Subjects', models.DO_NOTHING, db_column='subjectId')  # Field name made lowercase.
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'course_subjects'
        unique_together = (('courseid', 'subjectid'),)

class SystemSetups(models.Model):
    setupid = models.AutoField(db_column='setupId', primary_key=True)
    subjectid = models.ForeignKey(Subjects, models.DO_NOTHING, db_column='subjectId')
    setupname = models.CharField(db_column='setupName', max_length=100)
    setupdescription = models.TextField(db_column='setupDescription', blank=True, null=True)
    setupurl = models.CharField(db_column='setupUrl', max_length=255, blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'system_setups'
