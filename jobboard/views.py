################################################################################ 
# JobBoard: a simple Django-based job board
# Copyright (c) 2009, Imaginary Landscape
# All rights reserved.
#                    
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#     * Redistributions of source code must retain the above copyright notice, 
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the 
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Imaginary Landscape nor the names of its
#       contributors may be used to endorse or promote products derived from 
#       this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
################################################################################

"""
Views for the JobBoard application.
"""

import datetime

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, Context, loader
from django.views.generic.list_detail import object_list

from jobboard import models
from jobboard.forms import JobPost
from jobboard.forms import ApplicantPost
from jobboard.models import calculate_post_expires


def index(request):
    """
    Index page.

    Displays a few job postings and a few applicant postings.  The
    number of these are determined by the application settings
    JOBBOARD_JOBS_ON_INDEX and JOBBOARD_APPLICANTS_ON_INDEX
    respectively.
    """
    num_jobs = settings.JOBBOARD_JOBS_ON_INDEX
    num_applicants = settings.JOBBOARD_APPLICANTS_ON_INDEX

    jobs = models.JobPost.objects.filter(
        approved=True,
        expiration_date__gte=datetime.date.today())
    jobs = jobs[:num_jobs]

    applicants = models.ApplicantPost.objects.filter(
        approved=True,
        expiration_date__gte=datetime.date.today())
    applicants = applicants[:num_applicants]

    return render_to_response(
        'jobboard/index.html',
        {'jobs': jobs,
         'applicants': applicants},
        context_instance=RequestContext(request))


def job_list(request):
    """
    Displays all non-expired and approved job postings, paginated.

    The number of applicants per page is determined by the application
    config's variable "jobs_per_page".
    """
    all_jobs = models.JobPost.objects.filter(
        approved=True,
        expiration_date__gte=datetime.date.today())

    return object_list(
        request=request, queryset=all_jobs,
        paginate_by=settings.JOBBOARD_JOBS_PER_PAGE,
        template_object_name='job')


def applicant_list(request):
    """
    Displays all non-expired and approved applicant postings,
    paginated.

    The number of applicants per page is determined by the application
    config's variable "applicants_per_page".
    """
    all_applicants = models.ApplicantPost.objects.filter(
        approved=True,
        expiration_date__gte=datetime.date.today())

    return object_list(
        request=request, queryset=all_applicants,
        paginate_by=settings.JOBBOARD_APPLICANTS_PER_PAGE,
        template_object_name='applicant')


def submit_job(request):
    """
    Provides the user-facing form for job posting and submission
    processing of such posted data.

    Upon a GET request, the form is shown for user submission.  Upon
    POST, the form data will be validated, and upon successful
    validation, will be saved as a models.JobPost entry in the
    database.  The expiration date will be set to the number of days
    in the future from today specified by JOBBOARD_POSTS_EXPIRE_DAYS.

    If there are any models.NotifyEmail entries, an email will be sent
    to those recipients notifying them of the submission (if there are
    no entries, an email will not be sent).  The from address will be
    determined by the email address specified by JOBBOARD_FROM_EMAIL.

    Upon successful submission, the user will be redirected to a
    "thank you" page.
    """
    if settings.CAPTCHA:
        captcha = True
    else:
        captcha = False
    if request.method == 'POST':
        job_form = JobPost(request.POST)

        if not job_form.is_valid():
            return render_to_response(
                'jobboard/submit_job.html',
                {'job_form': job_form,
                 'captcha': captcha,
                },
                context_instance=RequestContext(request))

        job_data = job_form.cleaned_data
        job_post = models.JobPost()

        job_post.posters_name = job_data['posters_name']
        job_post.work_hours = job_data['work_hours']
        job_post.description = job_data['description']
        job_post.email = job_data['email']
        job_post.contact_information = job_data['contact_information']
        job_post.position = job_data['position']

        job_post.expiration_date = calculate_post_expires()
        job_post.when_posted = datetime.datetime.now()

        job_post.save()

        # if there are email addresses to notify, send the alert email
        if models.NotifyEmail.objects.count():
            email_template = loader.get_template(
                'jobboard/jobpost_email.txt')
            email_subject_template = loader.get_template(
                'jobboard/jobpost_email_subject.txt')

            body = email_template.render(Context({'job': job_post}))
            subject = email_subject_template.render(
                Context({'job': job_post})).strip()
            recipients = [
                notify.email for notify in models.NotifyEmail.objects.all()]
            send_mail(
                subject, body, settings.JOBBOARD_FROM_EMAIL,
                recipients, fail_silently=False)

        return HttpResponseRedirect(
            reverse('jobboard_thank_you'))
    else:
        job_form = JobPost()
        print str(job_form.as_table())
        return render_to_response(
            'jobboard/submit_job.html',
            {'job_form': job_form,
             'captcha': captcha,
            },
            context_instance=RequestContext(request))


def submit_applicant(request):
    """
    Provides the user-facing form for applicant posting and submission
    processing of such posted data.

    Upon a GET request, the form is shown for user submission.  Upon
    POST, the form data will be validated, and upon successful
    validation, will be saved as a models.ApplicantPost entry in the
    database.  The expiration date will be set to the number of days
    in the future from today specified by the
    JOBBOARD_POSTS_EXPIRE_DAYS setting.

    If there are any models.NotifyEmail entries, an email will be sent
    to those recipients notifying them of the submission (if there are
    no entries, an email will not be sent).  The from address will be
    determined by the email address set up in the JOBBOARD_FROM_EMAIL
    setting.

    Upon successful submission, the user will be redirected to a
    "thank you" page.
    """
    if settings.CAPTCHA:
        captcha = True
    else:
        captcha = False
    if request.method == 'POST':
        applicant_form = ApplicantPost(request.POST)

        if not applicant_form.is_valid():
            return render_to_response(
                'jobboard/submit_applicant.html',
                {'applicant_form': applicant_form,
                 'captcha': captcha,
                },
                context_instance=RequestContext(request))

        applicant_data = applicant_form.cleaned_data
        applicant_post = models.ApplicantPost()

        applicant_post.first_name = applicant_data['first_name']
        applicant_post.last_name = applicant_data['last_name']
        applicant_post.phone_number = applicant_data['phone_number']
        applicant_post.email = applicant_data['email']
        applicant_post.resume = applicant_data['resume']
        applicant_post.full_time = applicant_data.get('full_time', False)
        applicant_post.part_time = applicant_data.get('part_time', False)

        applicant_post.expiration_date = calculate_post_expires()
        applicant_post.when_posted = datetime.datetime.now()
        applicant_post.position = applicant_data['position']

        applicant_post.save()

        # if there are email addresses to notify, send the alert email
        if models.NotifyEmail.objects.count():
            email_template = loader.get_template(
                'jobboard/applicantpost_email.txt')
            email_subject_template = loader.get_template(
                'jobboard/applicantpost_email_subject.txt')

            body = email_template.render(
                Context({'applicant': applicant_post}))
            subject = email_subject_template.render(
                Context({'applicant': applicant_post})).strip()
            recipients = [
                notify.email for notify in models.NotifyEmail.objects.all()]
            send_mail(
                subject, body, settings.JOBBOARD_FROM_EMAIL,
                recipients, fail_silently=False)

        return HttpResponseRedirect(
            reverse('jobboard_thank_you'))
    else:
        applicant_form = ApplicantPost()
        return render_to_response(
            'jobboard/submit_applicant.html',
            {'applicant_form': applicant_form,
             'captcha': captcha,
            },
            context_instance=RequestContext(request))


def thank_you(request):
    """
    Just returns a rendered "thank you" page.
    """
    return render_to_response(
        'jobboard/thank_you.html', {},
        context_instance=RequestContext(request))
