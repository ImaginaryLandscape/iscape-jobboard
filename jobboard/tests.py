################################################################################                              
# Job Board: a simple Django-based job board                                                                  
# Copyright (c) 2009, Imaginary Landscape                                                                     
# All rights reserved.                                                                                        
#                                                                                                             
# Redistribution and use in source and binary forms, with or without                                          
# modification, are permitted provided that the following conditions are met:                                 
#                                                                                                             
#     * Redistributions of source code must retain the above copyright notice,                                
#       this list of conditions and the following disclaimer.                                                 
#     * Redistributions in binary form must reproduce the above copyright                                     
#       notice, this list of conditions and the                                                               
#     * following disclaimer in the documentation and/or other materials                                      
#       provided with the distribution.                                                                       
#     * Neither the name of the Imaginary Landscape nor the names of its                                      
#       contributors may be used to endorse or promote                                                        
#     * products derived from this software without specific prior written                                    
#       permission.                                                                                           
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
import datetime
import random
import urllib
import copy

from django.conf import settings
from django.contrib.webdesign import lorem_ipsum
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from jobboard import models
from jobboard import views


# settings expected by the test

settings.JOBBOARD_FROM_EMAIL = settings.SERVER_EMAIL
settings.JOBBOARD_POSTS_EXPIRE_DAYS = 30
settings.JOBBOARD_APPLICANTS_PER_PAGE = 15
settings.JOBBOARD_JOBS_PER_PAGE = 15
settings.JOBBOARD_APPLICANTS_ON_INDEX = 5
settings.JOBBOARD_JOBS_ON_INDEX = 5


################################################################################
## Exception classes
################################################################################

class Error(Exception): pass

class LocalAssertionError(AssertionError): pass
class BadExpirationDate(LocalAssertionError): pass
class ConfigValueError(LocalAssertionError): pass


################################################################################
## Test case bases
################################################################################

class MultiTestCase(TestCase):
    """
    Basically TestCase for when subclass has multiple classes with
    setUp and tearDown

    This is done by checking for all the classes in
    self.__class__.__bases__ and running the setUp and tearDown
    methods of each.
    """
    def setUp(self):
        for this_class in self.__class__.__bases__:
            if hasattr(this_class, 'setUp')\
                    and this_class is not MultiTestCase:
                this_class.setUp(self)

    def tearDown(self):
        for this_class in self.__class__.__bases__:
            if hasattr(this_class, 'tearDown') \
                    and this_class is not MultiTestCase:
                this_class.tearDown(self)


class PageLoadTester(object):
    """
    Implements a test which verifies that a url can be loaded with a
    get request, a status code of 'OK' is returned, and that a
    particular template is used.

    Requires that the class attributes 'url' and 'template' are set.
    """
    def test_page_loads(self):
        client = Client()
        response = client.get(self.url)

        # make sure we got status 'OK'
        self.assertEqual(response.status_code, 200)

        # make sure it used the expected template
        self.assertTemplateUsed(response, self.template)


class PostVerifyTester(object):
    """
    Designed for forms-related posts, that they throw the
    appropriate errors when bad data is submitted.

    Not really intended for web services, since those do not render
    html forms with error responses when things go badly.

    Attribute dependencies:
      url: should be the url we're posting to
      template: this is the template of the form used when someone
        runs a GET on this page, and also used when validation fails.
      required_fields: some iterable of the fields that would be
        required if empty data was posted to the view.
      error_fields: a dictionary with the keys being the fields in
        question, and the value being a tuple of
          (example_bad_data, 'Whatever error would be messaged to the user')

      good_post_data: (is this needed even? I don't think so)
      form_name: 

      TODO: fill the above two out
      TODO: decide if we need good_post_data.  Actually, I think we
        can make it so that 'test_correct_type_validation' uses
        good_post_data if it finds it, but just starts with an empty
        dict otherwise.

    TODO: add support for checking multiple errors for a field
    """
    def test_required_field_validation(self):
        """
        Tests that required fields are enforced about when empty data
        is submitted to the page.
        """
        client = Client()
        response = client.post(self.url, {})

        # ensure we stay on the form's page
        self.assertTemplateUsed(response, self.template)

        # now make sure that these fields are forcibly required
        for field_name in self.required_fields:
            self.assertFormError(
                response, self.form_name, field_name,
                'This field is required.')

    def test_correct_type_validation(self):
        """
        Tests that validation is enforced when bad data is posted to
        the form.
        """
        client = Client()

        # set up the bad post data
        bad_post_data = copy.copy(self.good_post_data)

        for field_name, value in self.error_fields.iteritems():
            bad_field_data = value[0]
            bad_post_data[field_name] = bad_field_data

        response = client.post(self.url, bad_post_data)

        # ensure we stay on the form's page
        self.assertTemplateUsed(response, self.template)

        # now let's make sure that the types are right
        for field_name, value in self.error_fields.iteritems():
            expected_error_message = value[1]
            self.assertFormError(
                response, self.form_name, field_name, expected_error_message)


################################################################################
## Utility methods
################################################################################

def setup_test_job_posts(test_jobs_pattern):
    """
    Sets up a certain number of test job posts.

    This method requires that at least one models.Position is already
    set up.

    Attributes:
      test_jobs_pattern: (iterable of dicts)
        This attribute should follow the pattern of:
          [{'approved': True, 'expired': False},
           {'approved': False, 'expired': True},
           {'approved': False, 'expired': False},
           {'approved': True, 'expired': True}]

        ... where each dictionary describes the fake job post
        being set up.  'approved' specifies whether or not the
        posting has been approved, and 'expired' describes whether
        or not the expiration date has been passed or not.

        Note that the remainder of the attributes will be filled with
        random lorem ipsum text, with the exception of Position, which
        will be any randomly selected position, and when_posted, which
        will always be datetime.datetime.now()

    Returns:
      The ids of the fake job posts.
    """
    fake_job_ids = []
    for pattern in test_jobs_pattern:
        init_dict = {
            'posters_name': lorem_ipsum.words(3, common=False),
            'work_hours': lorem_ipsum.words(5, common=False),
            'description': '\n'.join(lorem_ipsum.paragraphs(4, common=False)),
            'position': random.choice(models.Position.objects.all()),
            'email': '%s@%s.%s' % tuple(
                lorem_ipsum.words(3, common=False).split()),
            'contact_information': '\n'.join(
                lorem_ipsum.paragraphs(4, common=False)),
            'when_posted': datetime.datetime.now()}

        init_dict['approved'] = pattern['approved']

        expiration_delta = datetime.timedelta(days=settings.JOBBOARD_POSTS_EXPIRE_DAYS)
        if pattern['expired']:
            init_dict['expiration_date'] = \
                datetime.date.today() - expiration_delta
        else:
            init_dict['expiration_date'] = \
                datetime.date.today() + expiration_delta

        new_jobpost = models.JobPost.objects.create(**init_dict)
        fake_job_ids.append(new_jobpost.id)

    return fake_job_ids


def setup_test_applicant_posts(test_applicants_pattern):
    """
    Sets up a certain number of test applicant posts.

    This method is EXACTLY the same as setup_test_job_posts, except it
    sets up ApplicantPosts instead of JobPosts, and that it randomly
    sets full_time_ and part_time as either True or False.  So see
    setup_test_job_posts for usage.
    """
    fake_applicant_ids = []
    for pattern in test_applicants_pattern:
        init_dict = {
            'first_name': lorem_ipsum.words(1, common=False),
            'last_name': lorem_ipsum.words(1, common=False),
            # shows what awful things phone number can accept... but
            # what can you do?  Stupid international numbers.
            'phone_number': lorem_ipsum.words(2, common=False),
            'email': '%s@%s.%s' % tuple(
                lorem_ipsum.words(3, common=False).split()),
            'position': random.choice(models.Position.objects.all()),
            'resume': '\n'.join(lorem_ipsum.paragraphs(4, common=False)),
            'when_posted': datetime.datetime.now()}

        init_dict['full_time'] = random.choice((True, False))
        init_dict['part_time'] = random.choice((True, False))

        init_dict['approved'] = pattern['approved']

        expiration_delta = datetime.timedelta(days=settings.JOBBOARD_POSTS_EXPIRE_DAYS)
        if pattern['expired']:
            init_dict['expiration_date'] = \
                datetime.date.today() - expiration_delta
        else:
            init_dict['expiration_date'] = \
                datetime.date.today() + expiration_delta

        new_applicantpost = models.ApplicantPost.objects.create(**init_dict)
        fake_applicant_ids.append(new_applicantpost.id)

    return fake_applicant_ids


################################################################################
## Generic test classes (providing convenience methods and common
## tests for subclassing)
################################################################################

class FormTest(object):
    """
    Just used for some simple assertions and common tests for
    submission forms in this module.

    Note that this isn't itself a subclass of TestCase because we
    don't want to actually run any of the tests until this is
    subclassed.  Thus, any subclass of this should also be a subclass
    of TestCase.

    TODO: FormTest isn't very descriptive.  Find a better name.
    """
    def assert_model_and_post_equal(self, model, post_data, fields):
        for field in fields:
            self.assertEqual(getattr(model, field), post_data[field])

    def test_send_email(self):
        """
        Ensure that an email is sent when (and only if) there are
        entries in the NotifyEmail table.
        """
        # First make sure that no email is sent when we haven't put
        # any email addresses in the NotifyEmail table
        client = Client()
        response = client.post(self.url, self.good_post_data)
        self.assertEqual(len(mail.outbox), 0)

        # Okay, now let's add an email address
        models.NotifyEmail.objects.create(email="linux@holla.com")

        # Submit again, and make sure that there's a message in the
        # outbox.
        client = Client()
        response = client.post(self.url, self.good_post_data)
        self.assertEqual(len(mail.outbox), 1)

        # Now make sure that
        #  - the sender was the address set up in the config file
        #  - the recipients consisted of our recently set up
        #    NotifyEmail object
        # Maybe should check? (but currently don't)
        #  - the rendered subject line and body match
        this_email = mail.outbox[0]
        self.assertEqual(this_email.from_email, settings.JOBBOARD_FROM_EMAIL)
        self.assertEqual(list(this_email.to), ['linux@holla.com'])


################################################################################
## Specific view Test Cases
################################################################################

class SubmitJobTest(TestCase, FormTest, PageLoadTester, PostVerifyTester):
    """
    Tests the jobboard.views.submit_job view.

    This class is almost identical to SubmitApplicantTest, except
    tailored for submitting jobs instead of submitting applicants.

    Tests run:
     - That the page loads successfully with a normal GET request
       (via `PageLoadTester.test_page_loads`)
     - That a submission with good data goes through successfully
       (via `test_good_submit`)
     - That required fields are enforced
       (via `PostVerifyTester.test_required_field_validation`)
     - That fields with a particular type of validation have that type
       enforced (via `PostVerifyTester.test_correct_type_validation`)
     - That an email is successfully sent upon a successful post when
       (and only when) there are entries in `models.NotifyEmail` (via
       `FormTest.test_send_email`)

    Class attributes:
      fixtures: standard for django TestCases, see django docs
      url: see PageLoadTester docs
      template: see PageLoadTester docs

    Instance attributes:
      example_position: set via setUp, this is a models.Position
        object known to be set up by the fixture
      good_post_data: set via setUp, this is initialization data that
        is known to successfully post to the form at self.url
    """
    fixtures = ['jobboard/test_positions.json']
    url = reverse('jobboard_submit_job')
    template = 'jobboard/submit_job.html'
    form_name = 'job_form'
    required_fields = ('posters_name', 'position', 'contact_information')
    error_fields = {
        'email': ('aogiaoipygpoiyaig', 'Enter a valid e-mail address.'),
        'position': ('9999', ('Select a valid choice. That choice '
                              'is not one of the available choices.'))}

    def setUp(self):
        self.example_position = models.Position.objects.get(
            name='Dental Hygenist')

        self.good_post_data = {
            'posters_name': 'Christopher McBaggins',
            'work_hours': '9am-5pm',
            'description': 'An extremely boring job',
            'position': self.example_position.id,
            'email': 'lol@lol.lol',
            'contact_information': 'Call (555) 555-555 for details'}

    def test_good_submit(self):
        """
        Tests (almost) everything about a good submission, including:
         - whether there is a successful redirect to the thank you
           page
         - whether the appropriate data appears in the database

        The exception is whether an email is or isn't sent.  See the
        test_send_email method.
        """
        client = Client()
        response = client.post(self.url, self.good_post_data)

        # ensure we redirect properly
        redirect_url = urllib.basejoin(
            'http://testserver/', reverse('jobboard_thank_you'))
        self.assertRedirects(response, redirect_url)

        # ensure the data in the database is correct
        new_post = models.JobPost.objects.get(
            posters_name='Christopher McBaggins')

        # ensure those fields are set correctly
        self.assert_model_and_post_equal(
            new_post, self.good_post_data,
            ['posters_name', 'work_hours', 'description',
             'email', 'contact_information'])
        self.assertEqual(new_post.position, self.example_position)

        # now make sure the default fields are set correctly
        self.assertEqual(new_post.approved, False)

        # make sure that the when_posted field is set.  It should be
        # today unless this is running at like, midnight.  I guess
        # we're being extra careful in the next test, but.. meh.
        day_posted = datetime.date(*new_post.when_posted.timetuple()[:3])
        self.assertEqual(day_posted, datetime.date.today())

        # and the custom set field.. to be safe, we'll make sure its
        # between two days of the settings.JOBBOARD_POSTS_EXPIRE_DAYS variable.
        post_expire_ahead = datetime.date.today() + \
            datetime.timedelta(days=settings.JOBBOARD_POSTS_EXPIRE_DAYS + 1)
        post_expire_behind = datetime.date.today() + \
            datetime.timedelta(days=settings.JOBBOARD_POSTS_EXPIRE_DAYS - 1)

        if new_post.expiration_date >= post_expire_behind \
                and new_post.expiration_date <= post_expire_ahead:
            # whew, we're fine
            pass
        else:
            raise BadExpirationDate(
                "New job post had expiration date of %s, "
                "which isn't between %s or %s days "
                "ahead of today. (Date in config is %s, "
                "being lenient)" % (
                    new_post.when_posted.strftime('%m-%d-%Y %I:%M%p'),
                    settings.JOBBOARD_POSTS_EXPIRE_DAYS - 1,
                    settings.JOBBOARD_POSTS_EXPIRE_DAYS + 1,
                    settings.JOBBOARD_POSTS_EXPIRE_DAYS))


class SubmitApplicantTest(TestCase, FormTest, PageLoadTester, PostVerifyTester):
    """
    Tests the jobboard.views.submit_applicant view.

    This class is almost identical to SubmitJobTest, except
    tailored for submitting applicants instead of submitting jobs.

    Tests run:
     - That the page loads successfully with a normal GET request
       (via `PageLoadTester.test_page_loads`)
     - That a submission with good data goes through successfully
       (via `test_good_submit`)
     - That required fields are enforced
       (via `PostVerifyTester.test_required_field_validation`)
     - That fields with a particular type of validation have that type
       enforced (via `PostVerifyTester.test_correct_type_validation`)
     - That an email is successfully sent upon a successful post when
       (and only when) there are entries in `models.NotifyEmail` (via
       `FormTest.test_send_email`)

    Class attributes:
      fixtures: standard for django TestCases, see django docs
      url: see PageLoadTester docs
      template: see PageLoadTester docs

    Instance attributes:
      example_position: set via setUp, this is a models.Position
        object known to be set up by the fixture
      good_post_data: set via setUp, this is initialization data that
        is known to successfully post to the form at self.url
    """
    fixtures = ['jobboard/test_positions.json']
    url = reverse('jobboard_submit_applicant')
    template = 'jobboard/submit_applicant.html'
    form_name = 'applicant_form'
    required_fields = (
        'first_name', 'last_name', 'phone_number', 'position', 'resume')
    error_fields = {
        'email': ('aogiaoipygpoiyaig', 'Enter a valid e-mail address.'),
        'position': ('9999', ('Select a valid choice. That choice '
                              'is not one of the available choices.'))}

    def setUp(self):
        self.example_position = models.Position.objects.get(
            name='Dental Hygenist')

        self.good_post_data = {
            'first_name': 'Christopher',
            'last_name': 'McBaggins',
            'work_hours': '9am-5pm',
            'phone_number': '(555) 555-1234',
            'position': self.example_position.id,
            'email': 'lol@lol.lol',
            'resume': 'I once fought two dinosaurs with my bear fists',
            'full_time': 'true',
            'part_time': '', # ie, false
            }

    def test_good_submit(self):
        """
        Tests (almost) everything about a good submission, including:
         - whether there is a successful redirect to the thank you
           page
         - whether the appropriate data appears in the database

        The exception is whether an email is or isn't sent.  See the
        test_send_email method.
        """
        client = Client()
        response = client.post(self.url, self.good_post_data)

        # ensure we redirect properly
        redirect_url = urllib.basejoin(
            'http://testserver/', reverse('jobboard_thank_you'))
        self.assertRedirects(response, redirect_url)

        # ensure the data in the database is correct
        new_post = models.ApplicantPost.objects.get(
            first_name='Christopher', last_name='McBaggins')

        # ensure those fields are set correctly
        self.assert_model_and_post_equal(
            new_post, self.good_post_data,
            ['first_name', 'last_name', 'phone_number', 'email', 'resume'])

        self.assertEqual(new_post.position, self.example_position)
        self.assertEqual(new_post.full_time, True)
        self.assertEqual(new_post.part_time, False)

        # now make sure the default fields are set correctly
        self.assertEqual(new_post.approved, False)

        # make sure that the when_posted field is set.  It should be
        # today unless this is running at like, midnight.  I guess
        # we're being extra careful in the next test, but.. meh.
        day_posted = datetime.date(*new_post.when_posted.timetuple()[:3])
        self.assertEqual(day_posted, datetime.date.today())

        # and the custom set field.. to be safe, we'll make sure its
        # between two days of the settings.JOBBOARD_POSTS_EXPIRE_DAYS variable.
        post_expire_ahead = datetime.date.today() + \
            datetime.timedelta(days=settings.JOBBOARD_POSTS_EXPIRE_DAYS + 1)
        post_expire_behind = datetime.date.today() + \
            datetime.timedelta(days=settings.JOBBOARD_POSTS_EXPIRE_DAYS - 1)

        if new_post.expiration_date >= post_expire_behind \
                and new_post.expiration_date <= post_expire_ahead:
            # whew, we're fine
            pass
        else:
            raise BadExpirationDate(
                "New job post had expiration date of %s, "
                "which isn't between %s or %s days "
                "ahead of today. (Date in config is %s, "
                "being lenient)" % (
                    new_post.when_posted.strftime('%m-%d-%Y %I:%M%p'),
                    settings.JOBBOARD_POSTS_EXPIRE_DAYS - 1,
                    settings.JOBBOARD_POSTS_EXPIRE_DAYS + 1,
                    settings.JOBBOARD_POSTS_EXPIRE_DAYS))


class ThankYouPageTest(TestCase, PageLoadTester):
    """
    Tests the jobboard.views.thank_you view.

    Tests run:
     - That the page loads successfully with a normal GET request
       (via `PageLoadTester.test_page_loads`)

    Class attributes:
      url: see PageLoadTester docs
      template: see PageLoadTester docs
    """
    url = reverse('jobboard_thank_you')
    template = 'jobboard/thank_you.html'


class IndexTest(MultiTestCase, PageLoadTester):
    """
    Tests the jobboard.views.thank_you view.

    Tests run:
     - That the page loads successfully with a normal GET request
       (via `PageLoadTester.test_page_loads`)
     - That the page limits itself to the number of jobs and
       applicants on this page as mandated by the settings
       JOBBOARD_JOBS_ON_INDEX and JOBBOARD_APPLICANTS_ON_INDEX
       (via `test_post_limits`)
     - That the page properly excludes posts that have expired or
       haven't been approved (via `test_post_exclusions`)

    Class attributes:
      fixtures: standard for django TestCases, see django docs
      url: see PageLoadTester docs
      template: see PageLoadTester docs
    """
    fixtures = ['jobboard/test_positions.json']
    url = reverse('jobboard_index')
    template = 'jobboard/index.html'

    def test_post_limits(self):
        """
        Tests that the limits of number of posts shown for this page
        specified by the application config are actually enforced.

        Does this by generating five more than the number allowed on
        the index and tests to make sure it stays at the limit.
        """
        jobs_per_page = settings.JOBBOARD_JOBS_ON_INDEX
        applicants_per_page = settings.JOBBOARD_APPLICANTS_ON_INDEX

        # generate more than we need..
        num_jobs = jobs_per_page + 5
        jobs_pattern = [
            {'approved': True, 'expired': False} for i in range(num_jobs)]
        setup_test_job_posts(jobs_pattern)

        # and again
        num_applicants = applicants_per_page + 5
        applicants_pattern = [
            {'approved': True, 'expired': False} for i in range(num_applicants)]
        setup_test_applicant_posts(applicants_pattern)

        # now 'visit' the page
        client = Client()
        response = client.get(self.url)

        # making sure we get the right thing depending on whether
        # {% includes %} exist in the template or not
        if isinstance(response.context, list):
            context = response.context[0]
        else:
            context = response.context

        self.assertEqual(
            context['jobs'].count(),
            jobs_per_page)
        self.assertEqual(
            context['applicants'].count(),
            applicants_per_page)

    def test_post_exclusions(self):
        """
        This test should make sure that posts that are expired or not
        approved don't show up.
        """
        # set up three that show up (approved and not expired), as
        # well as one unapproved, one expired for each model, and one
        # that's both approved and expired.
        test_pattern = ({'approved': True, 'expired': False},
                        {'approved': True, 'expired': False},
                        {'approved': True, 'expired': False},
                        {'approved': False, 'expired': False},
                        {'approved': True, 'expired': True},
                        {'approved': False, 'expired': True})
        setup_test_job_posts(test_pattern)
        setup_test_applicant_posts(test_pattern)

        # now 'visit' the page
        client = Client()
        response = client.get(self.url)

        # making sure we get the right thing depending on whether
        # {% includes %} exist in the template or not
        if isinstance(response.context, list):
            context = response.context[0]
        else:
            context = response.context

        # and make sure that only three show up for each.
        self.assertEqual(context['jobs'].count(), 3)
        self.assertEqual(context['applicants'].count(), 3)


class JobListTest(MultiTestCase, PageLoadTester):
    """
    Tests the view jobboard.views.job_list.

    Tests run:
     - That the page loads successfully with a normal GET request
       (via `PageLoadTester.test_page_loads`)

    Class attributes:
      fixtures: standard for django TestCases, see django docs
      url: see PageLoadTester docs
      template: see PageLoadTester docs

    TODO: Add test to ensure pagination is working correctly
    TODO: Actually put some models in here via setup_test_job_posts
    """
    fixtures = ['jobboard/test_positions.json']
    url = reverse('jobboard_job_list')
    template = 'jobboard/jobpost_list.html'


class ApplicantListTest(MultiTestCase, PageLoadTester):
    """
    Tests the view jobboard.views.applicant_list.

    Tests run:
     - That the page loads successfully with a normal GET request
       (via `PageLoadTester.test_page_loads`)

    Class attributes:
      fixtures: standard for django TestCases, see django docs
      url: see PageLoadTester docs
      template: see PageLoadTester docs

    TODO: Add test to ensure pagination is working correctly
    TODO: Actually put some models in here via setup_test_job_posts
    """
    fixtures = ['jobboard/test_positions.json']
    url = reverse('jobboard_applicant_list')
    template = 'jobboard/applicantpost_list.html'
