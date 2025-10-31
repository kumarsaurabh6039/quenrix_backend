from django.db import models

# Create your models here.

class Createjob(models.Model):
    jobid = models.AutoField(db_column='jobId', primary_key=True)  # Field name made lowercase.
    jobtitle = models.CharField(db_column='jobTitle', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    job_type = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    reqexp = models.IntegerField(blank=True, null=True)
    company = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    location = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    from_passed_out_year = models.IntegerField(blank=True, null=True)
    to_passed_out_year = models.IntegerField(blank=True, null=True)
    hr_phone = models.CharField(max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    hr_email = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    job_description = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    apply_before_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    posteddate = models.DateTimeField(db_column='postedDate', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'createjob'


