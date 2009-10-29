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
