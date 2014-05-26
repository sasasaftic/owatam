from django.contrib.auth.models import User
from django.db import models


class WebPage(models.Model):
    user = models.ForeignKey(User)
    main_domain = models.CharField(max_length=20)
    page_id = models.CharField(max_length=20)
    selected = models.BooleanField(default=False)

    def __unicode__(self):
        return self.main_domain


class Visitor(models.Model):
    cookie_id = models.CharField(max_length=40, null=True)
    webpage = models.ForeignKey(WebPage)
    last_visit = models.DateTimeField(null=True)
    last_visited_page = models.CharField(max_length=255, null=True)
    last_page_visit = models.DateTimeField(null=True)
    last_visited_element = models.CharField(max_length=255, null=True)
    last_element_visit = models.DateTimeField(null=True)

    def __unicode__(self):
        return self.cookie_id


class Visit(models.Model):
    webpage = models.ForeignKey(WebPage)
    ip = models.CharField(max_length=30)
    location = models.CharField(max_length=20)
    page = models.CharField(max_length=255)
    call_type = models.CharField(max_length=20)
    title = models.CharField(max_length=20)
    element = models.CharField(max_length=20)
    date = models.DateTimeField()
    visitor = models.ForeignKey(Visitor)

    def __unicode__(self):
        return self.page


class VisitAnalyzed(models.Model):
    webpage = models.ForeignKey(WebPage)
    date = models.DateField(null=True)
    average_time_active = models.IntegerField(default=0)
    num_of_samples_active = models.IntegerField(default=0)
    average_time_all = models.IntegerField(default=0)
    num_of_samples_all = models.IntegerField(default=0)
    unique_visitors = models.IntegerField(default=0)
    all_visitors = models.IntegerField(default=0)


class Location(models.Model):
    webpage = models.ForeignKey(WebPage)
    country = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    num_of_visits = models.IntegerField(default=1)
    continent = models.CharField(max_length=200, null=True)
    time_zone = models.CharField(max_length=200, null=True)


class PageAnalyzed(models.Model):
    webpage = models.ForeignKey(WebPage)
    average_time = models.IntegerField(default=0)
    page = models.CharField(max_length=255)
    num_of_samples = models.IntegerField(default=1)


class ElementAnalyzed(models.Model):
    webpage = models.ForeignKey(WebPage)
    page = models.CharField(max_length=255)
    average_time = models.IntegerField(default=0)
    element = models.CharField(max_length=255)
    num_of_samples = models.IntegerField(default=1)


class UserSettings(models.Model):
    user = models.ForeignKey(User)
    active_time = models.IntegerField()
    new_visit_time = models.IntegerField()


class AboutDevice(models.Model):
    webpage = models.ForeignKey(WebPage)
    mobile = models.IntegerField(default=0)
    tablet = models.IntegerField(default=0)
    touch_capable = models.IntegerField(default=0)
    pc = models.IntegerField(default=0)
    bot = models.IntegerField(default=0)


class Browser(models.Model):
    webpage = models.ForeignKey(WebPage)
    browser = models.CharField(max_length=200)  # Family + version_string
    num_of_browsers = models.IntegerField(default=1)


class Device(models.Model):
    webpage = models.ForeignKey(WebPage)
    device = models.CharField(max_length=200)  # device.family
    num_of_devices = models.IntegerField(default=1)


class Os(models.Model):
    webpage = models.ForeignKey(WebPage)
    os = models.CharField(max_length=200)  # Os + os.family
    num_of_oss = models.IntegerField(default=1)
