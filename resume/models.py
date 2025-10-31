from django.db import models
from users.models import Users

# Create your models here.

class PersonalInfo(models.Model):
    personalid = models.AutoField(db_column='personalId', primary_key=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId')  # Field name made lowercase.
    firstname = models.CharField(db_column='firstName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    lastname = models.CharField(db_column='lastName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    dob = models.DateField(blank=True, null=True)
    email = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    phone = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    linkedinid = models.CharField(db_column='linkedinId', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    githubid = models.CharField(db_column='githubId', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'personal_info'

class EducationInfo(models.Model):
    educationid = models.AutoField(db_column='educationId', primary_key=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId')  # Field name made lowercase.
    qualification_type = models.CharField(max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    qualification = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    joined_on = models.DateField(blank=True, null=True)
    left_on = models.DateField(blank=True, null=True)
    marks = models.CharField(max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    marking_system = models.CharField(max_length=20, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    university = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'education_info'


class TechStack(models.Model):
    tech_stackid = models.AutoField(db_column='tech_stackId', primary_key=True)  # Field name made lowercase.
    techname = models.CharField(db_column='techName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'tech_stack'


class ProjectTechStack(models.Model):
    projecttechid = models.AutoField(db_column='projectTechId', primary_key=True)  # Field name made lowercase.
    projectid = models.ForeignKey('Projects', models.DO_NOTHING, db_column='projectId', blank=True, null=True)  # Field name made lowercase.
    tech_stackid = models.ForeignKey('TechStack', models.DO_NOTHING, db_column='tech_stackId', blank=True, null=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'project_tech_stack'


class Projects(models.Model):
    projectid = models.AutoField(db_column='projectId', primary_key=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId')  # Field name made lowercase.
    projectname = models.CharField(db_column='projectName', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    githublink = models.CharField(db_column='githubLink', max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'projects'


class ProjectDescriptions(models.Model):
    projectdescid = models.AutoField(db_column='projectDescId', primary_key=True)  # Field name made lowercase.
    projectid = models.ForeignKey('Projects', models.DO_NOTHING, db_column='projectId', blank=True, null=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId', blank=True, null=True)  # Field name made lowercase.
    description = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'project_descriptions'


class SkillCategories(models.Model):
    categoryid = models.AutoField(db_column='categoryId', primary_key=True)  # Field name made lowercase.
    categoryname = models.CharField(db_column='categoryName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'skill_categories'

class ProficiencyLevels(models.Model):
    proficiencyid = models.AutoField(db_column='proficiencyId', primary_key=True)  # Field name made lowercase.
    levelname = models.CharField(db_column='levelName', max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'proficiency_levels'


class SkillsInfo(models.Model):
    skillinfoid = models.AutoField(db_column='skillInfoId', primary_key=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId')  # Field name made lowercase.
    skillmasterid = models.ForeignKey('SkillsMaster', models.DO_NOTHING, db_column='skillMasterId', blank=True, null=True)  # Field name made lowercase.
    proficiencyid = models.ForeignKey(ProficiencyLevels, models.DO_NOTHING, db_column='proficiencyId', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'skills_info'


class SkillsMaster(models.Model):
    skillmasterid = models.AutoField(db_column='skillMasterId', primary_key=True)  # Field name made lowercase.
    skillname = models.CharField(db_column='skillName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    categoryid = models.ForeignKey(SkillCategories, models.DO_NOTHING, db_column='categoryId', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'skills_master'


class Experience(models.Model):
    experienceid = models.AutoField(db_column='experienceId', primary_key=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId')  # Field name made lowercase.
    position = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    company = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    joined_on = models.DateField(blank=True, null=True)
    left_on = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'experience'


class Expwork(models.Model):
    expworkid = models.AutoField(db_column='expWorkId', primary_key=True)  # Field name made lowercase.
    experienceid = models.ForeignKey(Experience, models.DO_NOTHING, db_column='experienceId', blank=True, null=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId', blank=True, null=True)  # Field name made lowercase.
    worked_on = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'expwork'