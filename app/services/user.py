import app.crud.user as crud


def create_profile(db, payload):
    return crud.create_user(payload)


def get_profile(db, user_id):
    return crud.get_user_by_id(user_id)


def modify_profile(db, user_id, payload):
    return crud.update_user(user_id, payload)
