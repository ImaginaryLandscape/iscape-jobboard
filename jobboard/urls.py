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
