from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login as django_login
# import requests
from django.http import JsonResponse
from django.views import View
from .models import Profile, Team, PartType, Part, Aircraft, BuiltAircraft, PartUsage, AircraftType
from .forms import PartCreateForm
from django.core.paginator import Paginator
from django.utils.dateformat import DateFormat
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import BuiltAircraft, PartType, Part
from .permissions import assembly_team_required  # Montaj Takımı için yetki kontrolü

from django.db import transaction, connection
from django.utils import timezone

from rest_framework import serializers
from rest_framework import viewsets




# ✅ API endpoint (JSON) - Menü
class MenuView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "user": user.username,
            "menu": [
                {"name": "Dashboard", "url": "/dashboard"},
                {"name": "Profile", "url": "/profile"},
                {"name": "Settings", "url": "/settings"},
            ]
        })


# ✅ API endpoint for server-side datatable (Parçalar listesi)
class PartListView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        team = request.user.profile.team
        parts = Part.objects.filter(team=team)

        draw = int(request.GET.get('draw', 1))
        start = int(request.GET.get('start', 0))
        length = int(request.GET.get('length', 10))
        search_value = request.GET.get('search[value]', '')

        if search_value:
            parts = parts.filter(part_type__name__icontains=search_value)

        total = parts.count()
        paginator = Paginator(parts, length)
        page_number = (start // length) + 1
        page = paginator.get_page(page_number)

        data = []
        for part in page.object_list:
            data.append({
                'id': part.id,
                'part_type': part.part_type.name,
                'aircraft_type': part.aircraft_type.name,
                'created_at': DateFormat(part.created_at).format('Y-m-d H:i')
            })

        return JsonResponse({
            'draw': draw,
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': data
        })

# Login page
def login_page(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            next_url = request.POST.get('next')
            if next_url:  # next parametresi varsa direkt oraya yönlendir
                return redirect(next_url)
            else:
                return redirect('menu-page')  # yoksa varsayılan sayfaya yönlendir
        else:
            messages.error(request, 'Geçersiz kullanıcı adı veya şifre.')

    return render(request, 'accounts/login.html')

@method_decorator(csrf_exempt, name='dispatch')
class DeletePartView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        import json
        data = json.loads(request.body)
        part_id = data.get('id')

        try:
            part = Part.objects.get(id=part_id, team=request.user.profile.team)
            part.delete()
            return JsonResponse({'success': True})
        except Part.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Parça bulunamadı'}, status=404)


# Menu page
@login_required(login_url='/api/login-page/')
def menu_page(request):
    return render(request, 'accounts/menu.html', {
        'user': request.user
    })


# Logout page
def logout_page(request):
    # Oturumdan çıkış yap
    request.session.flush()  # Session'ı temizler
    return redirect('html_login')  # Giriş sayfasına yönlendir


# Register page
def register_page(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hesap başarıyla oluşturuldu!')
            return redirect('html_login')
        else:
            messages.error(request, 'Lütfen bilgileri doğru girdiğinizden emin olun.')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required(login_url='/api/login-page/')
def create_part(request):
    profile = Profile.objects.get(user=request.user)
    team = profile.team
    part_type = team.responsible_part

    if not part_type:
        messages.error(request, "Sorumlu olduğunuz bir parça türü yok.")
        return redirect('menu-page')

    if request.method == 'POST':
        form = PartCreateForm(request.POST, user_team=team.name)
        if form.is_valid():
            part = form.save(commit=False)
            part.team = team
            part.part_type = part_type  # Takımın sabit parça türü atanır
            part.save()
            messages.success(request, f'{part_type} parçası başarıyla üretildi.')
            return redirect('create_part')
        else:
            # Form hatalarını kontrol et
            messages.error(request, "Formda hata var. Lütfen tekrar deneyin.")
            print(form.errors)  # Hata mesajlarını terminale yazdırın
    else:
        form = PartCreateForm(user_team=team.name)

    # Bu takımın daha önce ürettiği parçalar
    team_parts = Part.objects.filter(team=team).order_by('-created_at')

    return render(request, 'factory/create_part.html', {
        'form': form,
        'part_type': part_type,
        'team_parts': team_parts,
    })


# Montaj takımı kontrolü
@login_required
def check_assembly_team(user):
    profile = Profile.objects.get(user=user)
    if profile.team.name != 'Montaj Takımı':  # Takım adı kontrolü
        messages.error("Bu işlemi sadece Montaj Takımı üyeleri yapabilir.")
        return redirect('menu-page')



# Uçak üretim fonksiyonu
@login_required
def create_aircraft(request):
    profile = Profile.objects.get(user=request.user)

    # Montaj Takımı kontrolü
    if profile.team.name != 'Montaj Takımı':
        return redirect('menu-page')
        # raise PermissionDenied("Bu işlemi sadece Montaj Takımı üyeleri yapabilir.")

    # Uçak türünü seçiyoruz (örnek: 'TB2')
    aircraft_type = Aircraft.objects.first()  # Veya kullanıcıdan seçilen uçak tipi alınabilir

    # Uçak için gereken parçalar
    required_parts = PartType.objects.all()

    # Eksik parçaların tespiti
    missing_parts = []

    for part_type in required_parts:
        # Eksik parça var mı diye kontrol ediyoruz
        part_count = Part.objects.filter(part_type=part_type, is_used=False, quantity__gt=0).count()
        if part_count == 0:
            missing_parts.append(part_type)

    if missing_parts:
        # Eksik parçalar varsa kullanıcıya bildirilir
        missing_part_names = ', '.join([part.name for part in missing_parts])
        messages.error(request, f"Eksik parçalar: {missing_part_names}. Lütfen eksik parçaları tamamlayın.")
        return redirect('create_aircraft')  # Tekrar uçak üretme sayfasına yönlendirme

    # Tüm parçalar mevcutsa, uçağı üret
    built_aircraft = BuiltAircraft.objects.create(aircraft_type=aircraft_type)

    # Parçaları ilişkilendir ve kaydedilen her parça için `PartUsage` oluştur
    for part in Part.objects.filter(aircraft_type=aircraft_type, is_used=False):
        # Parça kullanılmadan önce miktarını kontrol ediyoruz
        if part.quantity > 0 and not part.is_used:
            built_aircraft.parts.add(part)
            part.is_used = True
            # part.quantity -= 1  # Parça miktarını azaltıyoruz
            part.save()

            # PartUsage kaydını oluşturuyoruz
            PartUsage.objects.create(
                part=part,
                built_aircraft=built_aircraft,
                quantity_used=1  # Burada her parça için miktar 1 kabul ediliyor, ihtiyaca göre değiştirilebilir
            )

    # Başarı mesajı
    messages.success(request, f"{aircraft_type.name} başarıyla üretildi.")
    return redirect('create_aircraft')


@login_required
@assembly_team_required
@transaction.atomic
def build_aircraft(request):
    if request.method == "POST":
        # Uçak tipi seçimi
        aircraft_id = request.POST.get("aircraft_type")
        aircraft = Aircraft.objects.get(id=aircraft_id)
        aircraft_type = aircraft.aircraft_type

        # Uçak için gerekli parçalar
        required_parts = Part.objects.filter(aircraft_type=aircraft_type, is_used=False)

        # Eksik parçaların kontrolü
        missing_parts = []
        for part in required_parts:
            if part.quantity <= 0:
                missing_parts.append(part)

        if missing_parts:
            part_names = ", ".join([part.part_type.name for part in missing_parts])
            messages.error(request, f"Eksik parçalar: {part_names}.")
            return redirect("build-aircraft")

        # Uçak üretimi
        built_aircraft = BuiltAircraft.objects.create(aircraft_type=aircraft_type)

        # Parçaları ilişkilendiriyoruz
        for part in required_parts:
            if part.quantity > 0:
                part.is_used = True
                part.quantity -= 1
                part.used_in_aircraft.add(built_aircraft)  # Parçayı uçağa ilişkilendir
                part.save()

        messages.success(request, f"{aircraft.name} uçağı başarıyla üretildi.")
        return redirect("build-aircraft")

    aircraft_types = Aircraft.objects.all()
    return render(request, "build_aircraft.html", {
        "aircraft_types": aircraft_types
    })

@login_required
@assembly_team_required
@transaction.atomic
def build_aircraft_view(request):
    if request.method == 'POST':
        aircraft_id = request.POST.get('aircraft_type')
        aircraft = Aircraft.objects.get(id=aircraft_id)

        # Aircraft'ın 'aircraft_type' ilişkisini kontrol et
        aircraft_type = aircraft.aircraft_type  # aircraft_type doğru ilişki

        required_parts = PartType.objects.all()
        selected_parts = []

        for part_type in required_parts:
            part = Part.objects.filter(
                part_type=part_type,
                aircraft_type=aircraft_type,  # doğru ilişki burada kullanılıyor
                is_used=False  # Boolean False değeri ile kontrol ediyoruz
            ).first()

            if part:
                selected_parts.append(part)
            else:
                messages.error(request, f"{aircraft.name} için gerekli {part_type.name} parçası eksik.")
                return redirect('build_aircraft')

        # Uçak üretimi için BuiltAircraft oluşturuluyor
        built_aircraft = BuiltAircraft.objects.create(aircraft_type=aircraft_type)

        # Seçilen parçaları ekleyelim
        for part in selected_parts:
            part.is_used = True  # Parçayı kullanılmış olarak işaretliyoruz
            part.save()  # Parçayı güncelliyoruz

            built_aircraft.parts.add(part)  # Parçayı uçağa ekliyoruz

        built_aircraft.save()  # Uçağı kaydediyoruz

        messages.success(request, f"{aircraft.name} uçağı başarıyla üretildi.")
        return redirect('build_aircraft')

    aircraft_types = Aircraft.objects.all()
    return render(request, 'build_aircraft.html', {
        'aircraft_types': aircraft_types
    })


@login_required
@assembly_team_required
def built_aircraft_list_view(request):
    built_aircrafts = BuiltAircraft.objects.prefetch_related('parts', 'aircraft_type').order_by('-created_at')
    return render(request, 'built_aircraft_list.html', {'built_aircrafts': built_aircrafts})


def produced_aircrafts_api(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    search_value = request.GET.get("search[value]", "").strip()

    queryset = BuiltAircraft.objects.prefetch_related('parts', 'aircraft_type')

    # Eğer arama varsa
    if search_value:
        queryset = queryset.filter(aircraft_type__name__icontains=search_value)

    total = queryset.count()

    # Sıralama işlemi
    order_column = request.GET.get('order[0][column]', 0)  # Sıralama için kolonu alıyoruz
    order_direction = request.GET.get('order[0][dir]', 'asc')  # Yönü alıyoruz

    # Eğer sıralama varsa
    if order_column == '0':
        queryset = queryset.order_by('aircraft_type__name' if order_direction == 'asc' else '-aircraft_type__name')
    elif order_column == '1':
        queryset = queryset.order_by('created_at' if order_direction == 'asc' else '-created_at')

    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page = paginator.get_page(page_number)

    data = []
    for aircraft in page:
        part_count = aircraft.parts.count()
        data.append({
            "id": aircraft.id,
            "aircraft_type": aircraft.aircraft_type.name,
            "created_at": aircraft.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "part_count": part_count
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,  # Filtrelenmiş ve toplam veri sayısı
        "data": data
    })
def all_parts_api(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))
    search_value = request.GET.get("search[value]", "").strip()
    order_column = int(request.GET.get("order[0][column]", 0))  # Sıralama kolonunu alıyoruz
    order_dir = request.GET.get("order[0][dir]", "asc")  # Sıralama yönünü alıyoruz

    # SQL sorgusunu yazıyoruz
    query = """
    SELECT 
        parts.id AS part_id,
        pt.name AS part_type,  -- part_type'ın ismini alıyoruz
        at.name AS aircraft_type,  -- aircraft_type'ın ismini alıyoruz
        t.name AS team,  -- team'in ismini alıyoruz
        CASE 
            WHEN parts.is_used THEN 'Kullanıldı' 
            ELSE 'Kullanılmadı' 
        END AS is_used,  -- Kullanım durumu
        parts.created_at,
        built_aircraft.id AS built_aircraft_id,
        built_aircraft.created_at AS production_date
    FROM public.accounts_part AS parts
    LEFT JOIN public.accounts_parttype AS pt ON parts.part_type_id = pt.id
    LEFT JOIN public.accounts_aircrafttype AS at ON parts.aircraft_type_id = at.id
    LEFT JOIN public.accounts_team AS t ON parts.team_id = t.id
    LEFT JOIN public.accounts_builtaircraft_parts AS bap ON bap.part_id = parts.id
    LEFT JOIN public.accounts_builtaircraft AS built_aircraft ON bap.builtaircraft_id = built_aircraft.id
    """

    # Filtreleme sorgusunu ekliyoruz
    if search_value:
        query += f" WHERE pt.name ILIKE '%{search_value}%' OR at.name ILIKE '%{search_value}%' OR t.name ILIKE '%{search_value}%'"

    # Sıralama sorgusunu ekliyoruz
    order_columns = ['part_type', 'aircraft_type', 'team', 'is_used', 'created_at', 'production_date']
    query += f" ORDER BY {order_columns[order_column]} {order_dir}"

    # Sayfalama parametrelerini ekliyoruz
    query += f" LIMIT {length} OFFSET {start}"

    # Veritabanı sorgusu çalıştırılıyor
    with connection.cursor() as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()

    # Veriyi işleyerek JSON formatına dönüştürüyoruz
    data = []
    for row in rows:
        part_id, part_type, aircraft_type, team, is_used, created_at, built_aircraft_id, production_date = row
        data.append({
            "part_id": part_id,
            "part_type": part_type,
            "aircraft_type": aircraft_type,
            "team": team,
            "is_used": is_used,
            "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "built_aircraft_id": built_aircraft_id,
            "production_date": production_date.strftime("%Y-%m-%d %H:%M:%S") if production_date else None
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": len(rows),
        "recordsFiltered": len(rows),
        "data": data
    })
class AircraftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aircraft
        fields = ['id', 'name']  # Gerekli alanları burada belirleyebilirsiniz

class PartSerializer(serializers.ModelSerializer):

    used_in_aircraft = AircraftSerializer(many=True, read_only=True)

    class Meta:
        model = Part
        fields = ['part_type', 'aircraft_type', 'team', 'is_used',  'created_at']

    def get_used_in(self, obj):
        # used_in, ilgili uçak ID'lerini döndürecek
        return [aircraft.id for aircraft in obj.used_in_aircraft.all()]

class PartViewSet(viewsets.ModelViewSet):
    queryset = Part.objects.select_related('aircraft_type', 'team')
    serializer_class = PartSerializer


def assemble_aircraft(aircraft, user):
    required_parts = PartType.objects.all()
    selected_parts = []

    for part_type in required_parts:
        part = Part.objects.filter(
            part_type=part_type,
            aircraft_type=aircraft,
            is_used=False
        ).first()

        if not part:
            return False, f"{aircraft.name} için gerekli {part_type.name} parçası eksik."

        selected_parts.append(part)

    built_aircraft = BuiltAircraft.objects.create(aircraft_type=aircraft)
    for part in selected_parts:
        part.is_used = True
        part.save()
        built_aircraft.parts.add(part)
        PartUsage.objects.create(part=part, built_aircraft=built_aircraft, quantity_used=1)

    return True, f"{aircraft.name} başarıyla üretildi."


