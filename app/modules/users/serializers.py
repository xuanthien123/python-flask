def serialize_user_profile(user):
    profile = serialize_user(user)
    profile.update({
        'address': user.address,
        'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
        'sex': user.sex,
        'email_verified_at': user.email_verified_at.isoformat() if user.email_verified_at else None,
    })
    return profile


def serialize_user(user):
    return {
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'roles': [role.name for role in user.roles],
    }
