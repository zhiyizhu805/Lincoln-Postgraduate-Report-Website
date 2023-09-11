from flask import (Flask, redirect, render_template, session, url_for)
from flask_mail import Mail, Message

from admin.admin import admin
from account.account import account
from student.student import student
from supervisor.supervisor import supervisor
from pgChair.pgChair import pgChair
from convenor.convenor import convenor

app = Flask(__name__)
# Secret key for session
app.secret_key = "admin123" 
# Secret key for WTForm                       
app.config['SECRET_KEY'] = 'WTForm secret key' 
# Flask Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587  
app.config['MAIL_USE_TLS'] = True 
app.config['MAIL_USERNAME'] = 'lupgms.lincoln@gmail.com'
app.config['MAIL_PASSWORD'] = 'Lincoln@123'
mail = Mail(app)



# Registering blueprints
app.register_blueprint(admin)
app.register_blueprint(account)
app.register_blueprint(student)
app.register_blueprint(supervisor)
app.register_blueprint(pgChair)
app.register_blueprint(convenor)

if __name__ == '__main__':
    app.run(debug=True)
