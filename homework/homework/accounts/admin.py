from django.contrib import admin
from .models import Team, Profile, TeamMember, Part, Aircraft, PartType, BuiltAircraft, AircraftPartCompatibility, PartUsage, AircraftType, ProducedAircraft

# Takımların admin panelinde gösterileceği düzenleme
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'responsible_part')  # Takım adı ve sorumlu parça
    # Takım üyelerini buradan yönetmek yerine, TeamMember ile ilişkilendirilecek

# Kullanıcı profillerinin admin panelinde gösterileceği düzenleme
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'team')  # Kullanıcı adı ve bağlı oldukları takım

# Takım üyelerinin admin panelinde gösterileceği düzenleme
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('profile', 'team', 'role', 'join_date')  # Üye, takım, rol ve katılım tarihi
    list_filter = ('team',)  # Takıma göre filtreleme yapılacak

# Parçaların admin panelinde gösterileceği düzenleme
class PartAdmin(admin.ModelAdmin):
    list_display = ('part_type', 'aircraft_type', 'team', 'is_used', 'created_at')  # Parça bilgileri
    list_filter = ('team', 'aircraft_type')  # Takıma ve uçak türüne göre filtreleme yapılacak

# Uçakların admin panelinde gösterileceği düzenleme
class AircraftAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Uçak adı

# Parça türlerinin admin panelinde gösterileceği düzenleme
class PartTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)  # Parça türü adı

# Üretilen uçakların admin panelinde gösterileceği düzenleme
class BuiltAircraftAdmin(admin.ModelAdmin):
    list_display = ('aircraft_type', 'created_at')  # Uçak türü ve üretim tarihi
    list_filter = ('aircraft_type',)  # Uçak türüne göre filtreleme yapılacak

# AircraftPartCompatibility için admin paneli düzenlemesi
class AircraftPartCompatibilityAdmin(admin.ModelAdmin):
    list_display = ('aircraft_type', 'part_type')  # Uçak türü ve parça türü uyumu
    list_filter = ('aircraft_type', 'part_type')  # Uçak türü ve parça türüne göre filtreleme

# Admin panelinde modelleri kaydediyoruz
admin.site.register(Team, TeamAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(TeamMember, TeamMemberAdmin)
# admin.site.register(Part, PartAdmin)
admin.site.register(Aircraft, AircraftAdmin)
admin.site.register(PartType, PartTypeAdmin)
admin.site.register(BuiltAircraft, BuiltAircraftAdmin)
admin.site.register(AircraftPartCompatibility, AircraftPartCompatibilityAdmin)

class PartUsageAdmin(admin.ModelAdmin):
    list_display = ('part', 'built_aircraft', 'quantity_used', 'created_at')
    list_filter = ('built_aircraft', 'part')  # Parça ve üretilen uçak türüne göre filtreleme yapılacak

admin.site.register(PartUsage, PartUsageAdmin)

# @admin.register(Part)
# class PartAdmin(admin.ModelAdmin):
#     list_display = ('part_type', 'aircraft_type', 'team', 'quantity', 'is_used', 'created_at')  # Parça bilgileri
#     list_filter = ('team', 'aircraft_type')  # Takıma ve uçak türüne göre filtreleme yapılacak




class BuiltAircraftAdmin(admin.ModelAdmin):
    list_display = ('aircraft_type', 'created_at', 'get_missing_parts')  # Eksik parçaları göstermek için yeni bir fonksiyon ekliyoruz
    list_filter = ('aircraft_type',)

    def get_missing_parts(self, obj):
        missing_parts = []
        required_parts = PartType.objects.all()
        for part_type in required_parts:
            if part_type not in obj.parts.values_list('part_type', flat=True):
                missing_parts.append(part_type.name)
        return ", ".join(missing_parts) if missing_parts else "Tüm parçalar mevcut"
    get_missing_parts.short_description = 'Eksik Parçalar'



admin.site.register(Part)
admin.site.register(ProducedAircraft)

@admin.register(AircraftType)
class AircraftTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')  # Uçak tipi bilgileri