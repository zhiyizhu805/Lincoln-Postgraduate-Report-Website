# login and register
from flask import (Blueprint,Flask, flash, redirect, render_template,
                   request, session, url_for)



account = Blueprint("account",__name__,template_folder="templates",static_folder="static",static_url_path='/account/static', url_prefix='')

from account.model import User,Student,Scholarship,Employment,Department
from admin.model import EmailSender
from student.model import SixMR

EmailSender = EmailSender()
User = User()
Student = Student()
Scholarship = Scholarship()
Employment=Employment()
Department = Department()
SixMR = SixMR()


@account.route('/')
def main():
    show_modal = False
    # Check if user is loggedin
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            return redirect(url_for('admin.dashboard'))
        elif session['role'] == "Student":
            return redirect(url_for('student.dashboard'))
        elif session['role'] == "PG Chair":
            return redirect(url_for('pgChair.dashboard'))
        elif session['role'] == "Convenor":
            return redirect(url_for('convenor.dashboard'))
        elif session['role'] == "Supervisor":
            # Check if the supervisor is a convenor.
            if User.check_if_convenor(session['username']):
                session['role'] = "Convenor"
                return redirect(url_for('convenor.dashboard'))
            else:
                return redirect(url_for('supervisor.dashboard'))           
        return render_template('home.html', username=session['username'],role=session['role'])
    # open register with flashing messages
    elif 'show_register_modal' in session:
        show_register_modal = True
        # clear session so the modal won't always open
        session.pop('show_register_modal', None)
        return render_template("home.html", show_register_modal=show_register_modal)
     # open show_reset_password_modal with flashing messages
    elif 'show_reset_password_modal' in session:
        show_reset_password_modal = True
        # clear session so the modal won't always open
        session.pop('show_reset_password_modal', None)
        return render_template("home.html", show_reset_password_modal=show_reset_password_modal)
    # open modal with flashing messages
    elif 'show_login_modal' in session:
        show_login_modal = True
        # clear session so the modal won't always open
        session.pop('show_login_modal', None)
        return render_template("home.html", show_login_modal=show_login_modal)
    elif 'show_complete_profile_modal' in session:
        show_complete_profile_modal = True
        # clear session so it won't always open
        session.pop('show_complete_profile_modal', None)
        #get department name list and staff name list for drop down list
        departments_name=Department.get_dept_name()
        all_staff_name=Department.get_all_staff_name()
        all_scholarship_name=Scholarship.get_all_scholarship_name()
        return render_template("home.html", show_complete_profile_modal=show_complete_profile_modal,departments_name=departments_name,all_staff_name=all_staff_name,all_scholarship_name=all_scholarship_name)
    return render_template("home.html")


@account.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST' and 'email_login' in request.form and 'password_login' in request.form:
        email = request.form['email_login']
        user_password = request.form['password_login']
        account = User.find_user_by_email(email)
        if account is not None:
            password = account['PW']
            # bcrypt.checkpw(user_password.encode('utf-8'), password.encode('utf-8')):
            # use function to check password
            if User.check_password(user_password, password):
                if account['Status'] == "Approval required":
                    flash(
                        'Your account is not approved yet, please wait for approval.', 'error')
                    session['show_login_modal'] = True
                elif account['Status'] == "Suspended":
                    flash(
                        'Your account is suspended, please contact the administrator.', 'error')
                    session['show_login_modal'] = True
                elif account['Status'] == "Change password":
                    session['username'] = account['Email']
                    flash('Please change your password to continue.', 'warning')
                    session['show_reset_password_modal'] = True
                elif account['Status'] == "Complete profile":
                    session['username'] = account['Email']
                    flash('Please complete your profile to continue.', 'warning')
                    session['show_complete_profile_modal'] = True
                else:
                    session['loggedin'] = True
                    session['username'] = account['Email']
                    user = User.get_user_info(account['Email'])
                    session['first_name'] = user['FirstName']
                    session['role'] = account['Role']
                return redirect(url_for('account.main'))
            else:
                # Set error message to display in login modal
                flash('Invalid password. Please try again.', 'error')
                session['show_login_modal'] = True

        else:
            # Set error message to display in login modal
            flash('Incorrect username', 'error')
            session['show_login_modal'] = True

    return redirect(url_for('account.main'))


@account.route('/reset_password', methods=['POST'])
def reset_password():
    if request.method == 'POST' and 'new_password' in request.form and 'new_confirmPassword' in request.form:
        new_password = request.form['new_password']
        confirm_new_password = request.form['new_confirmPassword']
        # get original data
        account = User.find_user_by_email(session['username'])
        if new_password != confirm_new_password:
            flash('Passwords entered do not match. Please try again.', 'error')
            session['show_reset_password_modal'] = True
        else:
            # if original psw equal to new psw
            if User.check_password(confirm_new_password, account['PW']):
                flash('New password cannot be the same as the old password.', 'error')
                session['show_reset_password_modal'] = True
            else:
                # update db with new user psw
                User.change_password(session['username'], confirm_new_password)
                # update user status to 'Complete profile',user then required to complete profile data to log in succrssfully.
                User.change_user_status('Complete profile',session['username'])
                flash('Password reset successful! Please complete your profile to continue!','warning')
                session['show_complete_profile_modal'] = True
                # session['show_login_modal'] = True
    return redirect(url_for('account.main'))


@account.route('/logout')
def logout():
    session.clear()
    return redirect("/")

@account.route('/complete_profile', methods=['POST'])
def complete_profile():
    # use session user email to get corresponding student ID
    studentid = Student.find_studentid_by_email(session['username'])
    enroldate = request.form['enroldate']
    mode_of_study = request.form['mode_of_study']
    thesis = request.form['thesis']
    dept = request.form['dept']
    principle_supervisor =request.form['principle_supervisor']
    associate_supervisor1 =request.form['associate_supervisor1']
    associate_supervisor2 =request.form['associate_supervisor2']
    #get department name list and staff name list for drop down list
    departments_name=Department.get_dept_name()
    all_staff_name=Department.get_all_staff_name()
    all_scholarship_name=Scholarship.get_all_scholarship_name()
    # optional scholarship section will go to scholarship table
    # while user filled in scholarship form(multiple and optional):
    scholarships = []
    i = 1
    while f"scholarshipID[{i}]" in request.form:
        scholarshipID = request.form[f"scholarshipID[{i}]"]
        scholarship_start_date = request.form[f"scholarship_start_date[{i}]"]
        scholarship_end_date = request.form[f"scholarship_end_date[{i}]"]
        scholarship = {
            'studentid': studentid,
            "scholarshipID": int(scholarshipID),
            "start_date": scholarship_start_date,
            "end_date": scholarship_end_date,
        }
        scholarships.append(scholarship)
        i += 1
    # optional additional employment section will go to employment table 
    # while user filled in addtional employment form(can be multiple):
    additional_employments = []
    # mandatory part name 1,additonal part name starting from 2
    i = 1
    while f"supervisorname[{i}]" in request.form:
        # this supervisorname is actually supervisor ID ,only display corrssponding names to users in dropdown list
        supervisorname = request.form[f"supervisorname[{i}]"]
        employmenttype = request.form[f"employmenttype[{i}]"]
        weeklyhours = request.form[f"weeklyhours[{i}]"]
        StartDate = request.form[f'StartDate[{i}]']
        EndDate = request.form[f'EndDate[{i}]']
        employment = {
            "studentid": studentid,
            'supervisorname': int(supervisorname),
            "employmenttype": employmenttype,
            "weeklyhours": weeklyhours,
            "StartDate" : StartDate,
            "EndDate" : EndDate
        }
        additional_employments.append(employment)
        i += 1
    # try:
    if f"supervisorname[1]" in request.form: 
        Employment.add_additional_employment_details(additional_employments)
    if f"scholarshipID[1]" in request.form:
        Scholarship.add_scholarship_details(scholarships)
    Student.supervision(studentid,principle_supervisor,associate_supervisor1,associate_supervisor2)
    Student.complete_myprofile_info(enroldate,mode_of_study,thesis,dept,studentid)
    User.change_user_status('Active',session['username'])
    session['show_login_modal'] = True
    flash("You've completed your profile successfully. Please log in.", 'success') 
    return redirect(url_for('account.main'))
    # except Exception as e:
    #     # show error flash msg if anything wrong in the process of inserting data into db.
    #     show_complete_profile_modal = True
    #     flash('Failed to add your profile .Please try again or contact administrators', 'error') 
    #     return render_template("home.html",scholarships=scholarships,employments=additional_employments,all_scholarship_name=all_scholarship_name,
    #                             mode_of_study=mode_of_study, thesis=thesis,dept=dept,show_complete_profile_modal=show_complete_profile_modal,enroldate=enroldate,
    #                             departments_name=departments_name,all_staff_name=all_staff_name)

@account.route('/register', methods=['POST'])
def register():
    # basic student details basic student details fecth which will go to student table   
    studentid = request.form['studentid']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    address = request.form['address']
    phone = request.form['phone']
    email = request.form['email']
    # psw and confirm psw fetch which will go to user table
    password = request.form['password']
    confirm_password = request.form['confirm_password']
    # validation in db - check if its a exist account from mysql
    account = User.find_user_by_email(email)
    student = Student.find_student_by_studentid(studentid)
    # validation in backend,show flash messages for different errors.
    if account is not None:
        flash('This email account already exists in our system. Please provide an alternative email address.', 'error_regi')
    elif student is not None:
        flash('This studentID has already registered in the system, please log in.', 'error_regi')
    else:
        if password != confirm_password:
            flash('The passwords entered do not match.', 'error_regi')  
        else:
            password_hashed = User.hashPsw(password)
            try:
                # add new user info to db
                User.creat_new_user(email, password_hashed)
                Student.register_student(studentid,firstname, lastname, address, phone, email)
                show_register_modal = True
                # send email to admin for approval
                admin_email = SixMR.get_pgadmin_email()
                message = f"Dear PG Administrator,\n\n{firstname}(student id: {studentid}) has applied to register with the LUPGMS.\n\nRegards,\n\nLUPGMS"
                EmailSender.sendEmail(admin_email, message)
                # Update communication history.
                SixMR.update_communication_history(admin_email, message)
                flash('The registration application has been submitted. We will send you an email notification when your application is approved.', 'success_regi') 
            except Exception as e:
                # show error flash msg if anything wrong in the process of inserting data into db.
                flash('Failed to create new user .Please contact administrators', 'error_regi') 
    show_register_modal = True
    return render_template("home.html",studentid=studentid,firstname=firstname, lastname=lastname, address=address, phone=phone, email=email,password=password,
                            confirm_password=confirm_password,show_register_modal = show_register_modal)
        
 
#visitor send inquiry email   
@account.route('/visitor_email_sender', methods=['POST'])
def visitor_email_sender():
    Name = request.form['Name']
    Email =request.form['Email']
    Subject =request.form['Subject']
    Comment =request.form['Comment']
    ## store inquiry data into database 
    ## TO DO #####
    flash('The inquiry has been sent successfully!We will get back to you as soon as possible!','success_inquriy')
    return redirect("/#contact")
