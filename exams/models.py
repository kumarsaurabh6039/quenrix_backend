from django.db import models
from batches.models import Batches
from courses.models import Courses

# Create your models here.



class ExamAttempts(models.Model):
    attemptid = models.AutoField(db_column='attemptId', primary_key=True)  # Field name made lowercase.
    examid = models.ForeignKey('Exams', models.DO_NOTHING, db_column='examId', blank=True, null=True)  # Field name made lowercase.
    userid = models.ForeignKey('users.Users', models.DO_NOTHING, db_column='userId', blank=True, null=True)  # Field name made lowercase.
    attemptdate = models.DateTimeField(db_column='attemptDate', blank=True, null=True)  # Field name made lowercase.
    total_score = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    ai_evaluated = models.BooleanField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exam_attempts'


class ExamBatches(models.Model):
    exambatchid = models.AutoField(db_column='examBatchId', primary_key=True)  # Field name made lowercase.
    examid = models.ForeignKey('Exams', models.DO_NOTHING, db_column='examId', blank=True, null=True)  # Field name made lowercase.
    batchid = models.ForeignKey(Batches, models.DO_NOTHING, db_column='batchId', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'exam_batches'


class ExamResults(models.Model):
    resultid = models.AutoField(db_column='resultId', primary_key=True)  # Field name made lowercase.
    attemptid = models.ForeignKey(ExamAttempts, models.DO_NOTHING, db_column='attemptId', blank=True, null=True)  # Field name made lowercase.
    score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    total_mcq_score = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    total_descriptive_score = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    total_coding_score = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    final_score = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exam_results'


class Exams(models.Model):
    examid = models.AutoField(db_column='examId', primary_key=True)  # Field name made lowercase.
    examname = models.CharField(db_column='examName', max_length=100, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    courseid = models.ForeignKey(Courses, models.DO_NOTHING, db_column='courseId', blank=True, null=True)  # Field name made lowercase.
    batchid = models.ForeignKey(Batches, models.DO_NOTHING, db_column='batchId', blank=True, null=True)  # Field name made lowercase.
    subjectid = models.ForeignKey('courses.Subjects', models.DO_NOTHING, db_column='subjectId', blank=True, null=True)  # Field name made lowercase.
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'exams'


class Options(models.Model):
    optionid = models.AutoField(db_column='optionId', primary_key=True)  # Field name made lowercase.
    questionid = models.ForeignKey('Questions', models.DO_NOTHING, db_column='questionId', blank=True, null=True)  # Field name made lowercase.
    optiontext = models.CharField(db_column='optionText', max_length=500, db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    iscorrect = models.BooleanField(db_column='isCorrect', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'options'



class QuestionTypes(models.Model):
    questiontypeid = models.AutoField(db_column='questionTypeId', primary_key=True)  # Field name made lowercase.
    typename = models.CharField(db_column='typeName', max_length=50, db_collation='SQL_Latin1_General_CP1_CI_AS')  # Field name made lowercase.
    is_active = models.BooleanField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'question_types'


class Questions(models.Model):
    questionid = models.AutoField(db_column='questionId', primary_key=True)  # Field name made lowercase.
    examid = models.ForeignKey(Exams, models.DO_NOTHING, db_column='examId', blank=True, null=True)  # Field name made lowercase.
    questiontypeid = models.ForeignKey(QuestionTypes, models.DO_NOTHING, db_column='questionTypeId', blank=True, null=True)  # Field name made lowercase.
    questiontext = models.TextField(db_column='questionText', db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)  # Field name made lowercase.
    points = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'questions'


class StudentAnswers(models.Model):
    studentanswerid = models.AutoField(db_column='studentAnswerId', primary_key=True)  # Field name made lowercase.
    attemptid = models.ForeignKey(ExamAttempts, models.DO_NOTHING, db_column='attemptId', blank=True, null=True)  # Field name made lowercase.
    questionid = models.ForeignKey(Questions, models.DO_NOTHING, db_column='questionId', blank=True, null=True)  # Field name made lowercase.
    selectedoptionid = models.ForeignKey(Options, models.DO_NOTHING, db_column='selectedOptionId', blank=True, null=True)  # Field name made lowercase.
    descriptive_answer = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    code_answer = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    ai_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    ai_feedback = models.TextField(db_collation='SQL_Latin1_General_CP1_CI_AS', blank=True, null=True)
    evaluated = models.BooleanField(blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    is_correct = models.BooleanField(blank=True, null=True)
    points_earned = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'student_answers'

