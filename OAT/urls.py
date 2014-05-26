from django.conf.urls import patterns, include, url
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'analysis.views.home', name='dashboard'),
    url(r'^manage/$', 'analysis.views.manage', name='manage'),
    url(r'^manage/new/$', 'analysis.views.new_webpage', name='new_webpage'),
    url(r'^manage/new/(?P<webpage_id>\d+)/$', 'analysis.views.delete_webpage', name='delete_webpage'),
    url(r'^manage/select/(?P<webpage_id>\d+)/$', 'analysis.views.select_webpage', name='select_webpage'),
    url(r'^send_data$', 'analysis.views.receive_data', name='receive_data'),
    url(r'^locations/$', 'analysis.views.locations', name='locations'),
    url(r'^pages/$', 'analysis.views.pages', name='pages'),
    url(r'^elements/$', 'analysis.views.elements', name='elements'),
    # url(r'^OAT/', include('OAT.foo.urls')),

    # User

    url('^accounts/register/', CreateView.as_view(
            template_name='registration/register.html',
            form_class=UserCreationForm,
            success_url='/',
    ), name='register'),

    url('^accounts/', include('django.contrib.auth.urls')),



    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^logout/$', 'django.contrib.auth.views.logout',
                      {'next_page': '/'}, name="log_out"),
)
