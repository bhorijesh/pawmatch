SHELTER_STAFF_GROUP = 'shelter_staff'


def is_shelter_staff(user):
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=SHELTER_STAFF_GROUP).exists()
