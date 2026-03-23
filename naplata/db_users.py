from django.contrib.auth import get_user_model
from django.db import DEFAULT_DB_ALIAS


def resolve_user_pk_for_db(user, db_alias):
    db_alias = db_alias or DEFAULT_DB_ALIAS

    if not getattr(user, "is_authenticated", False):
        return None

    user_model = get_user_model()
    if user_model.objects.using(db_alias).filter(pk=user.pk).exists():
        return user.pk

    username = (getattr(user, "username", "") or "").strip()
    if not username:
        return None

    return (
        user_model.objects.using(db_alias)
        .filter(username=username)
        .values_list("pk", flat=True)
        .first()
    )
