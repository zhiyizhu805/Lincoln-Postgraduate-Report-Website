from flask import Blueprint,request, render_template, redirect, url_for,  session, flash
from student.webforms import MyReportsReportingPeriod
from supervisor.model import User
from student.model import SixMRModule, SixMR
from flask_mail import Mail, Message
from admin.model import EmailSender
from supervisor import model


EmailSender = EmailSender()
SixMRModule = SixMRModule()
SixMR = SixMR()
User = User()
supervisor = Blueprint('supervisor',__name__ ,template_folder='templates', static_folder='static',  url_prefix='/supervisor')



@supervisor.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        return render_template('supervisor_dashboard.html')
    else:
        return render_template('accessDenied.html')


# function return staff profile
@supervisor.route('/profile')
def profile():
    # Check if user is loggedin
    if 'loggedin' in session:
        # call user_model to get sql data
        staff = User.profile_staff(session['username'])
        # Show the profile page with account info
        return render_template('supervisor_profile.html', staff=staff)
    return render_template('accessDenied.html')


# function making staff profile page editable
@supervisor.route('/profile/edit')
def profile_edit():
    if 'loggedin' in session:
        # call user_model to get sql data
        staff = User.profile_staff(session['username'])
        # Show the profile page with account info
        return render_template('supervisor_profile_edit.html', staff=staff)
    else:
        return render_template('accessDenied.html')


# function sending user input back to update db 
@supervisor.route('/profile/edit/process', methods=['POST'])
def profile_edit_process():
    if 'loggedin' in session:
        phone=request.form['phone']
        # call user_model to get sql data
        staff = User.profile_staff_edit_process(phone, session['username'])
        # Show the updated profile page with success flash message
        flash('Profile has been updated successfully!', 'success')
        return redirect(url_for('supervisor.profile'))
    
    else:
        return render_template('accessDenied.html')

# function to return list of supervisor's supervisees
@supervisor.route('/my_supervisees')
def my_supervisees():
    # Check if user is loggedin
    if 'loggedin' in session:
        # call user_model to get sql data
        supervisees = User.my_supervisees(session['username'])
        staff = User.profile_staff(session['username'])
        # Show a list of the supervisor's supervisees
        return render_template('my_supervisees.html', supervisees=supervisees, username=session['username'],role=session['role'])
    # User is not loggedin redirect to login page
    return redirect(url_for('account.login'))

# function returns supervisee's profile details
@supervisor.route('/profile_supervisee', methods=['GET'])
def profile_supervisee():
    # Check if user is loggedin
    if 'loggedin' in session:
        StudentEmail = request.args.get("StudentEmail")
        supervisee_info = User.profile_supervisee(StudentEmail)
        student_emp = User.student_emp(StudentEmail)
        student_sup = User.student_sup(StudentEmail)
        student_scholar = User.student_scholar(StudentEmail)
        return render_template('profile_supervisee.html', supervisee_info=supervisee_info, student_sup=student_sup, student_emp=student_emp, student_scholar=student_scholar, username=session['username'], role=session['role'])
# User is not loggedin redirect to login page
    return redirect(url_for('account.login'))

####################TO BE PROCESSED####################
####################TO BE PROCESSED####################
####################TO BE PROCESSED####################
####################TO BE PROCESSED####################
####################TO BE PROCESSED####################
# function to return a list of students then click students' name to view report
@supervisor.route('/viewstudents', methods=['POST', 'GET'])
def viewstudents():
    # Check if user is loggedin
    if 'loggedin' in session:
        # call user_model to get sql data
        student_list = User.view_student()
        # Show a list of the supervisor's supervisees
        return render_template('my_students.html', student_list=student_list)
    # User is not loggedin redirect to login page
    return redirect(url_for('account.login'))

# function to select the reporting period and redirect to the page with the list of reports for that period
@supervisor.route('/select_reporting_period', methods=['GET', 'POST'])
def select_reporting_period():
    # Check if user is loggedin
    if 'loggedin' in session:
        form = MyReportsReportingPeriod()
        if form.validate_on_submit():
            year = form.year.data
            period = form.period.data
            period_ending = year + period
            return redirect(url_for('supervisor.my_reports', period_ending=period_ending))
        return render_template('supervisor_select_reporting_period.html', form=form)
    return redirect(url_for('account.login'))

@supervisor.route('/my_reports/<period_ending>', methods=['GET'])
def my_reports(period_ending):
    # Check if user is loggedin
    if 'loggedin' in session:
        # Get all the reports from the selected period for the supervisor in a list.
        staff_id = User.profile_staff(session['username'])['StaffID']
        my_reports = User.get_supervisor_report_list(period_ending, staff_id)
        return render_template('supervisor_my_reports.html', my_reports=my_reports)
    return redirect(url_for('account.login'))

# Function for principal supervisor to accept or reject student's submitted report.
@supervisor.route('/my_reports/<int:report_id>/<action>', methods=['GET', 'POST'])
def submissionapproval(report_id, action):
    if 'loggedin' in session:
        if request.method == 'GET':
            if action == 'accept':
                # accept report and get student info to send email notification.
                student=SixMR.accept_report(report_id)
                student_name = student[0]['name']
                student_email = student[0]['email']
                period_ending = student[0]['EndDate']
                student_id = student[0]['StudentID']
                # send email notification to student
                message = f"Dear {student_name},\n\nYour report (ID:{report_id}) has been accepted by your principal supervisor.\n\nRegards,\nLUPGMS"
                EmailSender.sendEmail(student_email, message)
                # update communication history
                SixMR.update_communication_history(student_email, message)
                # update submission history
                submission_action = 'Accepted report submission'
                SixMR.update_submission_history(report_id,session['username'],'Principal Supervisor',submission_action)
                # send emails to non-principal supervisors
                non_principal_supervisor_emails = SixMR.get_non_principal_supervisor_email(student_id)
                for x in non_principal_supervisor_emails:
                    email = x['Email']
                    message = f"Dear supervisor,\n\nThe report (ID:{report_id}) of your supervisee {student_name} has been accepted by the principal supervisor. Now you can rate the student's performance.\n\nRegards,\nLUPGMS"
                    EmailSender.sendEmail(email, message)
                    # update communication history
                    SixMR.update_communication_history(email, message)
                
                # flash message to give feedback to supervisor
                flash(f'Report (ID:{report_id}) has been accepted!', 'success')
                return redirect(url_for('supervisor.my_reports', period_ending=period_ending))
        if request.method == 'POST':
            if action == 'reject':
                rejection_feedback=request.form.get('rejection_feedback')
                # reject report and get student info to send email notification.
                student=SixMR.reject_report(report_id)
                student_name = student[0]['name']
                student_email = student[0]['email']
                period_ending = student[0]['EndDate']
                # send email notification to student
                message = f"Dear {student_name},\n\nYour report (ID:{report_id}) has been rejected by your principal supervisor, please revise and resubmit.\n\nRejection Feedback:\n\n{rejection_feedback}\n\nRegards,\nLUPGMS"
                EmailSender.sendEmail(student_email, message)
                # update communication history
                SixMR.update_communication_history(student_email, message)
                # update submission history
                submission_action = 'Rejected report submission'
                SixMR.update_submission_history(report_id,session['username'],'Principal Supervisor',submission_action)
                # flash message to give feedback to supervisor
                flash(f'Report (ID:{report_id}) has been rejected!', 'success')
                return redirect(url_for('supervisor.my_reports', period_ending=period_ending))
    return redirect(url_for('account.login'))

# View 6MR report
@supervisor.route('/my_reports/<int:student_id>/<int:report_id>', methods=['GET', 'POST'])
def view_report(student_id, report_id):
    if 'loggedin' in session:
        return SixMRModule.view_6mr_report(student_id,report_id)
    else:
        return redirect(url_for('account.login'))

# Function for all supervisors to rate student's performance(fill out section E).
@supervisor.route('/rate_student/<int:student_id>/<int:report_id>', methods=['GET', 'POST'])
def supervisor_rate_student(student_id, report_id):
    if 'loggedin' in session:
        if request.method == 'POST':
            # get form data.
            form_data = request.form.to_dict()
            button = request.args.get('button')
            if button == 'saveButton':
                SixMR.update_e_table(report_id,session['username'],student_id,form_data,'save')
                flash("Form saved successfully!", 'success')
                return redirect(url_for('supervisor.supervisor_rate_student',student_id=student_id, report_id=report_id))
            if button == 'submitButton':
                SixMR.update_e_table(report_id,session['username'],student_id,form_data,'submit')
                flash("Form submitted successfully!", 'success')
                # Update submission history
                # Get the supervisor type to this student.
                supervisor_type = SixMR.get_supervisor_type(student_id,session['username'])
                submission_action = 'Finished performance rating'
                SixMR.update_submission_history(report_id,session['username'],supervisor_type,submission_action)
                # Send email to the student.
                student_info = SixMR.get_student_info(student_id)
                # ###########This is deactivated as per the PO's request.##########
                # message = f"Dear {student_info['FirstName']},\n\nYour report (ID:{report_id}) has been assessed by a supervisor. Please check your report.\n\nRegards,\n\nLUPGMS"
                #EmailSender.sendEmail(student_info['Email'], message)
                # update communication history
                #SixMR.update_communication_history(student_info['Email'], message)
                # check if all supervisors have submitted the form.
                if SixMR.if_all_supervisors_submitted(report_id) == True:
                    # Send email to the convenor/pg chair,update report status and update communication history.
                    convenor_or_pgchair_info = SixMR.get_convenor_or_pgchair_info(student_id)
                    name = convenor_or_pgchair_info['Name']
                    email = convenor_or_pgchair_info['Email']
                    message = f"Dear {name},\n\nThe report (ID:{report_id}) of {student_info['FirstName']} {student_info['LastName']} has been assessed by all supervisors. Please check the report.\n\nRegards,\n\nLUPGMS"
                    EmailSender.sendEmail(email, message)
                    # update communication history
                    SixMR.update_communication_history(email, message)
                    # update report status
                    SixMR.update_report_status(report_id,'Final rating pending')
                return redirect(url_for('supervisor.view_report',student_id=student_id, report_id=report_id))
        else:
            # get section E info to display on the page.
            # Get Reporting Period End Date.
            period_ending = SixMR.get_period_ending(report_id)['ReportPeriodEndDate']
            # get student info to display on the page.
            student_info = SixMR.get_student_info(student_id)
            # Get supervisor name and type
            supervisor_info = SixMR.get_supervisor_name_and_type(student_id, session['username'])
            # Get E_Table data
            supervisor_email = session['username']
            e_table = SixMR.get_e_table(report_id, supervisor_email, student_id)
            e_rest = SixMR.get_e_table_rest(report_id, supervisor_email, student_id)
            rating_options = ['Excellent', 'Good', 'Satisfactory', 'Below Average', 'Unsatisfactory']
            e_irco_options = ['Yes', 'No', 'N/A']


            return render_template('supervisor_rate_student.html', student_info=student_info, period_ending=period_ending,
                                    supervisor_info=supervisor_info, e_table=e_table, rating_options=rating_options,
                                    e_rest=e_rest,e_irco_options=e_irco_options, report_id=report_id, student_id=student_id)

    else:
        return redirect(url_for('account.login'))


# function returns a student's all employment history
@supervisor.route('/history_emp/<argument>', methods=['GET'])
def history_emp(argument):
    student_emp = argument
    student_emp_history = model.student_emp_history(student_emp)
    return render_template('supervisor_profile_history_studentemp.html',
                           student_emp_history=student_emp_history)


# function returns a student's all scholarship history
@supervisor.route('/history_scholar/<argument>', methods=['GET'])
def history_scholar(argument):
    student_sch = argument
    student_scho_history = model.student_scho_history(student_sch)
    return render_template('supervisor_profile_history_studentscholar.html',
                           student_scho_history=student_scho_history)