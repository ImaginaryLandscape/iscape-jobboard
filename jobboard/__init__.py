from django.conf import settings


if not hasattr(settings, 'JOBBOARD_FROM_EMAIL'):
    settings.JOBBOARD_FROM_EMAIL = settings.SERVER_EMAIL

if not hasattr(settings, 'JOBBOARD_POSTS_EXPIRE_DAYS'):
    settings.JOBBOARD_POSTS_EXPIRE_DAYS = 30

if not hasattr(settings, 'JOBBOARD_APPLICANTS_PER_PAGE'):
    settings.JOBBOARD_APPLICANTS_PER_PAGE = 15

if not hasattr(settings, 'JOBBOARD_JOBS_PER_PAGE'):
    settings.JOBBOARD_JOBS_PER_PAGE = 15

if not hasattr(settings, 'JOBBOARD_APPLICANTS_ON_INDEX'):
    settings.JOBBOARD_APPLICANTS_ON_INDEX = 5

if not hasattr(settings, 'JOBBOARD_JOBS_ON_INDEX'):
    settings.JOBBOARD_JOBS_ON_INDEX = 5
