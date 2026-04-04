import app.crud.user as crud


def create_profile(db, payload):
    return crud.create_user(payload)
