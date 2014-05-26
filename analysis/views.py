from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render_to_response
from django.template import RequestContext
from analysis.models import AboutDevice, Browser, Device, Os, PageAnalyzed, ElementAnalyzed
from models import WebPage, Visit, Visitor, VisitAnalyzed, Location
from django.http import HttpResponse
import json
from django.contrib.auth.decorators import login_required
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

        locations = Location.objects.filter(webpage=web_page).order_by("-num_of_visits")[0:5]

        pages_best = PageAnalyzed.objects.filter(webpage=web_page).order_by("-average_time")[0:5]

        pages_all = []
        for page in pages_best:
            pages_all.append((page, str(datetime.timedelta(seconds=page.average_time))))

        elements_best = ElementAnalyzed.objects.filter(webpage=web_page).order_by("-average_time")[0:5]
        elements_all = []
        for element in elements_best:
            elements_all.append((element, str(datetime.timedelta(seconds=element.average_time))))

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
                                                 "browsers": browsers, "devices": devices, "oss": oss, "pages": pages_all,
                                                 "elements": elements_all},
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
            WebPage.objects.get(pk=webpage_id, user=request.user)
            WebPage.objects.get(pk=webpage_id, user=request.user).delete()
        except Exception as e:
            print e
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

        if WebPage.objects.filter(main_domain=hostname, page_id=page_id).count():  # if webpage exists
            web_page = WebPage.objects.get(main_domain=hostname)

            visit_analyzeds = VisitAnalyzed.objects.filter(webpage=web_page, date=date_no_time)
            if visit_analyzeds.count():  # if visit analyzer exists else create one
                visit_analyzed = visit_analyzeds[0]

            else:
                visit_analyzed = VisitAnalyzed.objects.create(webpage=web_page, date=date_no_time)
                visit_analyzed.last_visit = date
                add_device_and_browser_info(request, web_page)  # get users device and browser information
                add_location_info(request, web_page, address)
                visit_analyzed.save()

            visitor_set = Visitor.objects.filter(cookie_id=cookie_id, webpage=web_page)  # if visitor exists else create one
            if visitor_set.count():
                visitor = visitor_set[0]
            else:
                visitor = Visitor.objects.create(cookie_id=cookie_id, webpage=web_page)
                visitor.last_visited_page = host
                visitor.last_page_visit = date
                visitor.last_visit = date
                visit_analyzed.unique_visitors += 1
                visit_analyzed.all_visitors += 1
                visit_analyzed.save()
                visitor.save()

            time_diff = (date - visitor.last_visit).seconds  # get time difference from last visit
            if 50 < time_diff < 200:  # if time difference is betwen active offset and new visit offset then this is still active usage
                new_average_active = (visit_analyzed.num_of_samples_active * visit_analyzed.average_time_active +
                                      time_diff) / (visit_analyzed.num_of_samples_active + 1)
                visit_analyzed.num_of_samples_active += 1
                visit_analyzed.average_time_active = new_average_active

                new_average_all = (visit_analyzed.num_of_samples_all * visit_analyzed.average_time_all +
                                   time_diff) / (visit_analyzed.num_of_samples_all + 1)
                visit_analyzed.num_of_samples_all += 1
                visit_analyzed.average_time_all = new_average_all

            elif time_diff >= 200:
                new_average_all = (visit_analyzed.num_of_samples_all * visit_analyzed.average_time_all +
                                   time_diff) / (visit_analyzed.num_of_samples_all + 1)
                visit_analyzed.num_of_samples_all += 1
                visit_analyzed.average_time_all = new_average_all
                add_device_and_browser_info(request, web_page)
                add_location_info(request, web_page, address)
                visit_analyzed.all_visitors += 1

            visitor.last_visit = date
            visit_analyzed.save()
            visitor.save()

            Visit.objects.create(webpage=web_page, page=host, date=date, visitor=visitor, ip=ip, location=address,
                                 title=title, element=element, call_type=action)

            if action == "first_call":

                page_analyzeds = PageAnalyzed.objects.filter(webpage=web_page, page=visitor.last_visited_page)
                if page_analyzeds.count():
                    page_analyzed = page_analyzeds[0]
                else:
                    page_analyzed = PageAnalyzed.objects.create(webpage=web_page, page=visitor.last_visited_page)

                time_diff = (date - visitor.last_page_visit).seconds
                if time_diff < 300:
                    page_analyzed.average_time = (page_analyzed.num_of_samples * page_analyzed.average_time +
                                                  time_diff) / (page_analyzed.num_of_samples + 1)
                    page_analyzed.num_of_samples += 1
                page_analyzed.save()
                visitor.last_visited_page = host
                visitor.last_page_visit = date
                visitor.save()

            if action == "scroll_call":
                if visitor.last_visited_element is None:
                    visitor.last_visited_element = element
                    visitor.last_element_visit = date
                    visitor.save()
                element_analayzeds = ElementAnalyzed.objects.filter(webpage=web_page, page=visitor.last_visited_page, element=visitor.last_visited_element)

                if element_analayzeds.count():
                    element_analayzed = element_analayzeds[0]
                else:
                    element_analayzed = ElementAnalyzed.objects.create(webpage=web_page, page=host, element=visitor.last_visited_element)

                time_diff = (date - visitor.last_element_visit).seconds
                if time_diff < 300:
                    element_analayzed.average_time = (element_analayzed.num_of_samples * element_analayzed.average_time +
                    time_diff) / (element_analayzed.num_of_samples + 1)

                    element_analayzed.num_of_samples += 1
                element_analayzed.save()

                visitor.last_visited_element = element
                visitor.last_element_visit = date
                visitor.save()

        data = {"": ""}
        return HttpResponse(json.dumps(data), content_type="application/json", status=200)

    data = {"": ""}
    return HttpResponse(json.dumps(data), content_type="application/json", status=200)


@login_required
def locations(request):
    webpages = WebPage.objects.filter(selected=True, user=request.user)
    if webpages.count():
        locations = Location.objects.filter(webpage=webpages[0]).order_by("-num_of_visits")
        return render_to_response('locations.html', {"locations": locations},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('locations.html', {"error": "Please select active webpage on manage tab."},
                                  context_instance=RequestContext(request))


@login_required
def pages(request):
    webpages = WebPage.objects.filter(selected=True, user=request.user)
    if webpages.count():
        pages_best = PageAnalyzed.objects.filter(webpage=webpages[0]).order_by("-average_time")
        pages_all = []
        for page in pages_best:
            pages_all.append((page, str(datetime.timedelta(seconds=page.average_time))))
        return render_to_response('pages.html', {"pages": pages_all},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('pages.html', {"error": "Please select active webpage on manage tab."},
                                  context_instance=RequestContext(request))


@login_required
def elements(request):
    webpages = WebPage.objects.filter(selected=True, user=request.user)
    if webpages.count():
        elements_best = ElementAnalyzed.objects.filter(webpage=webpages[0]).order_by("-average_time")
        elements_all = []
        for element in elements_best:
            elements_all.append((element, str(datetime.timedelta(seconds=element.average_time))))
        return render_to_response('elements.html', {"elements": elements_all},
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('elements.html', {"error": "Please select active webpage on manage tab."},
                                  context_instance=RequestContext(request))


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


def add_location_info(request, web_page, address):
    locations = Location.objects.filter(webpage=web_page, continent=address["continent"],
                                        country=address["country_name"], city=address["city"], time_zone=address["time_zone"])
    if locations.count():
        loc = locations[0]
        loc.num_of_visits += 1
        loc.save()
    else:
        Location.objects.create(webpage=web_page, continent=address["continent"],
                                country=address["country_name"], city=address["city"], time_zone=address["time_zone"])
