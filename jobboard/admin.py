from django.contrib import admin

from jobboard import models


class JobPostAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Approval Status',
         {'fields': ['approved']}),
        ('Dates',
         {'fields': ['when_posted', 'expiration_date']}),
        ('Details',
         {'fields': ['posters_name', 'work_hours',
                     'description', 'position',
                     'email', 'contact_information']}))
    list_filter = ['approved']
    list_display = [
        'posters_name', 'position',
        'when_posted', 'expiration_date',
        'approved']


class ApplicantPostAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Approval Status',
         {'fields': ['approved']}),
        ('Dates',
        {'fields': ['when_posted', 'expiration_date']}),
        ('Details',
         {'fields': ['first_name', 'last_name',
                     'phone_number', 'email',
                     'position', 'resume',
                     'full_time', 'part_time']}))
    list_filter = ['approved']
    list_display = [
        'full_name', 'position',
        'when_posted', 'expiration_date',
        'approved']


admin.site.register(models.NotifyEmail)
admin.site.register(models.Position)
admin.site.register(models.JobPost, JobPostAdmin)
admin.site.register(models.ApplicantPost, ApplicantPostAdmin)
