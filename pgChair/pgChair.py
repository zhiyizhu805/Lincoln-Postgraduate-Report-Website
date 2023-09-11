from flask import Blueprint,request, render_template, redirect, url_for,  session, flash
from pgChair import model
from pgChair.model import User
from student.webforms import MyReportsReportingPeriod
from student.model import SixMR
from flask_mail import Mail, Message
from admin.model import EmailSender
from pgChair.model import StatusBar

EmailSender = EmailSender()
SixMR = SixMR()
User = User()
StatusBar = StatusBar()
pgChair = Blueprint('pgChair',__name__ ,template_folder='templates',static_folder='static',  url_prefix='/pgChair')

@pgChair.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('pgChair_dashboard.html')
    else:
        return render_template('accessDenied.html')

#function returns a list of students within the Faculty
@pgChair.route('/pgChair/studentlist')
def pgchair_students():
    if 'loggedin' in session:
        student_result = model.get_all_student()
        # Show the profile page with account info
        return render_template('pgChair_studentlist.html', student_result=student_result)
    # User is not loggedin redirect to login page

    else:
        return render_template('accessDenied.html')

@pgChair.route('/pgChair/supervisorlist')
def pgchair_supervisor():
    if 'loggedin' in session:
        supervisor_result = model.get_all_supervisor()        
        # returns a template that lists all supervisors in the Faculty
        return render_template('pgChair_supervisorlist.html', supervisor_result=supervisor_result)
    # User is not loggedin redirect to login page
    else:
        return render_template('accessDenied.html')
    
# function returns a student's profile details
@pgChair.route('/profile_student', methods=['GET'])
def profile_student():
    # Check if user is loggedin
    if 'loggedin' in session:
        StudentEmail = request.args.get("StudentEmail")
        student_info = User.profile_student(StudentEmail)
        student_emp = User.student_emp(StudentEmail)
        student_sup = User.student_sup(StudentEmail)
        student_scholar = User.student_scholar(StudentEmail)
        return render_template('profile_student.html', student_info=student_info, student_emp=student_emp, student_sup=student_sup, student_scholar=student_scholar, username=session['username'], role=session['role'])
# User is not loggedin redirect to login page
    return redirect(url_for('account.login'))


# function returns a student's all employment history
@pgChair.route('/button_clicked/<argument>', methods=['GET'])
def button_clicked(argument):
    student_emp = argument
    student_emp_history = model.student_emp_history(student_emp)
    return render_template('pgChair_profile_history_studentemp.html',
                           student_emp_history=student_emp_history)


# function returns a student's all scholarship history
@pgChair.route('/button_clicked_sch/<argument>', methods=['GET'])
def button_clicked_sch(argument):
    student_sche = argument
    student_scho_history = model.student_scho_history(student_sche)
    return render_template('pgChair_profile_history_studentscholar.html',
                           student_scho_history=student_scho_history)



# function returns supervisor's profile details
@pgChair.route('/profile_supervisor', methods=['GET'])
def profile_supervisor():
    # Check if user is loggedin
    if 'loggedin' in session:
        SupervisorEmail = request.args.get("SupervisorEmail")
        supervisor_info = User.profile_supervisor(SupervisorEmail)        
        return render_template('profile_supervisor.html', supervisor_info=supervisor_info, username=session['username'], role=session['role'])
# User is not loggedin redirect to login page
    return redirect(url_for('account.login'))


# function return pgChair profile
@pgChair.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # call user_model to get sql data
        pgChair = User.profile_pgChair(session['username'])
        # Show the profile page with account info
        return render_template('pgChair_profile.html', pgChair=pgChair)
    return render_template('accessDenied.html')

# function making pgChair profile page editable
@pgChair.route('/profile/edit')
def profile_edit():
    if 'loggedin' in session:
        # call user_model to get sql data
        pgChair = User.profile_pgChair(session['username'])
        # Show the profile page with account info
        return render_template('pgChair_profile_edit.html', pgChair=pgChair)
    else:
        return render_template('accessDenied.html')
    
# function sending user input back to update db 
@pgChair.route('/profile/edit/process', methods=['POST'])
def profile_edit_process():
    if 'loggedin' in session:
        phone=request.form['phone']
        # call user_model to get sql data
        pgChair = User.profile_pgChair_edit_process(phone, session['username'])
        # Show the updated profile page with success flash message
        flash('Profile has been updated successfully!', 'success')
        return redirect(url_for('pgChair.profile'))   
    else:
        return render_template('accessDenied.html')

@pgChair.route('/select_reporting_period', methods=['GET', 'POST'])
def select_reporting_period():
    # Check if user is loggedin
    if 'loggedin' in session:
        form = MyReportsReportingPeriod()
        if form.validate_on_submit():
            year = form.year.data
            period = form.period.data
            period_ending = year + period
            return redirect(url_for('pgChair.my_reports', period_ending=period_ending))
        return render_template('pgChair_select_reporting_period.html', form=form)
    return redirect(url_for('account.login'))

@pgChair.route('/my_reports/<period_ending>', methods=['GET'])
def my_reports(period_ending):
    # Check if user is loggedin
    if 'loggedin' in session:
        # Get all the reports from the pg chair's faculty in the chosen period in a list.
        reports= User.get_pgchair_report_list(period_ending)
        return render_template('pgChair_my_reports.html', reports=reports)
    return redirect(url_for('account.login'))

@pgChair.route('/my_reports/respond_section_f/<int:report_id>', methods=['GET', 'POST'])
def respond_section_f(report_id):
    # Check if user is loggedin
    if 'loggedin' in session:
        if request.method == 'POST':
            form_data = request.form.to_dict()
            button = request.args.get('button')
            if button == 'saveButton':
                User.update_pgchair_response(report_id, form_data['pgChair_response'], 'save')
                flash("Feedback saved successfully!", 'success')
                return redirect(url_for('pgChair.respond_section_f',report_id=report_id))
            if button == 'submitButton':
                # Save the F response content and relevant F table columns and get student's email.
                student_id = User.get_student(report_id)['StudentID']
                email= User.update_pgchair_response(report_id, form_data['pgChair_response'], 'submit')
                # Send email to student.
                message = f"Dear Student,\n\nThe PG Chair has just responded to your concerns raised in Section F of your report(ID:{report_id}).Please check the report.\n\nRegards,\n\nLUPGMS"
                EmailSender.sendEmail(email, message)
                # update communication history
                SixMR.update_communication_history(email, message)
                flash("Feedback submitted successfully!", 'success')
                return redirect(url_for('supervisor.view_report',student_id=student_id, report_id=report_id))
        else:
            # Get the F response content.
            pgChair_response= User.get_pgchair_response(report_id)
            student_info = User.get_student(report_id)
            return render_template('pgChair_respond_section_f.html', pgChair_response=pgChair_response, report_id=report_id, student_info=student_info)
    return redirect(url_for('account.login'))

#  report status description for each report
@pgChair.route('/report_status_desc/<int:report_id>', methods=['POST','GET'])
def report_status_desc(report_id):
    # Check if user is loggedin
    if 'loggedin' in session:
        if request.method == 'POST':
            submission_history_desc_list = StatusBar.submission_history_desc_list(report_id)
            all_procedures=[1,2,3,4]
            submission_history_length =StatusBar.submission_history_index(report_id)
            current_status=StatusBar.report_status(report_id)['Status']
            return render_template("report_status_desc.html",submission_history=submission_history_desc_list,all_procedures=all_procedures,submission_history_length=submission_history_length,
                                   report_id=report_id,current_status=current_status)
        else:
            return render_template("accessDenied.html")
    else:
        return redirect(url_for('account.login'))