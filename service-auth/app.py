from flask import Flask, request, jsonify, make_response
from flask_marshmallow import Marshmallow
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import declarative_base, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from jwcrypto import jwk

import uuid

# creates Flask object
app = Flask(__name__)
# add Marshmallow
ma = Marshmallow(app)
# add Flask RESTfull api
api = Api(app)


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

# Make the DeclarativeMeta
Base = declarative_base()


# Database ORMs
# Users and roles
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    role = db.Column(db.String(50))
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(80))


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))


association_table = db.Table(
    "association",
    db.Model.metadata,
    db.Column("role_id", db.Integer, ForeignKey("roles.id")),
    db.Column("user_id", db.Integer, ForeignKey("users.id")),
)


class HelloWorld(Resource):
    def get(self):
        return {'hello': 'world'}


api.add_resource(HelloWorld, '/')

# User Database Route
# this route sends back list of users


@app.route('/users', methods=['GET'])
def list_users():
    # querying the database
    # for all the entries in it
    users = User.query.all()
    # converting the query objects
    # to list of jsons
    output = []
    for user in users:
        # appending the user data json
        # to the response list
        output.append({
            'id': user.id,
            'public_id': user.public_id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        })

    return jsonify({'users': output})


# route for logging user in
@app.route('/login', methods=['POST'])
def login():
    # creates dictionary of form data
    auth = request.form
    print(auth)
    if not auth or not auth.get('email') or not auth.get('password'):
        # returns 401 if any email or / and password is missing
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="Login required !!"'}
        )

    user = User.query\
        .filter_by(email=auth.get('email'))\
        .first()

    if not user:
        # returns 401 if user does not exist
        return make_response(
            'Could not verify',
            401,
            {'WWW-Authenticate': 'Basic realm ="User does not exist !!"'}
        )

    if check_password_hash(user.password, auth.get('password')):

        exp = datetime.now() + timedelta(hours=jwt_timedelta)
        exp = exp.timestamp()

        token = {
            'id': user.id,
            'public_id': user.public_id,
            'role': [user.role],
            'exp': exp
        }

        print(token)
        return make_response(jsonify({'access_token': token}), 201)

    # returns 403 if password is wrong
    return make_response(
        'Could not verify',
        403,
        {'WWW-Authenticate': 'Basic realm ="Wrong Password !!"'}
    )


# signup route
@app.route('/signup', methods=['POST'])
def signup():
    # creates a dictionary of the form data
    data = request.form

    # gets name, email and password
    name, email = data.get('name'), data.get('email')
    password = data.get('password')
    role = data.get('role', default='user')

    # checking for existing user
    user = User.query\
        .filter_by(email=email)\
        .first()
    if not user:
        # database ORM object
        user = User(
            public_id=str(uuid.uuid4()),
            name=name,
            email=email,
            role=role,
            password=generate_password_hash(password)
        )
        # insert user
        db.session.add(user)
        db.session.commit()

        return jsonify({"status": "Created"})
    else:
        # returns 202 if user already exists
        return jsonify({"status": "Already exist. Please login"})


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
