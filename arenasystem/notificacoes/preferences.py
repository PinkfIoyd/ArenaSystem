def notification_allowed(user, category, channel='app'):
    field = f'{channel}_{category}'
    try:
        preference = user.notification_preferences
    except Exception:
        return True
    return bool(getattr(preference, field, True))
