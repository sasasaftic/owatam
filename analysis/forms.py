from django import forms
from analysis.models import WebPage


class AddSiteForm(forms.Form):
    main_domain = forms.CharField()

    def add_main_domain(self):
        WebPage.objects.create(user, main_domain=self.main_domain)
