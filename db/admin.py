from django.contrib import admin
from .models import User, Question, Event, Speech, Donation, Alert

admin.site.register(User)
admin.site.register(Question)
admin.site.register(Event)
admin.site.register(Speech)
admin.site.register(Donation)
admin.site.register(Alert)