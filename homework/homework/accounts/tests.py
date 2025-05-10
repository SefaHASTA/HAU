from django.test import TestCase
from django.contrib.auth.models import User
from .models import Team, Profile, PartType, TeamMember

class TeamModelTest(TestCase):
    def setUp(self):
        # PartType ve Team nesnelerini doğru şekilde oluşturun.
        self.part_type = PartType.objects.create(name="Montaj Ekibi")
        self.team = Team.objects.create(name="Montaj Ekibi", responsible_part=self.part_type)

    def test_team_creation(self):
        # Ekip adı ve sorumlu parça adı doğru mu diye kontrol edin.
        self.assertEqual(self.team.name, "Montaj Ekibi")
        self.assertEqual(self.team.responsible_part.name, "Montaj Ekibi")

class ProfileModelTest(TestCase):
    def setUp(self):
        # Kullanıcı, takım ve profil nesnelerini doğru oluşturun.
        self.user = User.objects.create_user(username="kanat_user1", password="Kanat123*")
        self.part_type = PartType.objects.create(name="Kanat")
        self.team = Team.objects.create(name="Kanat Takımı", responsible_part=self.part_type)
        self.profile = Profile.objects.create(user=self.user, team=self.team)

    def test_profile_creation(self):
        # Profilin doğru oluşturulduğundan emin olun.
        self.assertEqual(self.profile.user.username, "kanat_user1")
        self.assertEqual(self.profile.team.name, "Kanat Takımı")

    def test_add_profile_to_team(self):
        # Takıma profil ekleyin ve doğru şekilde kaydedildiğini kontrol edin.
        member = TeamMember.objects.create(profile=self.profile, team=self.team, role="member")
        self.assertEqual(member.role, "member")  # Küçük harflerle "member"
        self.assertEqual(member.profile.user.username, "kanat_user1")
