# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile, Team, TeamMember

# Yeni kullanıcı oluşturulduğunda, varsayılan bir takım ekleyip profili oluşturuyoruz
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:  # Yalnızca kullanıcı oluşturulmuşsa
        team = Team.objects.first()  # Varsayılan bir takım alınıyor
        if not team:
            # Eğer hiç takım yoksa, varsayılan bir takım oluşturuluyor
            team = Team.objects.create(name="Default Team")  # Takım adı "Default Team"
        Profile.objects.create(user=instance, team=team)  # Profil oluşturuluyor

# Kullanıcı profili güncellendiğinde, takım bilgilerini de kaydediyoruz
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()  # Profil kaydını her güncellediğinizde de kaydedin

# Takım değiştiğinde, TeamMember tablosuna da yeni kayıt ekliyoruz
@receiver(post_save, sender=Profile)
def create_or_update_team_member(sender, instance, created, **kwargs):
    if instance.team:
        # Profilin takımı varsa, TeamMember tablosunda bir kayıt oluşturuyoruz
        team_member, created = TeamMember.objects.get_or_create(profile=instance, team=instance.team)
        # Eğer takım değiştiyse, mevcut kaydı güncelliyoruz
        if not created:
            team_member.team = instance.team
            team_member.save()
