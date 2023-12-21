from questions_data import api_response
import random
import smtplib
from flask import Flask, render_template, redirect, url_for, request, session
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.session import Session
from flask_wtf import FlaskForm
from jinja2.nodes import Test
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length
import requests
from functools import wraps


EMAIL = "njsreactdom@gmail.com"
PASSWORD = "vaweeqqzwmjakwoj"

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7zgsud7'
Bootstrap5(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///full_user.db'
app.config['SQLALCHEMY_BINDS'] = {
    'company': 'sqlite:///company.db',
    'tests': 'sqlite:///tests.db',
    'written': 'sqlite:///written.db'
}
db = SQLAlchemy()
db.init_app(app)

def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if 'user_id' in session:
            return view_func(*args, **kwargs)
        else:
            return render_template("home.html") # Unauthorized
    return wrapper


class User(db.Model):
    id = db.Column(db.String(20), primary_key=True, unique=True)
    username = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    dob = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(120), nullable=False)
    # image = db.Column(db.BLOB, nullable=False)


    def validate_studentpassword(self, password):
        if self.password == password:
            return True
        return False

class Company(db.Model):
    __bind_key__ = 'company'
    c_name = db.Column(db.String(80), nullable=False, primary_key=True)
    c_email = db.Column(db.String(120,), nullable=False, unique=True)
    password = db.Column(db.String(50), nullable=False)
    sector = db.Column(db.String(80), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(120), nullable=False)

    def validate_password(self, password):
        if self.password == password:
            return True
        return False

class Tests(db.Model):
    __bind_key__ = 'tests'
    test_id = db.Column(db.String(20), primary_key=True, unique=True)
    company_name = db.Column(db.String(80), nullable=False, unique=True)
    c_sector = db.Column(db.String(80), nullable=False)
    c_email = db.Column(db.String(120,), nullable=False, unique=True)
    c_url = db.Column(db.String(120), nullable=False)
    job_role = db.Column(db.String(80), nullable=False)
    skills = db.Column(db.String(120), nullable=False)
    lpa = db.Column(db.String(120), nullable=False)

class Written(db.Model):
    __bind_key__ = 'written'
    sl_no = db.Column(db.Integer, nullable=False, primary_key=True)
    c_name = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.String(20), nullable = False)
    score = db.Column(db.Integer, nullable=False)


with app.app_context():
    db.create_all()


class Exam_Form(FlaskForm):
    id = StringField('Enter your User ID: (YUNXXXX)', validators=[DataRequired()])
    get_otp = SubmitField('Get OTP')



class Otp_Form(FlaskForm):
    otp = StringField('Enter OTP', validators=[DataRequired()])
    submit = SubmitField('Submit')


@app.route('/')
def home():
    return render_template('home.html')

@login_required
@app.route('/student/<username>')
def student_home(username):
    if 'user_id' in session:
        return render_template('student_dashboard.html', username=username)
    else:
        return render_template("home.html")

@app.route('/sign-in', methods=['GET', 'POST'])
def sign_in():
    return render_template('signin.html')

@app.route('/student/sign-in', methods=['POST','GET'])
def student_sign_in():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.validate_studentpassword(password):
            session['user_id'] = email
            return redirect(url_for('student_home', username=user.username))
        else:
            return redirect(url_for('sign_up'))
    return render_template('sign_in_student.html')

@login_required
@app.route('/company/<cname>')
def company_home(cname):
    if 'c_id' in session:
        return render_template('company_dashboard.html', cname=cname)


@app.route('/company/sign-in/', methods=['GET', 'POST'])
def sign_in_company():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        company = Company.query.filter_by(c_email=email).first()
        print(company)
        if company and company.validate_password(password):
            session['c_id'] = email
            return redirect(url_for('company_home', cname=company.c_name))
        else:
            return redirect(url_for('sign_up'))
    return render_template('sign_in_company.html')


@app.route('/sign-up/', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            email = request.form['email']
            address = request.form['address']
            dob = request.form['dob']
            mobile = request.form['mobile']
            role = request.form['role']

            if role == "company":
                check = Company.query.filter_by(c_email=email).first()
                if check:
                    return redirect(url_for('sign_up'))
                new_company = Company(
                    c_name=username,c_email=email,password=password,
                    address=address,mobile=mobile,sector=request.form['companySector']
                )
                db.session.add(new_company)
                db.session.commit()
                return redirect(url_for('sign_in_company'))

            elif role == "applicant":
                check_email = User.query.filter_by(email=email).first()
                if check_email:
                    return redirect(url_for('sign_up'))
                # Generate ID
                id = generate_unique_id()
                new_user = User(id=id, username=username, email=email,
                                password=password,address=address, mobile=mobile, dob=dob
                                )
                db.session.add(new_user)
                message = (f"Subject: Welcome to Yunigma!\n\n Hello {username} \n Your ID is {id}\n"
                           f"Please keep this unique id confidential & and do not share it with anyone.\n"
                           f"If you have any concerns about the security of your account or suspect any unauthorized activity,"
                           f"please contact our support team immediately.\n"
                           f"Feel free to reach out to our support team at [support@email.com]"
                           f"Best regards,\n\n Team Yunigma.")
                send_mail(to=email,subject=message)
                db.session.commit()
                return redirect(url_for('student_sign_in', ))

    return render_template('signup.html')



@app.route('/exam-page/<c_name>', methods=['GET', 'POST'])
def exam_page(c_name):
    exam_form = Exam_Form()
    if exam_form.validate_on_submit():
        user_id = exam_form.id.data
        has_written = Written.query.filter_by(user_id=user_id, c_name = c_name).first()
        user = db.get_or_404(User, user_id)
        user_email = user.email
        user = User.query.filter_by(email=user_email).first()
        if has_written:
            return redirect(url_for('exam_page', c_name=c_name))
        session['c_name'] = c_name
        generated_otp = random.randint(100000, 9999999)
        message = (f'Subject:Yunigma Mailing Services\n\n OTP Generated\n\n'
                   f'Your otp is: {generated_otp}\n Valid only for 1min.')
        send_mail(user_email, message)
        return redirect(url_for('generated_otp',generated_otp=generated_otp))
    return render_template("index.html", exam_form=exam_form)


@app.route('/logout')
def logout():
    print(session)  # Print session before clearing
    session.pop('user_id', None)
    session.pop('username', None)
    print(session)  # Print session after clearing
    return redirect(url_for('home'))

@app.route('/about/')
def about_page():
    return render_template('about.html')

@login_required
@app.route('/quiz/', methods=['GET', 'POST'])
def index():
    user_id = session.get('user_id')
    user = User.query.filter_by(email=user_id).first()
    username = user.username
    if request.method == 'POST':
        # Process the form submission and calculate the score
        user_answers = {key: request.form[key] for key in request.form}
        score = calculate_score(user_answers)
        with open("../count.txt", "r") as file:
            count = int(file.read())
            sl_no = count + 1
        with open("../count.txt", "w") as file:
            file.write(str(sl_no))
        c_name = session['c_name']
        new_writer = Written(user_id=user_id, sl_no=sl_no, c_name=c_name, score=score)
        db.session.add(new_writer)
        db.session.commit()
        if score > 10:
            message = ("Subject:Congratulations!\n\n You have successfully passed the assessment\n"
                       "Use this link: at DD/MM/YYYY HH: to continue in your interview process.")
            send_mail(to=session['user_id'], subject=message)
            yun_id = user.id
            written_user_row = Written.query.filter_by(user_id=session['user_id']).first()
            company_name = written_user_row.c_name
            company_row = Tests.query.filter_by(company_name=company_name).first()
            c_email = company_row.c_email
            message = (f"Subject:New Applicant\n\n A new user passed the assessment.\n"
                       f"User Id: {yun_id}\n\n Score: {score}")
            send_mail(to=c_email, subject=message)
        return render_template('result.html', score=score, total_questions = len(api_response), username = username)
    elif request.method == 'GET':
        return render_template('quiz.html', questions=api_response, username=username)

def calculate_score(user_answers):
    correct_answers, i = 0, 0
    for c_ans in user_answers.values():
        if c_ans == api_response[i]['correct_answer']:
            correct_answers += 1
        i += 1
    return correct_answers

@app.route('/otp/<int:generated_otp>', methods = ['GET', 'POST'])
def generated_otp(generated_otp):
    if request.method == 'GET':
        return render_template('otp.html', form = Otp_Form())
    elif request.method == 'POST':
        otp = request.form['otp']
        if int(otp) == int(generated_otp):
            return redirect(url_for('index'))
        else:
            return f"<h1>Invalid OTP!</h1>"

@app.route('/user/<username>/jobs')
@login_required
def jobs(username):
    return render_template("jobs.html", username = username)

@app.route('/company/hire', methods = ['GET', 'POST'])
def hire():
    if request.method == 'POST':
        print(request.form)
        c_name = request.form['companyName']
        c_sector = request.form['companySector']
        c_url = request.form['c_url']
        c_email = request.form['c_email']
        job_role = request.form['jobRole']
        skills = request.form['skills']
        lpa = request.form['annualPackage'].strip()
        test_id = generate_test_id()

        new_test = Tests(company_name = c_name, job_role = job_role,
                         skills = skills, lpa = lpa, test_id = test_id, c_sector = c_sector,
                         c_url = c_url, c_email = c_email
        )
        db.session.add(new_test)
        db.session.commit()
        c_id = session.get('c_id')
        company = Company.query.filter_by(c_email = c_id).first()
        cname = company.c_name
        return redirect(url_for('company_home', cname=cname))
    return render_template("hire_new.html")

@app.route('/student/skills', methods = ['GET', 'POST'])
def skills():
    if request.method == 'POST':
        skills = request.form['skills']

    return render_template("enter_skills.html")


def generate_unique_id():
    unique_id = ""
    with open('unique_id.txt', 'r') as unique_id_file:
        prev_id = int(unique_id_file.read())
        prev_id += 1
        unique_id = "YUN" + str(prev_id)
    with open('unique_id.txt', 'w') as unique_id_file:
        unique_id_file.write(str(prev_id))

    return unique_id

def generate_test_id():
        test_id = "TEST"
        with open("test_id.txt", "r") as id_file:
            prev_no = int(id_file.read())
            cur_no = prev_no + 1
            test_id += str(cur_no)

        # Updating the file.
        with open("test_id.txt", "w") as id_file:
            id_file.write(str(cur_no))

        return test_id


def send_mail(to, subject):
    with smtplib.SMTP('smtp.gmail.com', port=587) as server:
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(
            from_addr=EMAIL,
            to_addrs=to,
            msg=subject
        )



if __name__ == '__main__':
    app.run(debug=True)