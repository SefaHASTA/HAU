from django.db import models
from django.contrib.auth.models import User
from rest_framework import serializers

class AircraftType(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

# Uçak türü modeli
class Aircraft(models.Model):
    name = models.CharField(max_length=100, unique=True)
    aircraft_type = models.ForeignKey(AircraftType, on_delete=models.CASCADE)
    def __str__(self):
        return self.name

# Parça türü modeli
class PartType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

# Takım modeli
class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    responsible_part = models.ForeignKey(PartType, on_delete=models.CASCADE, null=True, blank=True)
    members = models.ManyToManyField('Profile', through='TeamMember', related_name='teams')

    def __str__(self):
        return self.name

# Kullanıcı profili modeli
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.user.username

# Takım üyeliği modeli
class TeamMember(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, blank=True, null=True)
    join_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile} - {self.team.name} ({self.role})"


# Parça modeli
class Part(models.Model):
    part_type = models.ForeignKey(PartType, on_delete=models.CASCADE)
    aircraft_type = models.ForeignKey(AircraftType, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)
    quantity = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # used_in_aircraft = models.ManyToManyField(Aircraft, related_name="parts", blank= True)  # ManyToMany ilişki
    used_in_aircraft = models.ManyToManyField('BuiltAircraft', blank=True)

    def __str__(self):
        return self.part_type.name

# Üretilmiş uçak (tamamlanmış üretim kaydı)
class BuiltAircraft(models.Model):
    aircraft_type = models.ForeignKey(AircraftType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    parts = models.ManyToManyField(Part)

    def __str__(self):
        return f"{self.aircraft_type.name} - #{self.id}"

    def is_complete(self):
        required_part_types = PartType.objects.all()
        used_part_types = self.part_usages.values_list('part__part_type', flat=True).distinct()
        return all(part_type.id in used_part_types for part_type in required_part_types)

# Üretim geçmişi (isteğe bağlı)
class ProducedAircraft(models.Model):
    aircraft_type = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    production_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.aircraft_type.name} - {self.production_date}"

# Uçak-Parça türü uyumu
class AircraftPartCompatibility(models.Model):
    aircraft_type = models.ForeignKey(Aircraft, on_delete=models.CASCADE)
    part_type = models.ForeignKey(PartType, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.aircraft_type.name} - {self.part_type.name}"

# Parça Kullanımı: Hangi uçakta hangi parçadan ne kadar kullanıldı
class PartUsage(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    built_aircraft = models.ForeignKey(BuiltAircraft, on_delete=models.CASCADE, related_name='part_usages')
    quantity_used = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.part.part_type.name} - {self.built_aircraft.aircraft_type.name} ({self.quantity_used} adet)"


class PartSerializer(serializers.ModelSerializer):
    used_in_aircraft = serializers.SerializerMethodField()
    part_type = serializers.StringRelatedField()
    aircraft_type = serializers.StringRelatedField()
    team = serializers.StringRelatedField()
    is_used = serializers.SerializerMethodField()

    class Meta:
        model = Part
        fields = ['part_type', 'aircraft_type', 'team', 'is_used', 'created_at', 'used_in_aircraft']

    def get_used_in_aircraft(self, obj):
        return obj.used_in_aircraft.id if obj.used_in_aircraft else None

    def get_is_used(self, obj):
        return "Kullanıldı" if obj.is_used else "Kullanılmadı"


