from app import db, Role
# from sqlalchemy.orm import Session
db.drop_all()
db.create_all()

roles = [
    Role(name='user'),
    Role(name='tutor'),
    Role(name='regional_operator'),
    Role(name='federal_operator'),
    Role(name='system'),
]
# insert roles
db.session.bulk_save_objects(roles)
db.session.commit()
