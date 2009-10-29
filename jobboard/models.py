# Job Board: a simple Django-based job board
# Copyright (C) 2008  Imaginary Landscape
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime

from django.db import models
from django.conf import settings


################################################################################
## Utility functions
################################################################################
def calculate_post_expires():
    """
    Generate an expiration date based on settings.JOBBOARD_POSTS_EXPIRE_DAYS

    Returns:
      A date object that is JOBBOARD_POSTS_EXPIRE_DAYS in the future
    """
    post_expire_days = datetime.timedelta(
        days=settings.JOBBOARD_POSTS_EXPIRE_DAYS)
    return datetime.date.today() + post_expire_days


def default_position():
    if Position.objects.count() == 1:
        return Position.objects.all()[0]
    else:
        return None


################################################################################
## Models
################################################################################
class NotifyEmail(models.Model):
    """
    An email address where job post notifications will be sent.

    Field attributes:
      email: the email address where the notification will be sent
    """
    email = models.EmailField()

    class Admin:
        pass

    def __unicode__(self):
        return self.email


class Position(models.Model):
    """
    An available position for working, be it a cook, waitress or
    dental hygenist.

    These appear on drop-down forms for those submitting job posts or
    applicant posts.

    Field Attributes:
      name: The name of the position
    """
    name = models.CharField(max_length=80)

    class Admin:
        pass

    def __unicode__(self):
        return self.name


class JobPost(models.Model):
    """
    A post for an available job that people can apply to.

    These are usually user-submitted, and then approved by an
    administrator.  Once they are approved, they should show up on the
    job listing until the time they expire.

    Field Attributes:
      posters_name: The name of the person or company offering the job
      work_hours: Whatever kind of hours the person might be working
        (9-5, late shift, full time, part time, whatever)
      description: Description of this job
      position: Any one of the positions in models.Position
      email: An email address relevant to this job (probably for
        contact purposes)
      contact_information: Any other contact information
      when_posted: The timestamp for when this post was submitted
      approved: Whether or not this application was approved to be
        listed on the site.
      expiration_date: The date on which this post will no longer show
        up on the listing.
    """
    approved = models.BooleanField(default=False)
    when_posted = models.DateTimeField(default=datetime.datetime.today)
    expiration_date = models.DateField(
        default=calculate_post_expires,
        help_text=(
            "This field defaults to "
            "%s days from user submission." %
            settings.JOBBOARD_POSTS_EXPIRE_DAYS))

    posters_name = models.CharField("Poster's name", max_length=80)
    work_hours = models.CharField(max_length=80, blank=True)
    description = models.TextField(blank=True)
    position = models.ForeignKey(Position, default=default_position)
    email = models.EmailField('e-mail', blank=True)
    contact_information = models.TextField('How to apply')

    class Meta:
        ordering = ['-when_posted']

    class Admin:
        fields = (
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

    def __unicode__(self):
        return u"%s @ %s" % (
            self.posters_name, self.when_posted.strftime('%m-%d-%Y %I:%M%p'))


class ApplicantPost(models.Model):
    """
    A post for a person who is seeking employment.

    These are usually user-submitted, and then approved by an
    administrator.  Once they are approved, they should show up on the
    job listing until the time they expire.

    Field Attributes:
      first_name: First name of the person seeking employment
      last_name: Last name of the person seeking employment
      phone_number: A number at which this person can be contacted
      email: An email address at which this person can be contacted
      position: Any one of the positions in models.Position
      resume: Plaintext version of this person's resume
      full_time: Whether or not this person is interested in full time
        employment
      part_time: Whether or not this person is interested in part time
        employment
      when_posted: The timestamp for when this post was submitted
      approved: Whether or not this application was approved to be
        listed on the site.
      expiration_date: The date on which this post will no longer show
        up on the listing.
    """
    approved = models.BooleanField(default=False)
    when_posted = models.DateTimeField(default=datetime.datetime.today)
    expiration_date = models.DateField(
        default=calculate_post_expires,
        help_text=(
            "This field defaults to "
            "%s days from user submission." %
            settings.JOBBOARD_POSTS_EXPIRE_DAYS))

    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=40)
    phone_number = models.CharField('phone', max_length=25)
    email = models.EmailField('e-mail', blank=True)
    position = models.ForeignKey(Position, default=default_position)
    resume = models.TextField()

    full_time = models.BooleanField('full-time')
    part_time = models.BooleanField('part-time')

    class Meta:
        ordering = ['-when_posted']

    class Admin:
        fields = (
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

    def hours_string(self):
        """
        A nice, comma-joined list of the type of hours this person is
        interested in.

        If the user selected part_time and full_time for example,
        this would show up as:
          "part time, full_time"

        If the user doesn't select anything, it will just return the
        string "unspecified".

        Returns:
          Either a comma-joined string of the hours this person is
          interested in, or "unspecified" if the user didn't select
          any.
        """
        hours = []
        if self.full_time: hours.append('full time')
        if self.part_time: hours.append('part time')
        if hours:
            return ', '.join(hours)
        else:
            return 'unspecified'

    def __unicode__(self):
        return u"%s %s @ %s" % (
            self.first_name,
            self.last_name,
            self.when_posted.strftime('%m-%d-%Y %I:%M%p'))

    def full_name(self):
        return u"%s %s" % (self.first_name, self.last_name)

