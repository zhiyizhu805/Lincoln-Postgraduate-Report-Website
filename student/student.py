from flask import Flask,Blueprint,request, render_template, redirect, url_for,  session, flash
from student.webforms import ReportingPeriod
from student.model import User, SixMR, SixMRModule
from datetime import datetime
from flask_mail import Mail, Message
from admin.model import EmailSender


EmailSender = EmailSender()
User = User()
SixMR = SixMR()
SixMRModule = SixMRModule()

student = Blueprint('student',__name__, template_folder='templates', static_folder='static', url_prefix='/student')


@student.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """Student dashboard after logging in."""
    if 'loggedin' in session:
        return render_template('student_dashboard.html')
    else:
        return render_template('accessDenied.html')#


@student.route('/profile')
def profile():
    if 'loggedin' in session:
        student = User.student_profile(session['username'])
        student_emp = User.student_emp(session['username'])
        student_sup = User.student_sup(session['username'])
        student_scholar = User.student_scholar(session['username'])
        # Show the profile page with account info
        return render_template('student_profile.html',
                               student=student,
                               student_sup=student_sup,
                               student_emp=student_emp,
                               student_scholar=student_scholar,
                               username=session['username'], role=session['role'])
    # User is not loggedin redirect to login page

        return render_template('student_profile.html', student=student)

    else:
        return render_template('accessDenied.html')


# function making student profile page (info) editable
@student.route('/profile/edit/studentinfo')
def profile_edit():
    if 'loggedin' in session:
        student = User.student_profile(session['username'])
        # Show the profile page with account info
        return render_template('student_profile_edit_studentinfo.html', student=student)
    else:
        return render_template('accessDenied.html')


# function sending user input back to update (info) db 
@student.route('/profile/edit/studentinfo/process', methods=['POST'])
def profile_edit_process():
    if 'loggedin' in session:
        address=request.form['address']
        phone=request.form['phone']
        # call user_model to get sql data
        student = User.student_profile_edit_studentinfo_process(address, phone, session['username'])
        # Show the updated profile page with success flash message
        flash('Your profile has been successfully updated!', 'success')
        return redirect(url_for('student.profile'))   
    else:
        return render_template('accessDenied.html')
    
# function showing student employment history
@student.route('/profile/history/studentemp')
def profile_history_emp():
    if 'loggedin' in session:
        student_emp_history = User.student_emp_history(session['username'])
        return render_template('student_profile_history_studentemp.html',
                               student_emp_history=student_emp_history,
                               username=session['username'], role=session['role'])
    # User is not loggedin redirect to login page
    else:
        return render_template('accessDenied.html')
    
# function making student employment history editable
@student.route('/profile/edit/history/studentemp')
def profile_edit_history_emp():
    if 'loggedin' in session:
        student_emp_history = User.student_emp_history(session['username'])
        svList=User.svList()
        emptList=User.emptList()
        return render_template('student_profile_edit_history_studentemp.html',
                               student_emp_history=student_emp_history,
                               svList=svList,
                               emptList=emptList,
                               username=session['username'], role=session['role'])
    # User is not loggedin redirect to login page
    else:
        return render_template('accessDenied.html')

# function making student profile page (emp) editable
@student.route('/profile/edit/studentemp')
def profile_edit_emp():
    if 'loggedin' in session:
        student_emp = User.student_emp(session['username'])
        # Show the profile page with account info
        return render_template('student_profile_edit_studentemp.html', 
                               student=student,
                               student_emp=student_emp,
                               username=session['username'])
    else:
        return render_template('accessDenied.html')

# function sending user input back to update (emp history) db 
@student.route('/profile/edit/history/studentemp/process', methods=['POST'])
def profile_edit_history_emp_process():
    if 'loggedin' in session:
        employmentid=request.form.getlist('employmentid')
        supervisorname=request.form.getlist('supervisorname')
        employmenttype=request.form.getlist('employmenttype')
        weeklyhours=request.form.getlist('weeklyhours')
        startdate=request.form.getlist('startdate')
        enddate=request.form.getlist('enddate')
        # if end date input were empty, will defaultly show as 'ongoing'
        processed_enddate = []
        for date in enddate:
            if date == '':
                processed_enddate.append(None)
            else:
                processed_enddate.append(date) 
        # zip all the data into a list of tuples
        emp_history = zip(employmentid,supervisorname,employmenttype,weeklyhours,startdate,processed_enddate)
        for emp in emp_history:
            User.profile_edit_history_emp_process(emp)
        # Show the updated profile page with success flash message
        flash('Your employment history has been successfully updated!', 'success')
        return redirect(url_for('student.profile_history_emp'))   
    else:
        return render_template('accessDenied.html')    

# function sending user input back to update (emp) db 
@student.route('/profile/edit/studentemp/process', methods=['POST'])
def profile_edit_emp_process():
    if 'loggedin' in session:
        employmentid=request.form.get('employmentid')
        supervisorname=request.form.get('supervisorname')
        employmenttype=request.form.get('employmenttype')
        weeklyhours=request.form.get('weeklyhours')
        startdate=request.form.get('startdate')
        enddate=request.form.get('enddate')
        # if end date input were empty, it is the current employment.
        if enddate == '':
            enddate = None
        else:
            enddate = enddate
        # call user_model to get sql data
        student = User.student_profile_edit_studentemp_process(supervisorname, employmenttype, weeklyhours, startdate, enddate, employmentid)
        # Show the updated profile page with success flash message
        flash('Your profile has been successfully updated!', 'success')
        return redirect(url_for('student.profile'))   
    else:
        return render_template('accessDenied.html')
    

# function go to a new page to add an employment record
@student.route('/profile/add/studentemp')
def profile_add_emp():
    if 'loggedin' in session:
        student_id = User.student_profile(session['username'])['StudentID']
        emptList = User.emptList()
        svList = User.svList()
        # Show the profile page with account info
        return render_template('student_profile_add_studentemp.html', 
                               student_id=student_id,
                               emptList=emptList,
                               svList=svList,
                               username=session['username'])
    else:
        return render_template('accessDenied.html')
    

# function sending new employment record to (emp) db
@student.route('/profile/add/studentemp/process', methods=['POST'])
def profile_add_emp_process():
    if 'loggedin' in session:
        studentid=request.form.get('studentid')
        supervisorid=request.form.get('supervisorid')
        employmenttypeid=request.form.get('employmenttypeid')
        weeklyhours=request.form.get('weeklyhours')
        startdate=request.form.get('startdate')
        enddate=request.form.get('enddate')
        if enddate == '':
            enddate = None
        else:
            enddate = enddate
        student = User.student_profile_add_studentemp_process(studentid, supervisorid, employmenttypeid, weeklyhours, startdate, enddate)
        emptList = User.emptList()
        svList = User.svList()
        # Show the updated profile page with success flash message
        flash('Your employment record has been added successfully!', 'success')
        return redirect(url_for('student.profile'))   
    else:
        return render_template('accessDenied.html')


# function showing student scholarship history
@student.route('/profile/history/studentscho')
def profile_history_scho():
    if 'loggedin' in session:
        student_scho_history = User.student_scho_history(session['username'])
        return render_template('student_profile_history_studentscho.html',
                               student_scho_history=student_scho_history,
                               username=session['username'], role=session['role'])
    # User is not loggedin redirect to login page
    else:
        return render_template('accessDenied.html')



# function making student scholarship history editable
@student.route('/profile/edit/history/studentscho')
def profile_edit_history_scho():
    if 'loggedin' in session:
        student_scho_history = User.student_scho_history(session['username'])
        schoList = User.schoList()
        # Show the profile page with account info
        return render_template('student_profile_edit_history_studentscho.html', 
                               student=student,
                               student_scho_history=student_scho_history,
                               schoList=schoList,
                               username=session['username'])
    else:
        return render_template('accessDenied.html')   
    



# function making student profile page (current scho) editable
@student.route('/profile/edit/studentscho')
def profile_edit_scho():
    if 'loggedin' in session:
        student_scholar = User.student_scholar(session['username'])
        schoList = User.schoList()
        # Show the profile page with account info
        return render_template('student_profile_edit_studentscho.html', 
                               student=student,
                               student_scholar=student_scholar,
                               schoList=schoList,
                               username=session['username'])
    else:
        return render_template('accessDenied.html')
    

# function sending user input back to update (scho history) db 
@student.route('/profile/edit/history/studentscho/process', methods=['POST'])
def profile_edit_history_scho_process():
    if 'loggedin' in session:
        startdate=request.form.getlist('startdate')
        enddate=request.form.getlist('enddate')
        schorecodid=request.form.getlist('schorecordid')
        scholarshipname=request.form.getlist('scholarshipname')
        # call user_model to get sql data
        student = User.student_profile_edit_studentscho_process(scholarshipname, startdate, enddate, schorecodid)
        # Show the updated profile page with success flash message
        flash('Your scholarship history has been successfully updated!', 'success')
        return redirect(url_for('student.profile_history_scho'))   
    else:
        return render_template('accessDenied.html')

# function sending user input back to update (current scho) db 
@student.route('/profile/edit/studentscho/process', methods=['POST'])
def profile_edit_scho_process():
    if 'loggedin' in session:
        startdate=request.form.getlist('startdate')
        enddate=request.form.getlist('enddate')
        schorecodid=request.form.getlist('schorecordid')
        scholarshipname=request.form.getlist('scholarshipname')
        # call user_model to get sql data
        student = User.student_profile_edit_studentscho_process(scholarshipname, startdate, enddate, schorecodid)
        # Show the updated profile page with success flash message
        flash('Your profile has been successfully updated!', 'success')
        return redirect(url_for('student.profile'))   
    else:
        return render_template('accessDenied.html')


# function go to a new page to add a scholarship
@student.route('/profile/add/studentscho')
def profile_add_scho():
    if 'loggedin' in session:
        student_id = User.student_profile(session['username'])['StudentID']
        schoList = User.schoList()
        # Show the profile page with account info
        return render_template('student_profile_add_studentscho.html', 
                               student_id=student_id,
                               schoList=schoList,
                               username=session['username'])
    else:
        return render_template('accessDenied.html')


# function sending new scholarship record to (scho) db
@student.route('/profile/add/studentscho/process', methods=['POST'])
def profile_add_scho_process():
    if 'loggedin' in session:
        studentid=request.form.get('studentid')
        scholarshipid=request.form.get('scholarshipid')
        startdate=request.form.get('startdate')
        enddate=request.form.get('enddate')
        scholarshipid = int(scholarshipid)
        # call user_model to get sql data
        student = User.student_profile_add_studentscho_process(studentid, scholarshipid, startdate, enddate)
        # Show the updated profile page with success flash message
        flash('Your scholarship record has been successfully added!', 'success')
        return redirect(url_for('student.profile_history_scho'))   
    else:
        return render_template('accessDenied.html')



@student.route('/start_report', methods=['GET', 'POST'])
def start_report():
    """Intermediary page for student to select the reporting period to continue or to quit."""
    # Check if user is loggedin
    if 'loggedin' in session:
        form = ReportingPeriod()
        if form.validate_on_submit():
            year = form.year.data
            period = form.period.data
            period_ending = year + period
            # Get student_id
            student_id = User.student_profile(session['username'])['StudentID']
            # Check if already have unfinished report, if yes, flash message and ask to go to my reports page.
            if SixMR.check_unfinished_report(student_id) == True:
                flash('You have an unfinished report. Please go to My Reports and complete it.', 'warning')
                return render_template('student_start_report.html', form=form)
            # Check if the student already has a report for the period, if yes, flash message and ask to choose a different period.
            elif SixMR.check_report_period(student_id, period_ending) == True:
                flash('You already have a report for this period!', 'warning')
                return render_template('student_start_report.html', form=form)
            # check if the student already has 6 reports.
            elif SixMR.check_report_number(student_id) == True:
                flash('You already have 6 reports!', 'warning')
                return render_template('student_start_report.html', form=form)
            else:# Insert period_ending(DueDate) into database and start a report and get ReportID.
                report_id = SixMR.start_report(student_id, period_ending)
                ######### Insert the ReportID into the compulsory BCDF related tables to prep the form #########
                SixMR.insert_reportid_prep_BCDF(report_id)
                # Redirect to report page with report_id and student_id.
                return redirect(url_for('student.report', student_id=student_id,report_id=report_id, action='edit'))
        return render_template('student_start_report.html', form=form)
    # User is not loggedin redirect to login page
    else:
        return redirect(url_for('account.login'))



# Use this function to display all the reports for the student. and use separate functions to save each report.
@student.route('/report/<int:student_id>/<int:report_id>/<action>', methods=['GET', 'POST'])
def report(student_id, report_id, action):
    """Student report page."""
    # Check if user is loggedin
    if 'loggedin' in session:
        if request.method == 'POST':
            # Get Section A data.
            form_data = request.form.to_dict()
            # update the report with the form data(all the non-list data).
            SixMR.update_abcdf_sections_non_list_data(report_id,student_id,form_data)
            ####Update section D list data
            # Get Section D1 list data: Research Objectives.
            d1_research_objectives = request.form.getlist('d1_research_objectives[]')
            d1_status = request.form.getlist('d1_status[]')
            d1_comments = request.form.getlist('d1_comments[]')
            # Get Section D4 list data: Covid Effects.
            d4_objectives = request.form.getlist('d4_objectives[]')
            d4_target_completion_date = request.form.getlist('d4_target_completion_date[]')
            d4_anticipated_problems = request.form.getlist('d4_anticipated_problems[]')
            # Get d5 list data.
            d5_items = request.form.getlist('d5_items[]')
            d5_amount = request.form.getlist('d5_amount[]')
            d5_notes = request.form.getlist('d5_notes[]')
            # update D table with the list data.
            SixMR.update_d_list_data(report_id,d1_research_objectives,d1_status,d1_comments,
                                    d4_objectives,d4_target_completion_date,d4_anticipated_problems,
                                    d5_items,d5_amount,d5_notes)
            button = request.args.get('button')
            if button == 'saveButton':
                flash("Form saved successfully!", 'success') 
                action = 'edit'
                return redirect(url_for('student.report', student_id=student_id,report_id=report_id, action=action))
            if button == 'submitButton':
                flash("Form submitted successfully!", 'success')
                # Update submission history.
                submitter_email = session['username']
                role = session['role']
                submission_action = 'Submitted report'
                SixMR.update_submission_history(report_id, submitter_email, role, submission_action)
                # Send email notification to the principal supervisor.
                email = SixMR.get_principal_supervisor_email(student_id)
                name = User.student_profile(session['username'])['Student Name']
                message = f"Dear supervisor,\n\n{name}(student id: {student_id}) has submitted a 6-Month Report(report id:{report_id})!\n\nRegards,\n\nLUPGMS"
                EmailSender.sendEmail(email, message)
                # Update communication history.
                SixMR.update_communication_history(email, message)
                # Check if student has filledout section F, if yes, send email to the PG Chair.
                # See if section F is included.
                if_section_f = SixMR.if_section_f(report_id)
                if if_section_f == 'Yes':
                    # Send email notification to the PG Chair.
                    message = f"Dear PG Chair,\n\n{name}(student id: {student_id}) has submitted a student assessment of Supervision, Technical and Administrative Support(Section F) of the 6-Month Report(report id:{report_id})!\n\nRegards,\n\nLUPGMS"
                    # Get PG Chair email.
                    email = SixMR.get_pgchair_email()
                    EmailSender.sendEmail(email, message)
                    # Update communication history.
                    SixMR.update_communication_history(email, message) 
                # Update report status to submitted to principle supervisor.
                SixMR.update_report_status(report_id, 'Acceptance pending')
                action = 'view'
                return SixMRModule.view_6mr_report(student_id,report_id)
            # get data and save the whole report or part of report, tbdecided.
        else:
            ####### SECTION A ########
            # Get Reporting Period End Date.
            period_ending = SixMR.get_period_ending(report_id)['ReportPeriodEndDate']
            # Get student profile for Section A other than scholarship and employment.
            student_profile = SixMR.student_profile(session['username'])
            # Get supervision information.
            supervisors = SixMR.student_supervisors(student_id)
            # Get current scholarship information.
            scholarships = SixMR.student_current_scholarship(student_id)
            # Get current employment information.
            employment = SixMR.student_current_employment(student_id)
            ####### SECTION B ########
            # Get B_Table data.
            b_table = SixMR.get_b_table(report_id)
            b_options = ['Yes','No']
            # Get B_Approval data.
            b_approval = SixMR.get_b_approval(report_id)
            approval_options = ['Needed','Approval Given','Not Needed']
            # Get Report Order data
            report_order = SixMR.get_6mr_report_order(report_id)
            report_order_table = SixMR.get_report_order_table()
            ####### SECTION C ########
            # Get C_Table data
            c_table = SixMR.get_c_table(report_id)
            rating_options = ['Very Good', 'Good', 'Satisfactory', 'Unsatisfactory', 'Not Relevant']
            # Get C_Meeting Frequency data. 
            frequency = SixMR.get_meeting_frequency(report_id)
            fqc_options = ['Weekly', 'Fortnightly', 'Monthly', 'Every 3 months', 'Half yearly', 'Not at all']
            # C_Feedback period.
            feedback_period = SixMR.get_feedback_period(report_id)
            fb_options = ['1 week','2 weeks','1 month','3 months']
            # C_Feedback channel.
            c_feedback_channel_data = SixMR.get_c_feedback_channel_table(report_id)
            # D1 table.
            d1_data = SixMR.get_d1_data(report_id)
            status_options = ['Completed', 'Incomplete','Select One']
            d1_objective_change = SixMR.get_d1_objective_change(report_id)
            # D2 data.
            d2_data = SixMR.get_6mr_data(report_id)['D2_CovidEffects']
            # D3 data.
            d3_data = SixMR.get_6mr_data(report_id)['D3_AcademicAchievements']
            # D4 data.
            d4_data = SixMR.get_d4_data(report_id)
            # D5 data.
            d5_data = SixMR.get_d5_data(report_id)
            # D5 total expenditure
            d5_expenditure = SixMR.get_d5_expenditure(report_id)
            # D5 comments
            d5_comments = SixMR.get_6mr_data(report_id)['D5_Comments']
            # See if section F is included.
            if_section_f = SixMR.if_section_f(report_id)
            if if_section_f == 'Yes':
                # Get F_Table data.
                f_table = SixMR.get_f_table(report_id)
            else:
                f_table = False
            # set a view only mode for the report.
            if action == 'view':
                status = 'disabled'
            else:
                status = ''
            return render_template('student_report.html',period_ending=period_ending,
            student_profile=student_profile,supervisors=supervisors,scholarships=scholarships,
            employment=employment,b_table=b_table,b_options=b_options,b_approval=b_approval,
            approval_options=approval_options,report_order=report_order,report_order_table=report_order_table,
            c_table=c_table,rating_options=rating_options,frequency=frequency,fqc_options=fqc_options,
            feedback_period=feedback_period,fb_options=fb_options,c_feedback_channel_data=c_feedback_channel_data,
            d1_data=d1_data,status_options=status_options,d1_objective_change=d1_objective_change,
            d2_data=d2_data,d3_data=d3_data,d4_data=d4_data,d5_data=d5_data,d5_comments=d5_comments,
            d5_expenditure=d5_expenditure,f_table=f_table,student_id=student_id,report_id=report_id,
            status=status)
    else:    
        return redirect(url_for('account.login'))


@student.route('/my_reports', methods=['GET', 'POST'])
def my_reports():
    """Show all the student's reports."""
    if 'loggedin' in session:
        # Get reports for the student.
        student_id = User.student_profile(session['username'])['StudentID']
        reports = SixMR.get_reports(student_id)
        return render_template('student_my_reports.html', reports=reports)
    else:
        return redirect(url_for('account.login'))
    

# View 6MR report
@student.route('/my_reports/<int:student_id>/<int:report_id>', methods=['GET', 'POST'])
def view_report(student_id, report_id):
    if 'loggedin' in session:
        return SixMRModule.view_6mr_report(student_id,report_id)
    else:
        return redirect(url_for('account.login'))





