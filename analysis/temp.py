from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.template import RequestContext
from analysis.models import AboutDevice, Browser, Device, Os, PageAnalyzed, ElementAnalyzed
from models import WebPage, Visit, Visitor, VisitAnalyzed, Location
from django.http import HttpResponse
import json
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import FormView
from django.shortcuts import redirect
from ipware.ip import get_ip
import pygeoip
import datetime
import uuid


@login_required
def home(request):
    web_pages = WebPage.objects.filter(selected=True, user=request.user)
    if web_pages.count():
        web_page = web_pages[0]
        visits = Visit.objects.filter(webpage=web_page)

        curr_date = datetime.datetime.now()
        dates_list = [str((curr_date + datetime.timedelta(days=k)).year) + "-" + str((curr_date + datetime.timedelta
        (days=k)).month) + "-" + str((curr_date + datetime.timedelta(days=k)).day) for k in range(-30, 1)]

        date_visits_all = {}
        date_visits_unique = {}
        avg_active_time = 0
        avg_time = 0
        all_users = 0
        unique_users = 0
        visit_analyzeds = VisitAnalyzed.objects.filter(webpage=web_page)
        for analysis in visit_analyzeds:
            date_visits_all[str(analysis.date.year) + "-" + str(analysis.date.month) + "-" + str(analysis.date.day)] =\
                analysis.all_visitors
            date_visits_unique[str(analysis.date.year) + "-" + str(analysis.date.month) + "-" + str(analysis.date.day)] =\
                analysis.unique_visitors

            avg_active_time += analysis.average_time_active
            avg_time += analysis.average_time_all
            all_users += analysis.all_visitors
            unique_users += analysis.unique_visitors

        if visit_analyzeds.count():
            avg_active_time = str(datetime.timedelta(seconds=avg_active_time/visit_analyzeds.count()))
            avg_time = str(datetime.timedelta(seconds=avg_time/visit_analyzeds.count()))

        locations = Location.objects.filter(webpage=web_page).order_by("num_of_visits")[0:5]
        pages = PageAnalyzed.objects.filter(webpage=web_page).order_by("average_time")[0:5]
        elements = ElementAnalyzed.objects.filter(webpage=web_page).order_by("average_time")[0:5]

        about_devices = AboutDevice.objects.filter(webpage=web_page)
        about_device = None
        if about_devices.count():
            about_device = about_devices[0]

        browsers = Browser.objects.filter(webpage=web_page)
        devices = Device.objects.filter(webpage=web_page)
        oss = Os.objects.filter(webpage=web_page)

        return render_to_response('index.html', {"visits": visits, "date_visits_all": date_visits_all,
                                                 "date_visits_unique": date_visits_unique, "dates_list": dates_list,
                                                 "avg_active_time": avg_active_time, "avg_time": avg_time,
                                                 "all_users": all_users, "unique_users": unique_users,
                                                 "locations": locations, "about_device": about_device,
                                                 "browsers": browsers, "devices": devices, "oss": oss, "pages": pages,
                                                 "elements": elements},
                                  context_instance=RequestContext(request))

    return render_to_response('index.html', {"info": "First, please add and select your webpage in manage settings."}, context_instance=RequestContext(request))


@login_required
def manage(request):
    web_page = WebPage.objects.all()
    return render_to_response('manage.html', {"webpage": web_page}, context_instance=RequestContext(request))


@login_required
def new_webpage(request):
    if request.POST:
        domain = request.POST.get('domain', '')
        if domain:
            if WebPage.objects.filter(main_domain=domain).count():
                return render_to_response('new_webpage.html', {"error": "This page has already been added."},
                                          context_instance=RequestContext(request))
            else:
                if WebPage.objects.filter(user=request.user, selected=True).count():
                    webpage = WebPage.objects.create(user=request.user, main_domain=domain)
                else:
                    webpage = WebPage.objects.create(user=request.user, main_domain=domain, selected=True)
                page_id = str(uuid.uuid1())
                while WebPage.objects.filter(page_id=page_id).count():
                    page_id = str(uuid.uuid1())

                webpage.page_id = page_id
                webpage.save()
                return render_to_response('new_webpage.html', {
                    'javascript': '<script>var page_id="' + page_id + '";var js=document.createElement("script"); js.ty'
                    'pe="text/javascript"; js.src="http://cashiermobile.com:8080/static/js/owatam.js"; '
                    'document.body.appendChild(js)</script>'}, context_instance=RequestContext(request))
        else:
            return render_to_response('new_webpage.html', {"error": "Field cannot be emty"},
                                      context_instance=RequestContext(request))
    return render_to_response('new_webpage.html', context_instance=RequestContext(request))


@login_required
def delete_webpage(request, webpage_id):
    if webpage_id:
        try:
            print WebPage.objects.get(pk=webpage_id, user=request.user)
            WebPage.objects.get(pk=webpage_id, user=request.user).delete()
        except Exception as e:
            print e
            print request.user.username, webpage_id
            return render_to_response('new_webpage.html', {"error": "You cannot delete this webpage"},
                                      context_instance=RequestContext(request))
    return redirect('manage')


@login_required
def select_webpage(request, webpage_id):
    for page in WebPage.objects.filter(selected=True, user=request.user).all():
        page.selected = False
        page.save()
    page = WebPage.objects.get(pk=webpage_id, user=request.user)
    page.selected = True
    page.save()
    return redirect('manage')

@csrf_exempt
def receive_data(request):
    action = request.POST.get('name_id', '')
    hostname = request.POST.get('hostname', '')
    title = request.POST.get('title', '')
    host = request.POST.get('host', '')
    cookie_id = request.POST.get('cookie_id', '')
    js_date = request.POST.get('date', '')
    element = request.POST.get('element', '')
    ip = get_ip(request)
    date = datetime.datetime.utcfromtimestamp(float(js_date)/1000.0)
    date_no_time = date.date()

    try:
        gi = pygeoip.GeoIP('GeoLiteCity.dat')
        address = gi.record_by_addr(ip)
    except Exception as e:
        print e
        address = "unknown"

    if date and hostname and host and cookie_id:
        
        page_id = cookie_id[-36:]

        # page_analyzeds = PageAnalyzed.objects.filter(webpage=web_page, page=host)
                # if page_analyzeds.count():  # if page analyzer exists else create one
                #     page_analyzed = page_analyzeds[0]
                #     if action == "scroll_call":
                #         element_analyzeds = ElementAnalyzed.objects.filter(webpage=web_page, element=element, page=page_analyzed)
                #         if element_analyzeds.count():
                #             element_analyzed = element_analyzeds[0]
                #             time_diff = (date - page_analyzed.date).seconds
                #             element_analyzed.average_time = (element_analyzed.num_of_samples + element_analyzed.average_time +
                #                                              time_diff) / (element_analyzed.num_of_samples + 1)
                #             element_analyzed.num_of_samples += 1
                #
                #         else:
                #             element_analyzed = ElementAnalyzed.objects.create(webpage=web_page, element=element, page=page_analyzed)
                #             element_analyzed.date = date
                #         element_analyzed.save()

        if WebPage.objects.filter(main_domain=hostname, page_id=page_id).count():  # if webpage exists
            web_page = WebPage.objects.get(main_domain=hostname)

            visitor_set = Visitor.objects.filter(cookie_id=cookie_id, webpage=web_page)  # if visitor exists else create one
            if visitor_set.count():
                visitor = visitor_set[0]

                page_analyzeds = PageAnalyzed.objects.filter(webpage=web_page, page=host)
                if page_analyzeds.count():
                    page_analyzed = page_analyzeds[0]
                    if action == "scroll_call":
                        element_analyzeds = ElementAnalyzed.objects.filter(webpage=web_page, element=element, page=page_analyzed)
                        if element_analyzeds.count():
                            element_analyzed = element_analyzeds[0]
                            time_diff = (date - page_analyzed.date).seconds
                            element_analyzed.average_time = (element_analyzed.num_of_samples + element_analyzed.average_time +
                                                             time_diff) / (element_analyzed.num_of_samples + 1)
                            element_analyzed.num_of_samples += 1

                        else:
                            element_analyzed = ElementAnalyzed.objects.create(webpage=web_page, element=element, page=page_analyzed)
                            element_analyzed.date = date
                        element_analyzed.save()

                visit_analyzeds = VisitAnalyzed.objects.filter(webpage=web_page, date=date_no_time)
                if visit_analyzeds.count():
                    print 4
                    visit_analyzed = visit_analyzeds[0]
                    time_diff = (date - visitor.last_visit).seconds
                    if 50 < time_diff < 200:
                        new_average_active = (visit_analyzed.num_of_samples_active * visit_analyzed.average_time_active +
                                              time_diff) / (visit_analyzed.num_of_samples_active + 1)
                        visit_analyzed.num_of_samples_active += 1
                        add_device_and_browser_info(request, web_page)
                        visit_analyzed.average_time_active = new_average_active

                        page_analyzeds = PageAnalyzed.objects.filter(webpage=web_page, page=host)
                        if page_analyzeds.count():
                            page_analyzed = page_analyzeds[0]
                            time_diff = (date - page_analyzed.date).seconds
                            page_analyzed.average_time = (page_analyzed.num_of_samples * page_analyzed.average_time +
                                                          time_diff) / (page_analyzed.num_of_samples + 1)
                            page_analyzed.num_of_samples += 1
                        else:
                            page_analyzed = PageAnalyzed.objects.create(webpage=web_page, page=host)
                            page_analyzed.date = date
                        page_analyzed.save()

                    if time_diff >= 200:
                        new_average_all = (visit_analyzed.num_of_samples_all * visit_analyzed.average_time_all +
                                           time_diff) / (visit_analyzed.num_of_samples_all + 1)
                        visit_analyzed.num_of_samples_all += 1
                        visit_analyzed.average_time_all = new_average_all
                        add_device_and_browser_info(request, web_page)

                    visitor.last_visit = date
                    visit_analyzed.save()
                    visitor.save()
                else:
                    print 5
                    va = VisitAnalyzed.objects.create(webpage=web_page, date=date_no_time)
                    va.all_visitors += 1
                    visitor.last_visit = date
                    visitor.save()
                    va.save()
                    add_device_and_browser_info(request, web_page)

                    page_analyzeds = PageAnalyzed.objects.filter(webpage=web_page, page=host)
                    if page_analyzeds.count():
                        page_analyzed = page_analyzeds[0]
                        time_diff = (date - page_analyzed.date).seconds
                        page_analyzed.average_time = (page_analyzed.num_of_samples * page_analyzed.average_time +
                                                      time_diff) / (page_analyzed.num_of_samples + 1)
                        page_analyzed.num_of_samples += 1
                    else:
                        page_analyzed = PageAnalyzed.objects.create(webpage=web_page, page=host)
                        page_analyzed.date = date
                    page_analyzed.save()

                    locations = Location.objects.filter(webpage=web_page, continent=address["continent"],
                                       country=address["country_name"], city=address["city"], time_zone=address["time_zone"])
                    if locations.count():
                        print 7
                        loc = locations[0]
                        loc.num_of_visits += 1
                        loc.save()
                    else:
                        Location.objects.create(webpage=web_page, continent=address["continent"],
                                                country=address["country_name"], city=address["city"], time_zone=address["time_zone"])

            else:
                visitor = Visitor.objects.create(cookie_id=cookie_id, webpage=web_page)
                visitor.last_visit = date

                visit_analyzeds = VisitAnalyzed.objects.filter(webpage=web_page, date=date_no_time)
                if visit_analyzeds.count():
                    va = visit_analyzeds[0]
                else:
                    va = VisitAnalyzed.objects.create(webpage=web_page, date=date_no_time)
                va.unique_visitors += 1
                va.all_visitors += 1
                add_device_and_browser_info(request, web_page)

                locations = Location.objects.filter(webpage=web_page, continent=address["continent"],
                                                    country=address["country_name"], city=address["city"], time_zone=address["time_zone"])
                if locations.count():
                    loc = locations[0]
                    loc.num_of_visits += 1
                    loc.save()
                else:
                    Location.objects.create(webpage=web_page, continent=address["continent"],
                                            country=address["country_name"], city=address["city"], time_zone=address["time_zone"])

                va.save()
                visitor.save()
            Visit.objects.create(webpage=web_page, page=host, date=date, visitor=visitor, ip=ip, location=address,
                                 title=title, element=element, call_type=action)
        data = {"": ""}
        return HttpResponse(json.dumps(data), content_type="application/json", status=200)

    data = {"": ""}
    return HttpResponse(json.dumps(data), content_type="application/json", status=200)


@login_required
def locations(request):
    webpages = WebPage.objects.filter(selected=True, user=request.user)
    if webpages.count():
        locations = Location.objects.filter(webpage=webpages[0])
        return render_to_response('locations.html', {"locations": locations},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('locations.html', {"error": "Please select active webpage on manage tab."},
                                  context_instance=RequestContext(request))


class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = UserCreationForm
    success_url = '/'

    def post(self, request, *args, **kwargs):
        form = UserCreationForm(request.POST)
        if form.is_valid():
           user = form.save()


def add_device_and_browser_info(request, web_page):
    about_devices = AboutDevice.objects.filter(webpage=web_page)
    if about_devices.count():
        about_device = about_devices[0]
    else:
        about_device = AboutDevice.objects.create(webpage=web_page)
    if request.user_agent.is_mobile:
        about_device.mobile += 1
    if request.user_agent.is_tablet:
        about_device.tablet += 1
    if request.user_agent.is_touch_capable:
        about_device.touch_capable += 1
    if request.user_agent.is_pc:
        about_device.pc += 1
    if request.user_agent.is_bot:
        about_device.bot += 1
    about_device.save()

    browser_str = request.user_agent.browser.family + ", " + request.user_agent.browser.version_string
    browsers = Browser.objects.filter(webpage=web_page, browser=browser_str)
    if browsers.count():
        browser = browsers[0]
        browser.num_of_browsers += 1
        browser.save()
    else:
        Browser.objects.create(webpage=web_page, browser=browser_str)

    device_str = request.user_agent.device.family
    devices = Device.objects.filter(webpage=web_page, device=device_str)
    if devices.count():
        device = devices[0]
        device.num_of_devices += 1
        device.save()
    else:
        Device.objects.create(webpage=web_page, device=device_str)

    os_str = request.user_agent.os.family + ", " + request.user_agent.os.version_string
    oss = Os.objects.filter(webpage=web_page, os=os_str)
    if oss.count():
        os = oss[0]
        os.num_of_oss += 1
        os.save()
    else:
        Os.objects.create(webpage=web_page, os=os_str)
