from django.core.exceptions import PermissionDenied

def is_assembly_team(user):
    return user.profile.team and user.profile.team.name.lower() == 'montaj takımı'

def assembly_team_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not is_assembly_team(request.user):
            raise PermissionDenied("Bu işlemi yalnızca montaj takımı gerçekleştirebilir.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view
