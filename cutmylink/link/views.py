from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Link, Click, User
from .serializers import ClickSerializer, LinkSerializer, UserSerializer
from ipwhois import IPWhois
from django.shortcuts import redirect
import re
from datetime import datetime, timedelta
import datetime as dtime
from pytz import timezone
from django.db.models import Q
from urllib.parse import unquote
from django.db.models import Count
import locale
from django.shortcuts import render


def index(request):
    return render(request, 'index.html')
class ShortLinkRedirectView(APIView):
    def get(self, request, short_code):
        try:
            short_link = Link.objects.get(url=short_code)
        except:
            return redirect('https://google.com')
        link_id = short_link.id
        ip = get_client_ip(request)
        referer = request.headers.get('Referer', 'none')
        ip_info = IPWhois('94.179.41.245')
        result = ip_info.lookup_rdap()
        provider = result['network']['name']
        country = result['network']['country']
        os = request.user_agent.os.family
        browser = request.user_agent.browser.family
        device = getDevice(request)
        data = {
            "ip":ip,
            "provider":provider,
            "country":country,
            "os":os,
            "browser":browser,
            "referer":referer,
            "link": link_id,
            "device": device,
        }
        serializer = ClickSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status':'ok',
                             'message': serializer.data})
        else:
            return Response({
                'status': serializer.errors
            })

class UserCreateAPIView(generics.CreateAPIView):
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'ok',
                'data': serializer.data
            })
        else:
            return Response({
                'status': serializer.errors
            })

class LinkAPIView(generics.ListCreateAPIView):
    serializer_class = LinkSerializer

    def get_queryset(self,request):
        user = User.objects.get(telegram_id=request.query_params.get('user_id'))
        return Link.objects.filter(user_id=user.id).values('id', 'url', 'redirect_url', 'created_at', 'updated_at')

    def list(self, request):
        links = list(self.get_queryset(request))
        return Response(links)

    def create(self, request):
        user = User.objects.get(telegram_id=request.data['telegram_id'])
        if check_url(request.data['url']) and is_valid_redirect(request.data['reidrect_url']):
            data = {'url':request.data['url'], 'user': user.id , 'redirect_url':request.data['reidrect_url']}
            print(data)
            serializer = LinkSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status':'ok',
                    'data': serializer.data
                })
            else:
                return Response({
                    'status': serializer.errors
                })
        else:
            return Response({
                'status': 'error', 'description': 'Invalid URL or redirect link'
            }, status=status.HTTP_400_BAD_REQUEST)

class LinkAPIUpdate(generics.UpdateAPIView):
    queryset = Link.objects.all()
    serializer_class = LinkSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Дополнительная проверка поля перед обновлением
        if check_url(request.data.get('url')) and is_valid_redirect(request.data.get('redirect_url')):
            self.perform_update(serializer)
            return Response(serializer.data)
        else:
            response_data = {'status': 'error'}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

class LinkAPIDelete(generics.DestroyAPIView):
    queryset = Link.objects.all()
    serializer_class = LinkSerializer

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[-1].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def check_url(input_string):
    if ' ' in input_string:
        return False
    if not re.match("^[a-zA-Z0-9]+$", input_string):
        return False
    return True

def is_valid_redirect(url):
    regex_pattern = r'^(https?|ftp)://[^\s/$.?#].[^\s]*$'
    match = re.match(regex_pattern, url)
    return bool(match)

def getDevice(request):
    if request.user_agent.is_pc:
        return 'PC'
    elif request.user_agent.is_mobile or request.user_agent.is_tablet:
        return 'MOBILE'
    else:
        return 'BOT'

class LinkStatView(APIView):
    def get(self, request):
        link_name = request.query_params.get('link', None)
        start_date_param = unquote(request.query_params.get('date_from', ''))
        end_date_param = unquote(request.query_params.get('date_to', ''))
        print(start_date_param)
        try:
            start_date = datetime.strptime(start_date_param, '%Y-%m-%d %H:%M:%S.%f%z')
            end_date = datetime.strptime(end_date_param, '%Y-%m-%d %H:%M:%S.%f%z')
        except (ValueError, TypeError):
            print(start_date_param)
            return Response({'error': 'Invalid date format'}, status=400)

        date_list_string = []
        date_list_digit = []
        click_count_list = []
        current_date = start_date
        click_count = 0

        link = Link.objects.get(url=link_name)
        serializer = LinkSerializer(link)
        link_id = serializer.data.get('id')

        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

        locale.setlocale(locale.LC_TIME, 'uk_UA.UTF-8')
        while current_date <= end_date:
            date_list_digit.append(current_date.strftime('%Y-%m-%d'))
            date_string = current_date.strftime('%d %B %Y')
            date_list_string.append(date_string)
            clicks = Click.objects.filter(Q(time_create__date=current_date.date()) & Q(link_id=link_id))
            click_count = clicks.count()
            click_count_list.append(click_count)
            current_date += timedelta(days=1)

        clicks_country = Click.objects.filter(time_create__range=(start_date, end_date), link_id=link_id).values('country').annotate(clicks_count=Count('id'))
        #clicks_country = Click.objects.values('country').annotate(clicks_count=Count('id'))
        countries = [item['country'] for item in clicks_country]

        #clicks_device = Click.objects.values('device').annotate(clicks_count=Count('id'))
        clicks_device = Click.objects.filter(time_create__range=(start_date, end_date), link_id=link_id).values('device').annotate(clicks_count=Count('id'))
        devices = [item['device'] for item in clicks_device]
        country_clicks_count = [item['clicks_count'] for item in clicks_country]
        device_clicks_count = [item['clicks_count'] for item in clicks_device]
        #link = Link.objects.get(id=link_id)
        kyiv_tz = timezone('Europe/Kiev')
        current_datetime = datetime.now(kyiv_tz)
        #start_date = current_datetime - timedelta(days=5)
        #current_date = current_datetime.replace(hour=23, minute=59, second=59)
        #start_date_utc = start_date.astimezone(timezone('UTC'))
        #current_date_utc = current_date.astimezone(timezone('UTC'))
        clicks = Click.objects.filter(
            Q(time_create__gte=start_date, time_create__lte=end_date) &
            Q(link_id=link_id)
        )
        print(clicks_country)
        serializer = ClickSerializer(clicks, many=True)
        response_data = {'clicks': serializer.data, 'clicks_count': click_count_list, 'labels': date_list_string, 'country_labels': countries, 'country_clicks_count':country_clicks_count, 'device_labels': devices, 'device_clicks_count':device_clicks_count}
        return Response(response_data)