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

from django import forms
from django.conf import settings
from jobboard import models

if settings.CAPTCHA:
    from captcha.fields import CaptchaField


class JobPost(forms.Form):
    """
    The submission form for a visitor submitting a new job post.
    """
    posters_name = forms.CharField(max_length=80)
    work_hours = forms.CharField(max_length=80, required=False)
    description = forms.CharField(required=False, widget=forms.Textarea)
    position = forms.ModelChoiceField(models.Position.objects.all())
    email = forms.EmailField(required=False)
    contact_information = forms.CharField(widget=forms.Textarea)
    
    if settings.CAPTCHA:
        captcha = CaptchaField() 

    def clean_posters_name(self):
        """
        Clean up the `posters_name` field to reduce it to one line
        """
        return self.cleaned_data['posters_name'].split('\n')[0]


class ApplicantPost(forms.Form):
    """
    The submission form for a visitor submitting a new applicant post.
    """
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=40)
    phone_number = forms.CharField(max_length=25)
    position = forms.ModelChoiceField(models.Position.objects.all())
    email = forms.EmailField(required=False)
    resume = forms.CharField(widget=forms.Textarea)

    full_time = forms.BooleanField(required=False)
    part_time = forms.BooleanField(required=False)
    other_time = forms.BooleanField(required=False)
    if settings.CAPTCHA:
        captcha = CaptchaField()

    def clean_first_name(self):
        """
        Clean up the `first_name` field to reduce it to one line
        """
        return self.cleaned_data['first_name'].split('\n')[0]

    def clean_last_name(self):
        """
        Clean up the `last_name` field to reduce it to one line
        """
        return self.cleaned_data['last_name'].split('\n')[0]
