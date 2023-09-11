from flask import Blueprint,request, render_template, redirect, url_for,  session, flash
from student.webforms import MyReportsReportingPeriod
from convenor.model import User
from supervisor.model import User as SUser
from student.model import SixMR
from flask_mail import Mail, Message
from admin.model import EmailSender
from convenor import model

EmailSender = EmailSender()
SixMR = SixMR()
User = User()
SUser = SUser()

# create admin blue print, use its own children templates and define route pattern
convenor = Blueprint('convenor',__name__ ,template_folder='templates', static_folder='static', url_prefix='/convenor')

@convenor.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('convenor_dashboard.html')
    else:
        return render_template('accessDenied.html')
    
# function return convenor's profile
@convenor.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # call user_model to get sql data        
        convenor = User.profile_convenor(session['username'])
        # Show the profile page with account info
        return render_template('convenor_profile.html', convenor=convenor) 
    return render_template('accessDenied.html')

# function making convenor profile page editable
@convenor.route('/profile/edit')
def profile_edit():
    if 'loggedin' in session:
        # call user_model to get sql data
        convenor = User.profile_convenor(session['username'])
        # Show the profile page with account info
        return render_template('convenor_profile_edit.html', staff=convenor, convenor=convenor)
    else:
        return render_template('accessDenied.html')

# function sending convenor user input back to update db    
@convenor.route('/profile/edit/process', methods=['POST'])
def profile_edit_process():
    if 'loggedin' in session:
        phone=request.form['phone']
        # call user_model to get sql data
        convenor = User.convenor_profile_edit_process(phone, session['username'])
        # Show the updated profile page with success flash message
        flash('Profile has been updated successfully!', 'success')
        return redirect(url_for('convenor.profile'))   
    else:
        return render_template('accessDenied.html')
   
# function to return list of students in the convenor's department
@convenor.route('/my_students')
def my_students():
    # Check if user is loggedin
    if 'loggedin' in session:
        # call user_model to get sql data
        students = User.my_students(session['username'])
        # Show a list of students in the convenor's department
        return render_template('convenor_my_students.html', students=students, username=session['username'],role=session['role'])
    # User is not loggedin redirect to login page
    return redirect(url_for('account.login'))
    
# function to return list of supervisors in the convenor's department
@convenor.route('/my_supervisors')
def my_supervisors():
    # Check if user is loggedin
    if 'loggedin' in session:
        # call user_model to run sql query that returns the convenor's department code
        department = User.department(session['username'])        
        department_code = list(department.values())[0]
        #call user_model to run sql query that returns details for supervisors in department        
        supervisors= User.my_supervisors(department_code)
        return render_template('convenor_my_supervisors.html', supervisors=supervisors, username=session['username'],role=session['role'])
    # User is not loggedin redirect to login page
    else:
        return redirect(url_for('account.login'))
    
# function returns supervisor's profile details
@convenor.route('/profile_supervisor', methods=['GET'])
def profile_supervisor():
    # Check if user is loggedin
    if 'loggedin' in session:
        SupervisorEmail = request.args.get("SupervisorEmail")
        supervisor_info = User.profile_supervisor(SupervisorEmail)        
        return render_template('convenor_profile_supervisor.html', supervisor_info=supervisor_info, username=session['username'], role=session['role'])
# User is not loggedin redirect to login page
    return redirect(url_for('account.login'))

# function to return list of convenor's supervisees (if any)
@convenor.route('/my_supervisees')
def my_supervisees():
    # Check if user is loggedin
    if 'loggedin' in session:
        # call user_model to get sql data
        supervisees = User.my_supervisees(session['username'])
        #staff = User.profile_staff(session['username'])
        # Show a list of the supervisor's supervisees
        return render_template('convenor_my_supervisees.html', supervisees=supervisees, username=session['username'],role=session['role'])
    # User is not loggedin redirect to login page
    return redirect(url_for('account.login'))

# function returns a student's profile details
@convenor.route('/profile_student', methods=['GET'])
def profile_student():
    # Check if user is loggedin
    if 'loggedin' in session:
        StudentEmail = request.args.get("StudentEmail")
        student_info = User.profile_student(StudentEmail)
        student_emp = User.student_emp(StudentEmail)
        student_sup = User.student_sup(StudentEmail)
        student_scholar = User.student_scholar(StudentEmail)
        return render_template('convenor_profile_student.html', student_info=student_info, student_sup=student_sup, student_emp=student_emp, student_scholar=student_scholar, username=session['username'], role=session['role'])
# User is not loggedin redirect to login page
    return redirect(url_for('account.login'))

# function to select the reporting period and redirect to the page with the list of reports for that period
@convenor.route('/select_reporting_period', methods=['GET', 'POST'])
def select_reporting_period():
    # Check if user is loggedin
    if 'loggedin' in session:
        form = MyReportsReportingPeriod()
        if form.validate_on_submit():
            year = form.year.data
            period = form.period.data
            period_ending = year + period
            return redirect(url_for('convenor.my_reports', period_ending=period_ending))
        return render_template('convenor_select_reporting_period.html', form=form)
    return redirect(url_for('account.login'))

@convenor.route('/my_reports/<period_ending>', methods=['GET'])
def my_reports(period_ending):
    # Check if user is loggedin
    if 'loggedin' in session:
        # Get all the reports from the convenor's dept in the chosen period in a list.
        staff_id = SUser.profile_staff(session['username'])['StaffID']
        reports= User.get_convenor_report_list(period_ending, staff_id)
        return render_template('convenor_my_reports.html', reports=reports)
    return redirect(url_for('account.login'))


# function(for convenor/pg chair) to do the final rating on the report.
@convenor.route('/final_rating/<int:student_id>/<int:report_id>', methods=['GET', 'POST'])
def final_rating(student_id, report_id):
    if 'loggedin' in session:
        if request.method == 'POST':
            # get form data.
            form_data = request.form.to_dict()
            button = request.args.get('button')
            if button == 'saveButton':
                SixMR.update_final_rating(report_id,session['username'],form_data,'save')
                flash("Form saved successfully!", 'success')
                return redirect(url_for('convenor.final_rating',student_id=student_id, report_id=report_id))
            if button == 'submitButton':
                # Update SixMR with the data, set report to 'Finalised' and get the email address of the pg admin to send email.
                pg_admin_email=SixMR.update_final_rating(report_id,session['username'],form_data,'submit')
                # update submission history
                submission_action = 'Finished final rating(Report finalised)'
                SixMR.update_submission_history(report_id,session['username'],session['role'],submission_action)
                # Send email to pg admin and update communication history
                message = f"Dear PG Administrator,\n\nA {session['role']} has submitted a finalised report (ID:{report_id}) to you. Please check the report.\n\nRegards,\n\nLUPGMS"
                EmailSender.sendEmail(pg_admin_email, message)
                SixMR.update_communication_history(pg_admin_email, message)
                # Send email to student and update communication history
                student_email = User.get_student_email(student_id)
                message = f"Dear Student,\n\nA {session['role']} has finalised your report (ID:{report_id}) and submitted it to the PG Admin. Please check the report.\n\nRegards,\n\nLUPGMS"
                EmailSender.sendEmail(student_email, message)
                SixMR.update_communication_history(student_email, message)
                # Send email to all student's supervisors and update communication history
                supervisor_emails = User.get_supervisor_emails(student_id)
                for x in supervisor_emails:
                    message = f"Dear Supervisor,\n\nA {session['role']} has finalised and submitted a report (ID:{report_id}) of your supervisees. Please check the report.\n\nRegards,\n\nLUPGMS"
                    supervisor_email = x['Email']
                    EmailSender.sendEmail(supervisor_email, message)
                    SixMR.update_communication_history(supervisor_email, message)
                flash("Form submitted successfully!", 'success')
                return redirect(url_for('supervisor.view_report',student_id=student_id, report_id=report_id))
        else:
            # display the form for convenor/pg chair to do the final rating on the report.
            # Get report finaliser(convenor/pg chair) info.
            finaliser_info = User.get_report_finaliser(session['username'])
            # Get Reporting Period End Date.
            period_ending = SixMR.get_period_ending(report_id)['ReportPeriodEndDate']
            # get student info to display on the page.
            student_info = SixMR.get_student_info(student_id)
            # get final assessment info.
            final_assessment = User.get_final_assessment(report_id)
            return render_template('convenor_final_rating.html', student_id=student_id, report_id=report_id,
            finaliser_info=finaliser_info, final_assessment=final_assessment, period_ending=period_ending, student_info=student_info)
    else:
        return redirect(url_for('account.login'))


# function returns a student's all employment history
@convenor.route('/history_emp/<argument>', methods=['GET'])
def history_emp(argument):
    student_emp = argument
    student_emp_history = model.student_emp_history(student_emp)
    return render_template('convenor_profile_history_studentemp.html',
                           student_emp_history=student_emp_history)


# function returns a student's all scholarship history
@convenor.route('/history_scholar/<argument>', methods=['GET'])
def history_scholar(argument):
    student_sch = argument
    student_scho_history = model.student_scho_history(student_sch)
    return render_template('convenor_profile_history_studentscholar.html',
                            student_scho_history=student_scho_history)