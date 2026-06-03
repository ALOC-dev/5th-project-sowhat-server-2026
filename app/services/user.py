import app.crud.user as crud


def create_user(db, payload):
    return crud.create_user(db, payload)


def get_user(db, user_id):
    return crud.get_user_by_id(db, user_id)


def modify_user(db, user_id, payload):
    return crud.update_user(db, user_id, payload)
