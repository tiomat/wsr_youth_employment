# flask imports
from crypt import methods
from email.mime import application
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
import uuid
from sqlalchemy import ForeignKey, false, null, true  # for public id
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import random

# creates Flask object
app = Flask(__name__)

# configuration
# NEVER HARDCODE YOUR CONFIGURATION IN YOUR CODE
# INSTEAD CREATE A .env FILE AND STORE IN IT

# database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///service_application.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# creates SQLALCHEMY object
db = SQLAlchemy(app)


# Database ORMs
# Users and roles
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    role = db.Column(db.String(50))
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(80))


# Users applicattions
class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # не создаем связь, потому что планируем изолированные базы у каждого сервиса
    user_id = db.Column(db.Integer)
    snils = db.Column(db.String(100))               # СНИЛС храним в заявке
    inn = db.Column(db.String(100))                 # ИНН храним в заявке
    approved = db.Column(db.Boolean)                # Статус согласования

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# Diagnostic results
class Diagnostic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    # не создаем связь, потому что планируем изолированные базы у каждого сервиса
    user_id = db.Column(db.Integer)
    result = db.Column(db.String(100))              # результаты диагностики
    done = db.Column(db.Boolean)                    # результаты диагностики


# User Database Route
# this route sends back list of users
@app.route('/users', methods=['GET'])
def get_all_users():
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

        exp = 1658341812
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


# TODO: разобраться как сгенерировать эти данные
@app.route('/jwt', methods=['GET'])
def info():
    data = {
        "keys": [{
            "kty": "RSA",
            "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
            "e": "AQAB",
            "d": "X4cTteJY_gn4FYPsXB8rdXix5vwsg1FLN5E3EaG6RJoVH-HLLKD9M7dx5oo7GURknchnrRweUkC7hT5fJLM0WbFAKNLWY2vv7B6NqXSzUvxT0_YSfqijwp3RTzlBaCxWp4doFk5N2o8Gy_nHNKroADIkJ46pRUohsXywbReAdYaMwFs9tv8d_cPVY3i07a3t8MN6TNwm0dSawm9v47UiCl3Sk5ZiG7xojPLu4sbg1U2jx4IBTNBznbJSzFHK66jT8bgkuqsk0GjskDJk19Z4qwjwbsnn4j2WBii3RL-Us2lGVkY8fkFzme1z0HbIkfz0Y6mqnOYtqc0X4jfcKoAC8Q",
            "p": "83i-7IvMGXoMXCskv73TKr8637FiO7Z27zv8oj6pbWUQyLPQBQxtPVnwD20R-60eTDmD2ujnMt5PoqMrm8RfmNhVWDtjjMmCMjOpSXicFHj7XOuVIYQyqVWlWEh6dN36GVZYk93N8Bc9vY41xy8B9RzzOGVQzXvNEvn7O0nVbfs",
            "q": "3dfOR9cuYq-0S-mkFLzgItgMEfFzB2q3hWehMuG0oCuqnb3vobLyumqjVZQO1dIrdwgTnCdpYzBcOfW5r370AFXjiWft_NGEiovonizhKpo9VVS78TzFgxkIdrecRezsZ-1kYd_s1qDbxtkDEgfAITAG9LUnADun4vIcb6yelxk",
            "dp": "G4sPXkc6Ya9y8oJW9_ILj4xuppu0lzi_H7VTkS8xj5SdX3coE0oimYwxIi2emTAue0UOa5dpgFGyBJ4c8tQ2VF402XRugKDTP8akYhFo5tAA77Qe_NmtuYZc3C3m3I24G2GvR5sSDxUyAN2zq8Lfn9EUms6rY3Ob8YeiKkTiBj0",
            "dq": "s9lAH9fggBsoFR8Oac2R_E2gw282rT2kGOAhvIllETE1efrA6huUUvMfBcMpn8lqeW6vzznYY5SSQF7pMdC_agI3nG8Ibp1BUb0JUiraRNqUfLhcQb_d9GF4Dh7e74WbRsobRonujTYN1xCaP6TO61jvWrX-L18txXw494Q_cgk",
            "qi": "GyM_p6JrXySiz1toFgKbWV-JdI3jQ4ypu9rbMWx3rQJBfmt0FoYzgUIZEVFEcOqwemRN81zoDAaa-Bk0KWNGDjJHZDdDmFhW3AN7lI-puxk_mHZGJ11rxyR8O55XLSe3SPmRfKwZI6yU24ZxvQKFYItdldUKGzO6Ia6zTKhAVRU",
            "alg": "RS256",
            "kid": "2011-04-29"
        }]
    }
    return jsonify(data)


@app.route('/jwtpub', methods=['GET'])
def pubinfo():
    data = {"keys": [{
        "kty": "RSA",
        "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
        "e": "AQAB",
        "alg": "RS256",
        "kid": "2011-04-29"
    }]}
    return jsonify(data)


# СОЗДАНИЕ ЗАЯВКИ ПОЛЬЗОВАТЕЛЕМ
@app.route('/application', methods=["GET", "POST"])
def user_application():

    user_id = request.args.get('user_id', null)
    print("USER ID FROM TOKEN")
    print(user_id)

    if(request.method == "GET"):
        application = Application.query\
            .filter_by(user_id=user_id)\
            .first()
        if not application:
            return jsonify({"status": "not found", "data": {}})
        else:
            return jsonify({"status": "OK", "data": application.as_dict()})

    if(request.method == "POST"):

        data = request.form
        snils = data.get('snils', 'default')
        inn = data.get('inn', 'default')

        application = Application.query\
            .filter_by(user_id=user_id)\
            .first()

        if not application:
            application = Application(
                user_id=user_id,
                snils=snils,
                inn=inn,
                approved=False
            )
            db.session.add(application)
            db.session.commit()
        else:
            # проверяем что не вносим изменения в уже одобренную заявку
            if not application.approved:
                application.snils = snils
                application.inn = inn

                db.session.add(application)
                db.session.commit()

        return jsonify({"status": "ok", "data": application.as_dict()})


# СОГЛАСОВАНИЕ ЗАЯВКИ ФЕРЕДАЛЬНЫМ ОПЕРАТОРОМ
@app.route('/approve/<application_id>', methods=["GET", "POST"])
def fo_application(application_id):

    if (request.method == "GET"):
        application = Application.query\
            .filter_by(id=application_id)\
            .first()

        if not application:
            return jsonify({"status": "not found", "data": {}})
        else:
            return jsonify({"status": "OK", "data": application.as_dict()})

    if (request.method == "POST"):
        action = request.args.get('action', null)
        if not action:
            return jsonify({"status": "error", "data": "specify action in URL params"})

        application = Application.query\
            .filter_by(id=application_id)\
            .first()

        if not application:
            return jsonify({"status": "not found", "data": {}})
        else:

            if(action == 'approve'):
                decide = 1
            else:
                decide = 0

            application.approved = decide

            db.session.add(application)
            db.session.commit()

            return jsonify({"status": "OK", "data": application.as_dict()})


@app.route('/sys/application', methods=["GET"])
def get_application_status():
    user_id = request.args.get('user_id', null)

    application = Application.query\
        .filter_by(user_id=user_id)\
        .first()

    if not application:
        application_status = false
    else:
        application_status = application.approved

    return jsonify({"application": application_status})


@app.route('/diagnostic', methods=["GET"])
def get_diagnostic():
    user_id = request.args.get('user_id', null)
    link = "www.diagnostichost.ru/run?user_id="+user_id
    return jsonify({"status": "OK", "link": link})


@ app.route('/check/<id>', methods=["GET"])
def business_check(id):
    status = ['APPROVED', 'DENIED']
    decide = random.choice(status)
    print("Decision is "+decide)
    return jsonify({"status": decide})


@ app.route('/business/<id>', methods=["GET", "POST"])
def business_action(id):

    status = "OK"
    return jsonify({"method": request.method, "status": status})


if __name__ == "__main__":
    # setting debug to True enables hot reload
    # and also provides a debugger shell
    # if you hit an error while running the server
    app.debug = True
    app.run(host="0.0.0.0", port="4000")


# СТРУКТУРА СЕРВИСОВ

# 1. Работа с пользователями
# 1.1 Авторизация +
# 1.2 Регистрация +

# 2. Подача заявления
# 2.1 Поадача заявления и его отправка на проверку +
# 2.2 Проверка заявления и согласование или возврат на доработку +

# ~ Проверка при запросе диагностики, на то, что заявление согласовано ~

# 3. Прохождение диагностики
# 3.1 Выдать ссылку для прохождения диагностики
# 3.2 Получить результаты диагностики
# 3.3 Выдать результаты диагностики

# 4. Сервис проверки доступа и бизнес-процесс
# 4.1 Сбор необходимых данных на уровне Gateway
# 4.2 Проверка данных и целевого действия на соответствие
# 4.3 Возврат статуса в Gateway и принятие решение о пропуске запроса на целевой сервис или прекращение запроса

# TODO: собрать в Docker
# TODO: разобраться с шифрованием
