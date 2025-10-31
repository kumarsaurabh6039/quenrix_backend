from django.db import models
from courses.models import Subjects
# Create your models here.

class SubjectsTopicswiseQuestions(models.Model):
    topicquestionid = models.AutoField(db_column='topicQuestionId', primary_key=True)  # Field name made lowercase.
    subjectid = models.ForeignKey('courses.Subjects', models.DO_NOTHING, db_column='subjectId')  # Field name made lowercase.
    topicname = models.CharField(db_column='topicName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    practice_questions_url = models.CharField(max_length=255, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    is_active = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'subjects_topicswise_questions'
