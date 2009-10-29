from django.conf.urls.defaults import patterns

urlpatterns = patterns(
    'jobboard.views',
    (r'^$', 'index', {}, 'jobboard_index'),
    (r'^jobs/$', 'job_list', {}, 'jobboard_job_list'),
    (r'^submit_job/$', 'submit_job', {}, 'jobboard_submit_job'),
    (r'^applicants/$', 'applicant_list', {}, 'jobboard_applicant_list'),
    (r'^submit_applicant/$', 'submit_applicant',
     {}, 'jobboard_submit_applicant'),
    (r'^thank_you/$', 'thank_you', {}, 'jobboard_thank_you'),
)
