from flask import Flask, jsonify, request, render_template
from auth import authenticate

app = Flask(__name__)


#TODO FE: Signup/Login Forms
#TODO BE: Signup/Login handling, DB interaction (local/dev DB like SQLite + Cloud DB)
#TODO Infra: K8s cluster + Cloud DB
@app.route('/', methods=['GET','POST'])
def hello_world():
    #Testing HTML forms
    if request.method == "POST":
        first_name = request.form.get("fname")
        last_name = request.form.get("lname")
        return f"Your name is {first_name} {last_name}"
    return render_template("form.html")

@app.route('/signup', methods=['GET'])
def get_signup():
    # Get signup page
    pass

@app.route('/signup', methods=['POST'])
def post_signup():
    # Process signup, add new user if necessary
    # HTML form
    # Inputs: username/email, password, confirmed password
    # hash password, as soon as possible
    # Make new user entry in DB, hashed password
    # Return a 'confirmed signup' if all goes well
    # Rollback transaction in DB if some failure, to not have double entries
    # Redirect to login if all is good using HATEOAS
    pass

@app.route('/login', methods=['GET'])
def get_login():
    # Get login page
    pass

@app.route('/login', methods=['POST'])
def post_login():
    # Process login, validate account and manage authorization
    # If error return message to try again, maybe password wrong
    # Inputs: username/email, password
    # Validate hashed password against DB
    # If all good, redirect to main/home page using HATEOAS
    # Jump off to functions in auth.py
    username = "test"
    pw = "test"
    authenticate(username, pw)
    pass

# Forget password
# Enter email
# check if exists
# if not do nothing
# else allow entry of new password
# PUT new password to user id i.e. email/username
# route "/user/<user-id>

if __name__ == '__main__':
    app.run(debug=True)