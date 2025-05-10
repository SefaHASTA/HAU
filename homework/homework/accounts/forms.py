from django import forms
from .models import Part, Team, PartType


class PartCreateForm(forms.ModelForm):
    class Meta:
        model = Part
        fields = ['part_type', 'aircraft_type', 'team']
        widgets = {
            'part_type': forms.Select(attrs={'class': 'form-control'}),
            'aircraft_type': forms.Select(attrs={'class': 'form-control'}),
            'team': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        user_team_name = kwargs.pop('user_team', None)  # 'user_team' parametresini alıyoruz
        super().__init__(*args, **kwargs)

        if user_team_name:
            try:
                # Takımın detaylarını alıyoruz
                team = Team.objects.get(name=user_team_name)

                # Takımın sorumlu olduğu part_type'ı dropdown olarak getiriyoruz
                if team.responsible_part:
                    self.fields['part_type'].queryset = PartType.objects.filter(id=team.responsible_part.id)
                else:
                    self.fields['part_type'].queryset = PartType.objects.none()  # Eğer responsible_part yoksa, boş liste

                # Takım bilgisini de dropdown olarak ekliyoruz
                self.fields['team'].queryset = Team.objects.filter(id=team.id)

                # Eğer team.responsible_part None ise, part_type alanını boş bırakabilirsiniz
                if team.responsible_part is None:
                    self.fields['part_type'].required = False

            except Team.DoesNotExist:
                # Hata durumunda
                self.fields['team'].queryset = Team.objects.none()  # Hiçbir takım gösterilmesin
                self.fields['part_type'].queryset = PartType.objects.none()  # Hiçbir parça türü gösterilmesin
                print("Team not found!")

    def clean(self):
        cleaned_data = super().clean()
        team = cleaned_data.get('team')
        part_type = cleaned_data.get('part_type')

        # Kullanıcının takımı ile parça türünün uyumlu olup olmadığını kontrol et
        if team and part_type and team.responsible_part != part_type:
            raise forms.ValidationError(
                f"{team.name} takımı yalnızca {team.responsible_part.name} parçalarını üretebilir."
            )

        return cleaned_data
