from django.core.validators import MinValueValidator
from django.db import models


class User(models.Model):
    username = models.CharField(max_length=32)
    chat_id = models.BigIntegerField()
    business_card = models.TextField()
    firstname = models.CharField(max_length=100)
    secondname = models.CharField(max_length=100)


class Question(models.Model):
    from_who = models.ForeignKey(
        User,
        related_name='question_from',
        on_delete=models.CASCADE,
    )
    to_who = models.ForeignKey(
        User,
        related_name='question_to',
        on_delete=models.CASCADE,
    )
    text = models.TextField()
    communication_request = models.BooleanField(default=False)
    alert = models.BooleanField(default=False)
    time = models.DateTimeField(auto_now_add=True)


class Event(models.Model):
    date = models.DateField()
    title = models.CharField(max_length=100)
    users = models.ManyToManyField(User)


class Speech(models.Model):
    start_time = models.DateTimeField(blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    event = models.ForeignKey(
        Event,
        related_name='speeches',
        on_delete=models.CASCADE,
    )
    speaker = models.ForeignKey(
        User,
        related_name='speeches',
        on_delete=models.CASCADE,
    )


class Donation(models.Model):
    user = models.ForeignKey(
        User,
        related_name='donations',
        on_delete=models.CASCADE,
    )
    summ = models.FloatField(validators=[MinValueValidator(0)])
    time = models.DateTimeField(auto_now_add=True)


class Alert(models.Model):
    text = models.TextField()
    send = models.BooleanField(default=False)
