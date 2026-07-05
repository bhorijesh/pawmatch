from .permissions import is_shelter_staff


def user_roles(request):
    return {'is_shelter_staff': is_shelter_staff(request.user)}
