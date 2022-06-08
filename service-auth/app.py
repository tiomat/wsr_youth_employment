from flask import Flask, jsonify, make_response, request
from flask_marshmallow import Marshmallow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from jwcrypto import jwk

import uuid

# creates Flask object
app = Flask(__name__)
# add Marshmallow
ma = Marshmallow(app)

# configuration
# NEVER HARDCODE YOUR CONFIGURATION IN YOUR CODE
# INSTEAD CREATE A .env FILE AND STORE IN IT


# AUTH
# Create JWK for auth
key = jwk.JWK.generate(kty='RSA', size=512, kid="auth")
private_key_export = key.export(as_dict=True)
public_key_export = key.export_public(as_dict=True)
# Time delta for token lifetime
jwt_timedelta = 1

# database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///service_auth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


# creates SQLALCHEMY object
db = SQLAlchemy(app)


# Database ORMs

# Many Users to Many Roles
user_to_roles_association = db.Table(
    "users_to_roles",
    db.Model.metadata,
    db.Column("role_id", db.Integer, ForeignKey("roles.id")),
    db.Column("user_id", db.Integer, ForeignKey("users.id")),
)


# Users
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    # role = db.Column(db.String(50))
    roles = db.relationship("Role", secondary=user_to_roles_association)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(80))


# Roles
class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))

# Role Schema


class RoleSchema(ma.Schema):
    class Meta:
        model: Role
        fields = ("id", "name")


# Role Schema Mapping
role_schema = RoleSchema()
roles_schema = RoleSchema(many=True)


# User Schema
class UserSchema(ma.Schema):
    roles = ma.Nested(RoleSchema, many=True)

    class Meta:
        model = User
        # Fields to expose
        fields = ("id", "public_id", "name", "email", "roles", "_links")


# User Schema Mapping
user_schema = UserSchema()
users_schema = UserSchema(many=True)


# Response template
def custom_reponse(data, status=200, always_ok=True):
    if always_ok:
        http_status = 200
    else:
        http_status = status

    return make_response(
        jsonify({
                "status": status,
                "data": data
                }),
        http_status)


# Routes

# Users
# GET – get all users
# POST – create new user
@ app.route("/users/", methods=["GET", "POST"])
def users():
    all_users = User.query.all()
    return custom_reponse(users_schema.dump(all_users))


# GET – get user by id
# PUT – update user by id
@ app.route("/users/<id>", methods=["GET", "PUT"])
def users_detail(id):
    user = User.query.get(id)
    if not user:
        return custom_reponse("Not found", 404)
    return custom_reponse(user_schema.dump(user))


# Roles
# GET – get all roles
# POST – N/A
@ app.route("/roles/", methods=["GET"])
def roles():
    all_users = Role.query.all()
    return custom_reponse(roles_schema.dump(all_users))


# GET – get role by id
# PUT – N/A
@ app.route("/roles/<id>")
def roles_detail(id):
    role = Role.query.get(id)
    if not role:
        return custom_reponse("Not found", 404)
    return custom_reponse(role_schema.dump(role))


# route for logging user in
@ app.route('/login', methods=['POST'])
def login():
    # creates dictionary of form data
    auth = request.form

    if not auth or not auth.get('email') or not auth.get('password'):
        # returns 401 if any email or / and password is missing
        return custom_reponse("Can't find required fileds: email or password", 400)

    user = User.query.filter_by(email=auth.get('email')).first()
    # user = User.query\
    #     .filter_by(email=auth.get('email'))\
    #     .first()
    print(user)
    if not user:
        # returns 401 if user does not exist
        return custom_reponse("Could not verify", 401)

    if check_password_hash(user.password, auth.get('password')):

        exp = datetime.now() + timedelta(hours=jwt_timedelta)
        exp = exp.timestamp()

        # Map roles to list
        user_roles = roles_schema.dump(user.roles)
        list_roles = []
        for el in user_roles:
            list_roles.append(el["name"])

        token = {
            'id': user.id,
            'public_id': user.public_id,
            'roles': list_roles,
            'exp': exp
        }

        print(token)
        return make_response(jsonify({'access_token': token, "exp": exp}), 200)

    # returns 403 if password is wrong
    return custom_reponse("Could not verify", 401)


# signup route
@app.route('/signup', methods=['POST'])
def signup():
    # creates a dictionary of the form data
    data = request.form

    # gets name, email and password
    name, email = data.get('name'), data.get('email')
    password = data.get('password')
    role_name = data.get('role', default='user')

    # checking for existing user
    user = User.query.filter_by(email=email).first()
    role = Role.query.filter_by(name=role_name).first()

    if not role:
        role = Role.query.get(name='user')

    if not user:
        # database ORM object
        user = User(
            public_id=str(uuid.uuid4()),
            name=name,
            email=email,
            password=generate_password_hash(password)
        )
        # insert user

        user.roles.append(role)

        db.session.add(user)
        db.session.commit()

        return custom_reponse("Created")
    else:
        # returns 202 if user already exists
        return custom_reponse("User already exist")


@app.route('/jwt', methods=['GET'])
def info():
    data = {
        "keys": [private_key_export]
    }
    return jsonify(data)


@app.route('/jwtpub', methods=['GET'])
def pubinfo():

    data = {
        "keys": [public_key_export]
    }
    return jsonify(data)


if __name__ == "__main__":
    # setting debug to True enables hot reload
    # and also provides a debugger shell
    # if you hit an error while running the server
    app.debug = True
    app.run(host="0.0.0.0", port="4000")
