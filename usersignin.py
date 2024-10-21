import os

import certifi

import ssl

import secrets

import json

import random

import requests

import random

import datetime
from datetime import timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_mail import Mail, Message
from flask_cors import CORS


from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired 

from wtforms import Form, StringField, PasswordField, validators, ValidationError
from wtforms.fields import EmailField
from user import NormalUser, BusinessUser


#use _id to denote special keys
#emails are used as the ids


def sudo_delete(email):
    try:
        user_database.delete_one({"_id": email})
    except:
        pass

def email_validator(form, field):
    user = user_database.find_one(field.data)
    if user:
        raise ValidationError("Email is already in use!")    

class SignInForm(Form):
    email_address = EmailField("Email")
    password = PasswordField("Password")


class RegisterForm(Form):
    email_address = EmailField("Email", [email_validator])
    password = PasswordField("Password")
    name = StringField("Name")
    confirmed = PasswordField("Confirm Your Password")
    #we can add more once we find out more of what we want
    

def generate_salt():
    os.urandom(1024)

#We want this in the main.py, iirc
#--------stuff that should be in main.py---------------
def __load_mongo_config() -> str:
    with open("mongoconfig.noread", mode = "r") as f:
        string = f.readline()
    return string

def __load_migraide_config() -> list[str]:
    container = list()
    with open("migraideconfig.noread", "r") as f:
        for line in f.readlines():
             container.append(line)
    return container       

def __generate_random_value() -> int:
    random.randint(100_000, 0xFFF_FFF)    

def __generate_meet_link(title: str, text: str, email_consul: str, email_client: str) -> str:
    # date_start_year = start.year
    # date_start_month = start.month
    # date_start_day = start.day
    # date_start_hour = start.hour
    # if date_start_month < 10:
    #     date_start_month = f"0{date_start_month}"
    # if date_start_hour < 10:
    #     date_start_hour = f"0{date_start_hour}"
    # date_start_min = start.minute
    # #we're going through all the stress redeclaring so we don't break the overflow possibilities
    # end = start + timedelta(seconds = 3600)
    # end_start_year = end.year
    # end_start_month = end.month
    # end_start_day = end.day
    # end_start_hour = end.hour
    # if end_start_month < 10:
    #     end_start_month = f"0{end_start_month}"
    # if end_start_hour < 10:
    #     end_start_hour = f"0{end_start_hour}"
    # end_start_min = end.minute
    # date_start_str = f"{date_start_year}{date_start_month}{date_start_day}T{date_start_hour}{date_start_min}00Z"
    # date_end_str = f"{end_start_year}{end_start_month}{end_start_day}{end_start_hour}{end_start_min}00Z"
    return f"""https://calendar.google.com/calendar/render?action=TEMPLATE&text={title.replace(" ", "+")}&details={text.replace(" ", "+")}&add={email_consul},{email_client}&location=https://meet.google.com"""
secret = secrets.token_hex(256)
mongo_config_value = __load_mongo_config()
certificate = certifi.where()
salt = generate_salt()
mailconfig = __load_migraide_config()

application = Flask(__name__)
application.config["MONGO_URI"] = mongo_config_value
application.config["MAIL_PORT"] = int(mailconfig[-1])
application.config["MAIL_SERVER"] = mailconfig[1][:-1]
application.config["MAIL_USE_TLS"] = False
application.config["MAIL_USE_SSL"] = True
application.config["MAIL_USERNAME"] = mailconfig[0][:-1]
application.config["MAIL_PASSWORD"] = mailconfig[2][:-1]
application.config["MAIL_DEFAULT_SENDER"] = mailconfig[0][:-1]
application.config["SECRET_KEY"] = secret #TODO: remove in prod
application.config.update(
    SESSION_COOKIE_SECURE = True,
    # SESSION_HTTPONLY = True,
    SESSION_COOKIE_SAMESITE = "Lax",
    PERMANENT_SESSION_LIFETIME = timedelta(days = 5)
)
application.config['MAIL_TIMEOUT'] = 30  # Set a 30-second timeout for Flask-Mail operations
application.config['MAIL_MAX_EMAILS'] = None  # Remove limit on emails sent in a single connection
application.config['MAIL_SUPPRESS_SEND'] = False 

CORS(application)

db = PyMongo(application, tls = True, tlsCAFile=certificate)
user_database = db.cx.user_database["business_database"]
client_database = db.cx.user_database["client_database"]
temp_db = db.cx.user_database["temp_database"]
nkrypt = Bcrypt(application)
mail = Mail(application)
secret_serializer = URLSafeTimedSerializer(application.secret_key)
 
def __send_confirmation_email(address, url):
    msg = Message("Confirm your Account", recipients = [address])
    msg.body = f"""
                Hi,
                Use the following link to complete your sign up process: {url}
                If you didn't request this code, please ignore this email.
        """
    try:
        mail.send(msg)
    except Exception as e:
        print(e)

def __send_welcome_mail(address, name):
    msg = Message("Welcome to Migraide AI", recipients = [address])
    msg.body = f"""
            Hi {name},
            Your EB Visa consultant wants you to complete some important forms, but don't worry we will help you through the process
            Our AI Agent is capable of filling out all your EB1 and EB2 visa forms for you with a high degree of precision and speed.
            Let's get you started
            """
    try:
        mail.send(msg)
    except Exception as e:
        print(e)

def __send_nudge_mail(address, client_id):
    msg = Message("Form filling scheduled", recipients = [address])
    msg.body = f"Please click on the following link to fill out your forms: https://migraide.com/client/form-filler/{client_id}"
    try:
        mail.send(msg)
    except:
        print(e) #substitute for logging information later on
        
#see if connecting works
def __connect_db_test():
    try:
        val = json.dumps(db.cx.admin.command("ping"))
    except Exception as e:
        print(f"{e}")
    print("Successfully connected to database")
    print(f"{val}")
    
#--------stuff that should be in main.py---------------
@application.route("/signin", methods = ["POST", "GET"])
def signin():
    if request.method == "POST":
        data = request.get_json()
        email = data["email_address"]
        password = data["password"]
        user = user_database.find_one({"_id": email})
        if user and nkrypt.check_password_hash(user["password"], password):
            session["time"] = datetime.datetime.now().isoformat()
            session["current"] = user["_id"]
            return jsonify({"status": "Success", "message": "Sign-in successful"}), 200
        else:
            return jsonify({"status": "Error", "message": "Invalid sign-in credentials"}), 401

@application.route("/forgot_password", methods = ["POST", "GET"])
def forgot_password():
    #more traditional way of handling input form data, might deprecate the classes when in production
    email = request.form["email"]
    user = user_database.find_one({"_id": email})
    if user:
        token = secret_serializer.dumps(email, salt)
        to_reset = url_for("reset_password", token = token, _external = True)
        message = Message("Password Reset Request", recipients = [email])
        message.body = f"Click the following to reset your password: {to_reset}"
        mail.send(message)
        return jsonify({"status": "success", "message": "email sent"})
    else:
        return jsonify({"status": "error", "message": "this user does not exist"})
        
@application.route("/reset_password/<token>", methods = ["POST", "GET"])
def reset_password(token):
    try: 
        email = secret_serializer.loads(token, salt = salt, max_age = 3600)
    except:
        #frontend should route to the pass-word reset on this failure
        return jsonify({"status": "error", "message": "The password reset link is invalid, or the custom token has expired"})
    new_password = request.form["Password"]
    hashed = nkrypt.generate_password_hash(new_password)
    user_database.update_one({"_id": email}, {"$set": {"password": hashed}})
    return jsonify({"status": "success", "message": "Your password has been updated!, congratulations!"})

def __generate_config_token(email):
    s = URLSafeTimedSerializer(application.secret_key)
    return s.dumps(email, salt = salt)

def __confirm_config_token(token):
    serializer = URLSafeTimedSerializer(application.secret_key)
    try:
        email = serializer.loads(token, salt = salt)
    except BadSignature:
        return None
    except TimeoutError:
        return False
    except Exception:
        return None
    return email

@application.route("/nudge_client", methods = ["POST"])
def nudge_client():
    email = request.form["email"]
    user = session["current"]
    litmus = user_database.find_one({"_id": user, "clients": email})
    if litmus:
        client = client_database.find_one({"_id": email})
        __send_nudge_mail(email, client["rand_id"])
        return jsonify({"status": "success", "message": "The user has been sent a nudge mail"})
    else:
        return jsonify({"status": "error", "message": "Malformed request"})                     

@application.route("/confirm_email/<token>", methods = ["POST", "GET"])
def confirm_email(token):
    email = __confirm_config_token(token)
    #oh this is autoconfirming
    if email:
        user = temp_db.find_one_and_delete({"_id": email})
        __send_welcome_mail(email, user["first_name"])
        user_database.insert_one(user)
        return jsonify({"status": "success", "message": f"Business user: {user['_id']} has on-boarded successfully"})
    else:
        return jsonify({"status": "failure", "message": "The confirmation token has expired or has timed out"})
       

#works for now
@application.route("/register", methods = ["POST", "GET"])
def register():
    
    if request.method == "POST":
        data = request.get_json()
        print(data)
        if data["business_user"] == "true":
            try:
                user = BusinessUser(data)
                #store it in the db for now, otherwise we can delete it if the token doesn't work
                password =data["password"]
                hashed = nkrypt.generate_password_hash(password)
                user.set_password(hashed)
                user = user.serialize()
                user["business_id"] = __generate_random_value()
                temp_db.insert_one(user)
                token = __generate_config_token(user["_id"])
                confirm_url = url_for("confirm_email", token = token, _external = True)
                __send_confirmation_email(user["_id"], confirm_url)
                return jsonify({"status": "success", "message": "email sent sucessfully"})
            except Exception as e:
                return jsonify({"status": "failure", "message": f"Exception raised: {e}"})
            

@application.route("/dashboard", methods = ["POST", "GET"])  
# route is set to an empty string
# example code block to potentially solve "cannot GET /pages/dashboard.html" error on frontend
# @application.route("/dashboard", methods=["GET", "POST"])
# def dashboard():
#     if "current" not in session:
#         return jsonify({"status": "error", "message": "Not authenticated"}), 401

#     email = session["current"]
#     user = user_database.find_one({"_id": email})

#     if not user:
#         return jsonify({"status": "error", "message": "User not found"}), 404

#     return jsonify({
#         "status": "success",
#         "first_name": user.get("first_name", ""),
#         "businessname": user.get("businessname", ""),
#         "message": "Success"
#     })
def dashboard():
    email = session["current"]
    try:
        user = user_database.find_one({"_id": email})
        if user:
            businessname = user["businessname"]
            first_name = user["first_name"]
        return jsonify({
            "status": "success",
            "first_name": f"{first_name}",
            "businessname": f"{businessname}",
            "message": "Success"          
            })
    except Exception as e:
        return jsonify({
                    "status": "error",
                    "message":f"{e}"
                })

@application.route("/add_client", methods = ["POST", "GET"])
def add_client():
    if request.method == "POST":
        email = session["current"]
        user = user_database.find({"_id": email})
        if user:
            #process the form
            client = NormalUser(request.form)
            client.set_rand_id(__generate_random_value())
            updated = BusinessUser(user, True)
            updated.set_password(user["password"])
            updated.add_client(client._id)
            __send_nudge_mail(client._id, client.rand_id)
            user_database.find_one_and_update({"_id": email},{
                                                  "$set":{
                                                      "clients": updated.clients
                                                  }
                                              })
            client_database.insert_one(client.__dict__)
            return jsonify({
                               "status": "success",
                               "message": "client added successfully"
                           })
        else:
            return jsonify({"status": "error", "message": "possible session error"})


@application.route("/show_clients", methods = ["POST", "GET"])
def show_clients():
    if request.method == "POST":
        try:
            business_user = user_database.find_one(
                {'_id': session["current"]},
                {'clients': 1}  # Only retrieve the clients field
            )
            if not business_user:
                return jsonify({'error': 'Business user not found'}), 404
        
            # Get the list of client emails
            client_emails = business_user.get('clients', [])
            if not client_emails:
                return jsonify({'clients': []})
             # Fetch and format client data
            client_data = list(client_database.find(
                {'_id': {'$in': client_emails}},
                {
                    'gender': 1,
                    'first_name': 1,
                    'middle_name': 1,
                    'last_name': 1,
                    'phone_number': 1,
                    "status": 1
                }
            ))        
            # Format the response
            formatted_clients = []
            for client in client_data:
                # Build full name, handling possible missing middle name
                name_parts = [
                    client.get('first_name', ''),
                    client.get('middle_name', ''),
                    client.get('last_name', '')
                ]
                # Remove empty parts and join with space
                full_name = ' '.join(filter(None, name_parts))
                formatted_client = {
                    'email': client['_id'],  # Since email is the _id
                    'full_name': full_name,
                    'gender': client.get('gender', ''),
                    'phone_numbers': client.get('phone_numbers', []),
                    "status": client.get("status", "")
                }
                formatted_clients.append(formatted_client)
            # Sort by full name
            formatted_clients.sort(key=lambda x: x['full_name'])        
            return jsonify({
                'status': 'success',
                'client_count': len(formatted_clients),
                'clients': formatted_clients
            })
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500


@application.route("/business_information", methods = ["GET", "POST"])
def business_information():
    if request.method == "POST":
        curr_email = session["current"]
        curr_user = user_database.find_one({"_id": curr_email})
        if curr_user:
            mem = BusinessUser(curr_user, True)
            mem.update_business_information(request.form)
            user_database.find_one_and_replace({"_id": curr_email}, mem.serialize())
            return jsonify({"status": "success", "message": "the operation was successful"})
        else:
            return jsonify({"status": "error", "message": "session data might be corrupted"})

@application.route("/generate_meet", methods = ["POST", "GET"])
def generate_meet():
    email = session["current"]
    client = request.form["client_email"]
    form_name = request.form["form_name"]
    form_title = request.form["form_link"]
    title = "Going over VISA form"
    text = f"This is an invitation to go over the {form_name}, at {form_link}"
    link = __generate_meet_link(title, text, email, client)
    return jsonify({"status": "success", "message": "link generated successfully", "link":f"{link}"})
    

def __get_ip_location(ip):
    response = requests.get(f"https://ipapi.co/{ip}/json/")
    if response.status_code == 200:
        data = response.json()
        print(data)
        return{
            "city": data.get("city"),
            "region": data.get("region"),
            "country": data.get("country_name")
        }
    return None


@application.route("/get_location", methods = ["POST"])
def get_location():
    ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
    location_data = __get_ip_location(ip)
    if ip and location_data["error"]:
        location_data["status"] = "success"
        location_data["message"] = "got the ip"
        return jsonify(location_data)
    else:
        return jsonify({"status": "failure", "message": "failed to get the ip", "location_data_reserved": location_data["reason"]})

def test_meet_links():
    title = "Testing Meet Links"
    text = "This is just a test, you don't really have to join, lol"
    form_link = "https://migraide.com"
    email_consul = "omokennanna832@gmail.com"
    email_client = "faith.e.ida@gmail.com"
    link = __generate_meet_link(title, text, email_consul, email_client)
    print(link)    

# test_meet_links()

application.run(debug = True)
