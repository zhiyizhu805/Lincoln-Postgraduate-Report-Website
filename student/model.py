from flask import Flask, Blueprint, request, render_template, redirect, url_for, session, flash
from contextlib import contextmanager
import mysql.connector
import connect
import datetime

today = datetime.date.today()
current_time = datetime.datetime.now().time()

@contextmanager
def get_cursor():
    connection = mysql.connector.connect(user=connect.dbuser,
                                         password=connect.dbpass, 
                                         host=connect.dbhost,
                                         database=connect.dbname, 
                                         autocommit=True)
    cur = connection.cursor(dictionary=True)
    try:
        yield cur
    finally:
        cur.close()
        connection.close()


class User:
    def __init__(self, email=None, password=None, student_id=None, period_ending=None, report_id=None,
                supervisorname=None, employmenttype=None, weeklyhours=None, startdate=None, enddate=None, employmentid=None):
        self.email = email
        self.password = password
        self.student_id = student_id
        self.period_ending = period_ending
        self.report_id = report_id
        self.supervisorname = supervisorname
        self.employmenttype = employmenttype
        self.weeklyhours = weeklyhours
        self.startdate = startdate
        self.enddate = enddate
        self.employmentid = employmentid


    def find_user_by_email(self, email):
        with get_cursor() as cur:
            cur.execute("SELECT * FROM User WHERE Email=%s", (email,))
            result = cur.fetchone()
        return result


    #  get Student profile
    def student_profile(self, email):
        with get_cursor() as cur:
            studentinfo_sql = """Select st.StudentID, CONCAT(st.FirstName,' ', st.LastName) as 'Student Name', st.EnrolmentDate, st.Address, st.Phone, 
                                st.Email, st.ModeOfStudy, st.ThesisTitle
                                from Student st
                                left join Department dep on st.DepartmentCode = dep.DepartmentCode
                                where st.Email = %s;"""
            cur.execute(studentinfo_sql, (email,))
            result = cur.fetchone()
        return result

    #  get Student 6mr supervisor details.
    def student_sup(self, email):
        with get_cursor() as cur:
            student_sup_sql = """select CONCAT(stf.FirstName,  ' ', stf.LastName) as 'Supervisor Name',
                                    sup.SupervisorType
                                    from Student stu
                                    left join Supervision sup on stu.StudentID = sup.StudentID
                                    left join Staff stf on sup.SupervisorID = stf.StaffID
                                    Where stu.Email = %s;"""
            cur.execute(student_sup_sql, (email,))
            result = cur.fetchall()
        return result

    #  get Student employment history details
    def student_emp_history(self, email):
        with get_cursor() as cur:
            student_emo_history_sql = """select emp.EmploymentID, CONCAT(stf.FirstName,  ' ', stf.LastName) as 'Supervisor Name', emp.SupervisorID, 
                                    empt.EmploymentType, emp.WeeklyHours, emp.StartDate, emp.EndDate, emp.StudentID
                                    from Student stu
                                    left join Employment emp on stu.StudentID = emp.StudentID
                                    left join EmploymentType empt on empt.EmploymentTypeID = emp.EmploymentTypeID
                                    left join Staff stf on emp.SupervisorID = stf.StaffID
                                    Where stu.Email = %s
                                    Order by EndDate DESC;"""
            cur.execute(student_emo_history_sql, (email,))
            result = cur.fetchall()
        return result

    #  get Student current Employment details
    def student_emp(self, email):
        with get_cursor() as cur:
            student_emo_sql = """select emp.EmploymentID, CONCAT(stf.FirstName,  ' ', stf.LastName) as 'Supervisor Name', emp.SupervisorID, 
                                    empt.EmploymentType, emp.WeeklyHours, emp.StartDate, emp.EndDate, emp.StudentID
                                    from Student stu
                                    left join Employment emp on stu.StudentID = emp.StudentID
                                    left join EmploymentType empt on empt.EmploymentTypeID = emp.EmploymentTypeID
                                    left join Staff stf on emp.SupervisorID = stf.StaffID
                                    Where stu.Email = %s AND emp.EndDate IS NULL;"""
            cur.execute(student_emo_sql, (email,))
            result = cur.fetchall()
        return result
    
    #  get Student Scholarship history details
    def student_scho_history(self, email):
        with get_cursor() as cur:
            student_scho_history_sql = """Select sr.ScholarshipID, sr.SchoRecordID, sch.Name, sch.Value, sr.StartDate, sr.EndDate, sr.StudentID
                                from Student stu
                                join ScholarshipRecord sr on stu.StudentID = sr.StudentID
                                join Scholarship sch on sr.ScholarshipID = sch.ScholarshipID
                                Where stu.Email = %s
                                order by EndDate DESC;"""
            cur.execute(student_scho_history_sql, (email,))
            result = cur.fetchall()
        return result

    #  get Student current Scholarship details
    def student_scholar(self, email):
        with get_cursor() as cur:
            student_scholar = """Select sr.ScholarshipID, sr.SchoRecordID, sch.Name, sch.Value, sr.StartDate, sr.EndDate, sr.StudentID
                                from Student stu
                                join ScholarshipRecord sr on stu.StudentID = sr.StudentID
                                join Scholarship sch on sr.ScholarshipID = sch.ScholarshipID
                                Where stu.Email = %s AND sr.EndDate>=CURDATE();"""
            cur.execute(student_scholar, (email,))
            result = cur.fetchall()
        return result
    

    #  get all Scholarship info
    def schoList(self):
        with get_cursor() as cur:
            schoList = """Select * from Scholarship;"""
            cur.execute(schoList)
            result = cur.fetchall()
        return result
    
    #  get all emp type info
    def emptList(self):
        with get_cursor() as cur:
            emptList = """Select DISTINCT emp.EmploymentTypeID, empt.EmploymentType
                        from Employment emp
                        join EmploymentType empt on emp.EmploymentTypeID = empt.EmploymentTypeID; """
            cur.execute(emptList)
            result = cur.fetchall()
        return result

    #  get all sv name info
    def svList(self):
        with get_cursor() as cur:
            svList = """Select DISTINCT emp.SupervisorID, CONCAT(stf.FirstName,  ' ', stf.LastName) as 'Supervisor Name'
                        from Employment emp
                        join Staff stf on emp.SupervisorID = stf.StaffID; """
            cur.execute(svList)
            result = cur.fetchall()
        return result


    #  edit Student profile
    def student_profile_edit_studentinfo_process(self, address, phone, email):
        with get_cursor() as cur:
            studentinfoedit_sql = """Update Student Set Address = %s, Phone = %s Where Email = %s;"""
            cur.execute(studentinfoedit_sql,(address, phone, email))
            cur.reset()
        return redirect (url_for("student.profile_edit"))
    

    #  edit Student Employment details
    def student_profile_edit_studentemp_process(self, supervisorname, employmenttype, weeklyhours, startdate, enddate, employmentid):
        with get_cursor() as cur:
            cur.execute("SELECT StaffID FROM Staff WHERE CONCAT(FirstName,' ',LastName)=%s;", (supervisorname,))
            supervisorid = cur.fetchone()['StaffID']
            cur.execute("SELECT EmploymentTypeID FROM EmploymentType WHERE EmploymentType=%s;", (employmenttype,))
            employmenttypeid = cur.fetchone()['EmploymentTypeID']
            studentempedit_sql = """Update Employment emp 
                                    left join Student stu on stu.StudentID = emp.StudentID
                                    left join EmploymentType empt on emp.EmploymentTypeID = empt.EmploymentTypeID
                                    Set SupervisorID = %s, emp.EmploymentTypeID = %s, WeeklyHours = %s, StartDate = %s, EndDate = %s
                                    Where emp.EmploymentID = %s;"""
            cur.execute(studentempedit_sql,(supervisorid, employmenttypeid, weeklyhours, startdate, enddate, employmentid))
            cur.reset()
        return redirect (url_for("student.profile_edit"))

    def profile_edit_history_emp_process(self, emp):
        with get_cursor() as cur:
            cur.execute("UPDATE Employment SET SupervisorID=%s,EmploymentTypeID=%s,WeeklyHours=%s,StartDate=%s,EndDate=%s WHERE EmploymentID=%s;",(emp[1],emp[2],emp[3],emp[4],emp[5],emp[0]))
    
    
    #  edit Student Scholarship details
    def student_profile_edit_studentscho_process(self, scholarshipname, startdate, enddate, schorecordid):
        with get_cursor() as cur:
            studentschoedit_sql= """Update ScholarshipRecord schor
                                    left join Scholarship scho on schor.ScholarshipID = scho.ScholarshipID
                                    Set schor.ScholarshipID = %s, StartDate = %s, EndDate = %s
                                    Where schor.SchoRecordID = %s;"""
            studentscho_zipped = zip(scholarshipname, startdate, enddate, schorecordid)
            for studentscho in studentscho_zipped:
                cur.execute(studentschoedit_sql,studentscho)
            cur.reset()
        return redirect (url_for("student.profile_edit"))
    
    #  add a new Scholarship record
    def student_profile_add_studentscho_process(self, studentid, scholarshipid, startdate, enddate):
        with get_cursor() as cur:
            cur.execute("""Insert into ScholarshipRecord (StudentID, ScholarshipID, StartDate, EndDate) 
                        Values (%s, %s, %s, %s);""",(studentid, scholarshipid, startdate, enddate))

    #  add a new Employment record
    def student_profile_add_studentemp_process(self, studentid, supervisorid, employmenttypid, weeklyhours, startdate, enddate):
        with get_cursor() as cur:
            if enddate is None:
                cur.execute("""INSERT INTO Employment (StudentID, SupervisorID, EmploymentTypeID, WeeklyHours, StartDate) 
                            VALUES (%s, %s, %s, %s, %s);""",
                            (studentid, supervisorid, employmenttypid, weeklyhours, startdate))
            else:
                cur.execute("""Insert into Employment (StudentID, SupervisorID, EmploymentTypeID, WeeklyHours, StartDate, EndDate) \
                            Values (%s, %s, %s, %s, %s, %s);""",
                            (studentid, supervisorid, employmenttypid, weeklyhours, startdate, enddate))



class SixMR:
    def __init__(self, email=None, password=None, student_id=None, period_ending=None, report_id=None, form_data=None,
     d1_research_objectives=None, d1_status=None, d1_comments=None,d4_objectives=None,d4_target_completion_date=None,
     d4_anticipated_problems=None, d5_items=None, d5_amount=None, d5_notes=None, report_status=None,submitter_email=None,
     role=None, message=None, action=None,submission_action=None):
        self.email = email
        self.password = password
        self.student_id = student_id
        self.period_ending = period_ending
        self.report_id = report_id
        self.form_data = form_data
        self.d1_research_objectives = d1_research_objectives
        self.d1_status = d1_status
        self.d1_comments = d1_comments
        self.d4_objectives = d4_objectives
        self.d4_target_completion_date = d4_target_completion_date
        self.d4_anticipated_problems = d4_anticipated_problems
        self.d5_items = d5_items
        self.d5_amount = d5_amount
        self.d5_notes = d5_notes
        self.report_status = report_status
        self.submitter_email = submitter_email
        self.role = role
        self.message = message
        self.action = action
        self.submission_action = submission_action

    #  Insert DueDate,B_ReportOrder and StudentID into SixMR table to start a report and get ReportID,set status to "Unfinished".
    def start_report(self, student_id, period_ending):
        with get_cursor() as cur:
            # Get report_order.
            cur.execute("SELECT COUNT(StudentID) FROM SixMR WHERE StudentID=%s;", (student_id,))
            report_order_num = cur.fetchone()['COUNT(StudentID)'] + 1
            for x in ['1st','2nd','3rd','4th','5th','6th']:
                if report_order_num == int(x[0]):
                    report_order = x
            cur.execute("INSERT INTO SixMR (ReportPeriodEndDate, B_ReportOrder, StudentID, Status) VALUES (%s, %s, %s, %s)", (period_ending, report_order, student_id, "Unfinished"))
            ReportID = cur.lastrowid
        return ReportID
    
    # Check if user already have unfinished report
    def check_unfinished_report(self, student_id):
        with get_cursor() as cur:
            cur.execute("SELECT * FROM SixMR WHERE StudentID=%s AND Status=%s;", (student_id, "Unfinished"))
            result = cur.fetchone()
            if result:
                return True
            else:
                return False
    
    # check if the Student already has a report for the chosen period.
    def check_report_period(self, student_id, period_ending):
        with get_cursor() as cur:
            cur.execute("SELECT * FROM SixMR WHERE StudentID=%s AND ReportPeriodEndDate=%s;", (student_id, period_ending))
            result = cur.fetchone()
            if result:
                return True
            else:
                return False
        
    # Check if the Student already has 6 reports.
    def check_report_number(self, student_id):
        with get_cursor() as cur:
            cur.execute("SELECT COUNT(StudentID) FROM SixMR WHERE StudentID=%s;", (student_id,))
            result = cur.fetchone()['COUNT(StudentID)']
            if result == 6:
                return True
            else:
                return False

    #  Insert ReportID to section BCDF related tables to prep the form for students to fill out.
    def insert_reportid_prep_BCDF(self, report_id):
        with get_cursor() as cur:
            ######Prep B_Table######
            # Get all the MilstoneID from Milestone table
            cur.execute("SELECT MilestoneID FROM Milestone;")
            result = cur.fetchall()
            for x in result:
                cur.execute("INSERT INTO B_Table (ReportID, MilestoneID) VALUES (%s, %s);", (report_id, x['MilestoneID']))
            ######Prep B_Approval######
            cur.execute("SELECT ApproverID FROM Approver;")
            result = cur.fetchall()
            for x in result:
                cur.execute("INSERT INTO B_Approval (ReportID, ApproverID) VALUES (%s, %s);", (report_id, x['ApproverID']))
            ######Prep C_Table######
            cur.execute("SELECT CriterionID FROM EvaluationCriterion;")
            result = cur.fetchall()
            for x in result:
                cur.execute("INSERT INTO C_Table (ReportID, CriterionID) VALUES (%s, %s);", (report_id, x['CriterionID']))
            ######Prep SupervisorAssessment table and E_Table######
            cur.execute("SELECT StudentID FROM SixMR WHERE ReportID=%s;", (report_id,))
            student_id = cur.fetchone()['StudentID']
            #get all supervision ID
            cur.execute("SELECT SupervisionID FROM Supervision WHERE StudentID=%s;", (student_id,))
            supervision_ids = cur.fetchall()
            for x in supervision_ids:
                cur.execute("INSERT INTO SupervisorAssessment (ReportID, SupervisionID) VALUES (%s, %s);", (report_id, x['SupervisionID']))
                assessment_id = cur.lastrowid
                cur.execute("SELECT CriterionID FROM AssessmentCriterion;") 
                result = cur.fetchall()
                for y in result:
                    cur.execute("INSERT INTO E_Table (AssessmentID, CriterionID) VALUES (%s, %s);", (assessment_id, y['CriterionID']))
            # Prep C_FeedbackChannel table
            cur.execute("SELECT FeedbackChannelID FROM FeedbackChannel;")
            result = cur.fetchall()
            for x in result:
                cur.execute("INSERT INTO C_FeedbackChannel (ReportID, FeedbackChannelID) VALUES (%s, %s);", (report_id, x['FeedbackChannelID']))
            # Prep F table
            cur.execute("INSERT INTO F (ReportID) VALUES (%s);", (report_id,))


    # Get current reporting period end date:
    def get_period_ending(self, report_id):
        with get_cursor() as cur:
            cur.execute("SELECT ReportPeriodEndDate FROM SixMR WHERE ReportID=%s;", (report_id,))
            result = cur.fetchone()
        return result
    
    #  get Student profile
    def student_profile(self, email):
        with get_cursor() as cur:
            cur.execute("SELECT * FROM Student WHERE Email=%s;", (email,))
            result = cur.fetchone()
        return result

    #  supervisor get Student profile
    def student_profile_edit(self, student_id):
        with get_cursor() as cur:
            cur.execute("SELECT * FROM Student WHERE StudentID=%s;", (student_id,))
            result = cur.fetchone()
        return result
    
    #  get a student's 6MR supervisors details.
    def student_supervisors(self, student_id):
        with get_cursor() as cur:
            sql = """SELECT sup.SupervisorType, CONCAT(stf.FirstName,' ',stf.LastName) 
                    AS SupervisorName
                    FROM Supervision AS sup 
                    LEFT JOIN Staff AS stf 
                    ON sup.SupervisorID=stf.StaffID
                    WHERE sup.StudentID=%s;"""
            cur.execute(sql, (student_id,))
            result = cur.fetchall()
        return result
    
    #  get a student's 6MR current Scholarship details
    def student_current_scholarship(self, student_id):
        with get_cursor() as cur:
            sql = """SELECT sch.Name, sch.Value, sr.StartDate, sr.EndDate
                    FROM ScholarshipRecord AS sr 
                    LEFT JOIN Scholarship AS sch 
                    ON sr.ScholarshipID=sch.ScholarshipID
                    WHERE sr.StudentID=%s and sr.EndDate>=%s;"""
            cur.execute(sql, (student_id,today,))
            result = cur.fetchall()
        return result
    
    # get a student's 6MR current Employment details.
    def student_current_employment(self, student_id):
        with get_cursor() as cur:
            sql = """SELECT et.EmploymentType, CONCAT(s.FirstName,' ',s.LastName) AS Name, em.WeeklyHours, em.StartDate, em.EndDate
                    FROM Employment AS em
                    LEFT JOIN EmploymentType AS et
                    ON em.EmploymentTypeID=et.EmploymentTypeID
                    LEFT JOIN Staff AS s
                    ON em.SupervisorID=s.StaffID 
                    WHERE em.StudentID=%s and em.EndDate IS NULL;"""
            cur.execute(sql, (student_id,))
            result = cur.fetchall()
        return result
    
    # Get 6MR's B_Table content.
    def get_b_table(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT b.MilestoneID, m.MilestoneName, b.IsCompleted, b.CompletionDate
                    FROM B_Table AS b
                    LEFT JOIN Milestone AS m
                    ON b.MilestoneID=m.MilestoneID
                    WHERE b.ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchall()
        return result
    
    # Get 6MR's B_Approval content.
    def get_b_approval(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT b.ApproverID, a.ApproverName, b.ApprovalStatus
                    FROM B_Approval AS b
                    LEFT JOIN Approver AS a
                    ON b.ApproverID=a.ApproverID
                    WHERE b.ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchall()
        return result
    
    # Get a student's reports list
    def get_reports(self, student_id):
        with get_cursor() as cur:
            sql = """SELECT * FROM SixMR WHERE StudentID=%s ORDER BY ReportID;"""
            cur.execute(sql, (student_id,))
            result = cur.fetchall()
            # Get the percentage of supervisor assessment completion for each report.
            if result:
                for x in result:
                    report_id = x['ReportID']
                    # Get the total number of supervisor assessments that should be done.
                    cur.execute("""SELECT COUNT(ReportID) AS 'Total' FROM SupervisorAssessment WHERE ReportID=%s;""", (report_id,))
                    total = cur.fetchone()
                    # Get the number of supervisor assessments that have been done.
                    cur.execute("""SELECT COUNT(ReportID) AS 'Total' FROM SupervisorAssessment WHERE ReportID=%s AND CompletionDate IS NOT NULL;""", (report_id,))
                    done = cur.fetchone()
                    if done:
                        percentage = str(done['Total'])+'/'+str(total['Total'])
                    else:
                        percentage = '0/'+str(total['Total'])
                    x['Percentage'] = percentage 
                    # Get the section F status for each report.
                    # if 6mr is unfinished, if section F is filled out, status is 'Yes', otherwise 'No'.
                    if x['Status'] == 'Unfinished':
                        if x['IfSectionF'] == 'Yes':
                            x['Section F'] = 'Yes'
                        if x['IfSectionF'] == 'No':
                            x['Section F'] = 'No'
                    # After the 6mr is not unfinished, if section F is responded, status is 'Responded', otherwise 'Submitted'.
                    if x['Status'] in ['Performance rating pending','Final rating pending','Finalised','Acceptance pending','Rejected']:
                        if x['IfSectionF'] == 'Yes':
                            cur.execute("""SELECT HasResponded FROM F WHERE ReportID=%s;""", (report_id,))
                            has_responded = cur.fetchone()['HasResponded']
                            if has_responded == 1:
                                x['Section F'] = 'Responded'
                            if has_responded == 0:
                                x['Section F'] = 'Submitted'
                        if x['IfSectionF'] == 'No':
                            x['Section F'] = 'N/A'
        return result
    
    # Get current report order
    def get_6mr_report_order(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT B_ReportOrder FROM SixMR WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchone()['B_ReportOrder']
        return result
    
    # Get ReportOrder table data
    def get_report_order_table(self):
        with get_cursor() as cur:
            sql = """SELECT * FROM ReportOrder;"""
            cur.execute(sql)
            result = cur.fetchall()
        return result
    
    # Get C_Table data
    def get_c_table(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT c.CriterionID,e.Criterion,c.Result,c.Comments
                    FROM C_Table AS c
                    JOIN EvaluationCriterion AS e
                    ON c.CriterionID=e.CriterionID
                    WHERE c.ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchall()
        return result
    

    # Get C_MeetingFrequency form SixMR
    def get_meeting_frequency(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT C_MeetingFrequency FROM SixMR WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchone()['C_MeetingFrequency']
        return result
    
    # Get C feedback period
    def get_feedback_period(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT C_FeedbackPeriod FROM SixMR WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchone()['C_FeedbackPeriod']
        return result
    
    # Get data from C_FeedbackChannel
    def get_c_feedback_channel_table(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT c.ReportID, c.FeedbackChannelID,f.FeedbackChannel,c.IsSelected 
                FROM C_FeedbackChannel AS c JOIN FeedbackChannel AS f
                ON c.FeedbackChannelID=f.FeedbackChannelID WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchall()
        return result
    
    
    # Get D1 table data.
    def get_d1_data(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT * FROM D1 WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchall()
        return result
    
    # Get D1 objective change data
    def get_d1_objective_change(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT D1_ObjectiveChange FROM SixMR WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchone()['D1_ObjectiveChange']
        return result
    
    # Get 6mr data
    def get_6mr_data(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT * FROM SixMR WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchone()
        return result
    
    # Get D4 data
    def get_d4_data(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT * FROM D4 WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchall()
        return result
    
    # Get D5 data
    def get_d5_data(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT * FROM D5 WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchall()
        return result
    
    # Get D5 total expenditure
    def get_d5_expenditure(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT SUM(Amount) AS Total FROM D5 WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = "$" + str(cur.fetchone()['Total']) + " NZD"
        return result
    
    # See if section F is included in the report.
    def if_section_f(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT IfSectionF FROM SixMR WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchone()['IfSectionF']
        return result
    
    # Get F table data.
    def get_f_table(self, report_id):
        with get_cursor() as cur:
            sql = """SELECT * FROM F WHERE ReportID=%s;"""
            cur.execute(sql, (report_id,))
            result = cur.fetchone()
        return result
    
    # Update ABCDF table with form data(non-list data part).
    def update_abcdf_sections_non_list_data(self, report_id,student_id,form_data):
        with get_cursor() as cur:
            d = form_data
            # update phone and addres.
            cur.execute("UPDATE Student SET Phone=%s, Address=%s WHERE StudentID=%s;", (d['phone'],d['address'],student_id,))
            for x in d.keys():
                # update B_Table.
                if x.startswith('milestone'):
                    milestone_id = x[9:]
                    is_completed = d[x]
                    completion_date = d['completion_date'+milestone_id]
                    milestone_id = int(milestone_id)
                    if is_completed == 'Yes':
                        if completion_date == '':
                            cur.execute("UPDATE B_Table SET IsCompleted=%s WHERE ReportID=%s AND MilestoneID=%s;", (is_completed,report_id,milestone_id,))
                        else:
                            cur.execute("UPDATE B_Table SET IsCompleted=%s, CompletionDate=%s WHERE ReportID=%s AND MilestoneID=%s;", (is_completed,completion_date,report_id,milestone_id,))
                    if is_completed == 'No':
                        cur.execute("UPDATE B_Table SET IsCompleted=%s, CompletionDate=NULL WHERE ReportID=%s AND MilestoneID=%s;", (is_completed,report_id,milestone_id,))
                # update B_Approval table
                if x.startswith('approver'):
                    approver_id = x[8:]
                    approval_status = d[x]
                    approver_id = int(approver_id)
                    cur.execute("UPDATE B_Approval SET ApprovalStatus=%s WHERE ReportID=%s AND ApproverID=%s;", (approval_status,report_id,approver_id,))
                # Update report_order in SixMR table
                if x =='report_order':
                    cur.execute("UPDATE SixMR SET B_ReportOrder=%s WHERE ReportID=%s;", (d[x],report_id,))
                # Update C_Table data
                if x.startswith('evaluation_criterion'):
                    criterion_id = x[20:]
                    result = d[x]
                    criterion_id = int(criterion_id)
                    cur.execute("UPDATE C_Table SET Result=%s WHERE ReportID=%s AND CriterionID=%s;", (result,report_id,criterion_id,))
                if x.startswith('ec_comment'):
                    criterion_id = x[10:]
                    comments = d[x]
                    criterion_id = int(criterion_id)
                    cur.execute("UPDATE C_Table SET Comments=%s WHERE ReportID=%s AND CriterionID=%s;", (comments,report_id,criterion_id,))
                # Update C_MeetingFrequency
                if x == 'meeting_frequency':
                    cur.execute("UPDATE SixMR SET C_MeetingFrequency=%s WHERE ReportID=%s;", (d[x],report_id,))
                # Update C_FeedbackPeriod
                if x == 'feedback_period':
                    cur.execute("UPDATE SixMR SET C_FeedbackPeriod=%s WHERE ReportID=%s;", (d[x],report_id,))
                # Update d1_objective_change
                if x == 'd1_objective_change':
                    cur.execute("UPDATE SixMR SET D1_ObjectiveChange=%s WHERE ReportID=%s;", (d[x],report_id,))
                # update d2_covid_effects
                if x == 'd2_covid_effects':
                    cur.execute("UPDATE SixMR SET D2_CovidEffects=%s WHERE ReportID=%s;", (d[x],report_id,))
                # update d3_academic_achievements
                if x == 'd3_academic_achievements':
                    cur.execute("UPDATE SixMR SET D3_AcademicAchievements=%s WHERE ReportID=%s;", (d[x],report_id,))
                # update d5_comments
                if x == 'd5_comments':
                    cur.execute("UPDATE SixMR SET D5_Comments=%s WHERE ReportID=%s;", (d[x],report_id,))
                # Update Section F content
                if x == 'if_section_f':
                    if d[x] == 'No':
                        cur.execute("UPDATE SixMR SET IfSectionF='No' WHERE ReportID=%s;", (report_id,))
                        cur.execute("UPDATE F SET SupervisorNames=NULL,Comments=NULL,TalkTo=NULL,ResponseDate=NULL,ResponseTime=Null,Response=NULL WHERE ReportID=%s;", (report_id,))
                    if d[x] == 'Yes':
                        cur.execute("UPDATE SixMR SET IfSectionF='Yes' WHERE ReportID=%s;", (report_id,))
                        if 'talkto' in d.keys():
                            cur.execute("UPDATE F SET SupervisorNames=%s,Comments=%s,TalkTo=%s WHERE ReportID=%s;", (d['reportedsupervisors'],d['complaintcontent'],d['talkto'],report_id,))
                        else:
                            cur.execute("UPDATE F SET SupervisorNames=%s,Comments=%s WHERE ReportID=%s;", (d['reportedsupervisors'],d['complaintcontent'],report_id,))

            # Update C_FeedbackChannel
            deselected_channels = [1,2,3,4]
            for x in d.keys():
                if x.startswith('feedback_channel'):
                    feedback_channel_id = x[16:]
                    feedback_channel_id = int(feedback_channel_id)
                    cur.execute("UPDATE C_FeedbackChannel SET IsSelected='Yes' WHERE ReportID=%s AND FeedbackChannelID=%s;", (report_id,feedback_channel_id,))
                    deselected_channels.remove(feedback_channel_id)
            for d in deselected_channels:
                cur.execute("UPDATE C_FeedbackChannel SET IsSelected='No' WHERE ReportID=%s AND FeedbackChannelID=%s;", (report_id,d,))


    # Update D table with form data(list data part).
    def update_d_list_data(self, report_id, d1_research_objectives, d1_status, d1_comments,
                         d4_objectives, d4_target_completion_date, d4_anticipated_problems,
                         d5_items, d5_amount, d5_notes):
        with get_cursor() as cur:
            # Delete existing data in D1 table
            cur.execute("DELETE FROM D1 WHERE ReportID=%s;", (report_id,))
            # Insert new data into D1 table
            d1_zipped = zip(d1_research_objectives, d1_status, d1_comments)
            for x in d1_zipped:
                cur.execute("INSERT INTO D1 (ReportID, ResearchObjective, Status, Comments) VALUES (%s, %s, %s, %s);", (report_id, x[0], x[1], x[2],))
            # Delete existing data in D4 table
            cur.execute("DELETE FROM D4 WHERE ReportID=%s;", (report_id,))
            # Insert new data into D4 table
            for x in range(len(d4_target_completion_date)):
                if d4_target_completion_date[x] == '':
                    d4_target_completion_date[x] = None
            d4_zipped = zip(d4_objectives, d4_target_completion_date, d4_anticipated_problems)
            for x in d4_zipped:
                cur.execute("INSERT INTO D4 (ReportID, Objective, TargetCompletionDate, AnticipatedProblems) VALUES (%s, %s, %s, %s);", (report_id, x[0], x[1], x[2],))
            #delete existing data in D5 table
            cur.execute("DELETE FROM D5 WHERE ReportID=%s;", (report_id,))
            # Insert new data into D5 table
            for x in range(len(d5_amount)):
                if d5_amount[x] == '':
                    d5_amount[x] = None
            d5_zipped = zip(d5_items, d5_amount, d5_notes)
            for x in d5_zipped:
                cur.execute("INSERT INTO D5 (ReportID, Item, Amount, Notes) VALUES (%s, %s, %s, %s);", (report_id, x[0], x[1], x[2],))  
        
    # Get a student's principal supervisor's email address for the system to send an email alert.
    def get_principal_supervisor_email(self, student_id):
        with get_cursor() as cur:
            sql = """SELECT stf.Email FROM Staff AS stf
                    LEFT JOIN Supervision AS sup
                    ON stf.StaffID=sup.SupervisorID
                    WHERE sup.StudentID=%s AND sup.SupervisorType='Principal Supervisor';"""
            cur.execute(sql, (student_id,))
            result = cur.fetchone()['Email']
            return result
    
    # Get a student's non-principal supervisors' email for the system to send an email alert .
    def get_non_principal_supervisor_email(self, student_id):
        with get_cursor() as cur:
            sql = """SELECT stf.Email FROM Staff AS stf
                    LEFT JOIN Supervision AS sup
                    ON stf.StaffID=sup.SupervisorID
                    WHERE sup.StudentID=%s AND sup.SupervisorType!='Principal Supervisor';"""
            cur.execute(sql, (student_id,))
            result = cur.fetchall()
        return result
    
    # Update 6MR report to different status.
    def update_report_status(self, report_id, status):
        with get_cursor() as cur:
            cur.execute("UPDATE SixMR SET Status=%s WHERE ReportID=%s;", (status,report_id,))
    
    # Get the current supervisor's relationship to the student
    def get_supervisor_type(self, student_id, email):
        with get_cursor() as cur:
            cur.execute("SELECT SupervisorType FROM Supervision WHERE StudentID=%s AND SupervisorID=(SELECT StaffID FROM Staff WHERE Email=%s);", (student_id,email,))
            role1 = cur.fetchone()['SupervisorType']
            # check to see if this supervisor is also a convenor.
            cur.execute("SELECT * FROM Department WHERE ConvenorID=(SELECT StaffID FROM Staff WHERE Email=%s);", (email,))
            if cur.fetchone() is not None:
                result = 'Convenor/'+role1
            else:
                result = role1
        return result 
    
    # Check if all supervisors have subbmitted their assessment.
    def if_all_supervisors_submitted(self, report_id):
        with get_cursor() as cur:
            cur.execute("SELECT * FROM SupervisorAssessment WHERE ReportID=%s AND CompletionDate IS NULL;", (report_id,))
            result = cur.fetchall()
            if result == []:
                return True
            else:
                return False
    
    # decide whether to send report to convenor or pg chair for final assessment and get that person's email and name.
    def get_convenor_or_pgchair_info(self,student_id):
        with get_cursor() as cur:
            # Check if the department's convenor is also this student's supervisor.
            cur.execute("SELECT * FROM Department WHERE ConvenorID IN (SELECT SupervisorID FROM Supervision WHERE StudentID=%s);", (student_id,))
            result = cur.fetchone()
            if result != []:
                # If true,it means one supervisor is also a convenor, so send report to pg chair.
                cur.execute("SELECT Email, FirstName AS Name FROM Staff WHERE Email=(SELECT Email FROM User WHERE Role='PG Chair');")
                result = cur.fetchone()
            else:
                # If no, send report to convenor.
                cur.execute("SELECT Email,FirstName AS Name FROM Staff WHERE StaffID=(SELECT ConvenorID FROM Department JOIN Student ON Studuent.DepartmentCode=Department.DepartmentCode WHERE StudentID=%s);",(student_id,))
                result = cur.fetchone()
            return result

    # Update submission history.
    def update_submission_history(self, report_id, submitter_email, role, submission_action):
        with get_cursor() as cur:
            if submission_action != 'Rejected report submission':
                cur.execute("INSERT INTO SubmissionHistory (ReportID, SubmitterEmail, SubmitterRole, Action, Date, Time) VALUES (%s, %s, %s, %s, %s, CURRENT_TIME());", (report_id, submitter_email, role, submission_action, today))
            if submission_action == 'Rejected report submission':
                cur.execute("DELETE FROM SubmissionHistory WHERE ReportID=%s;", (report_id,))
    
    # Update communication history.
    def update_communication_history(self, email, message):
        with get_cursor() as cur:
            Sender = "lupgms.lincoln@gmail.com"
            cur.execute("INSERT INTO Communication (Sender, Recipient, Content, SentDate, SentTime) VALUES (%s, %s, %s, %s,CURRENT_TIME());", (Sender, email, message, today))

    # For a principal supervisor to accept a report submitted by a student.
    def accept_report(self, report_id):
        with get_cursor() as cur:
            # Update report status to 'Performance rating pending'.
            cur.execute("UPDATE SixMR SET Status='Performance rating pending' WHERE ReportID=%s;", (report_id,))
            # Get Student name and email by report_id.
            cur.execute("SELECT stu.StudentID, CONCAT(stu.FirstName,' ',stu.LastName) AS name, stu.Email AS email, six.ReportPeriodEndDate AS EndDate FROM Student AS stu JOIN SixMR AS six ON stu.StudentID=six.StudentID WHERE six.ReportID=%s;", (report_id,))
            result = cur.fetchall()
        return result
    
    # For a principal supervisor to reject a report submitted by a student.
    def reject_report(self, report_id):
        with get_cursor() as cur:
            # Update report status to 'Rejected'.
            cur.execute("UPDATE SixMR SET Status='Rejected' WHERE ReportID=%s;", (report_id,))
            # Get Student name and email by report_id.
            cur.execute("SELECT stu.StudentID, CONCAT(stu.FirstName,' ',stu.LastName) AS name, stu.Email AS email, six.ReportPeriodEndDate AS EndDate FROM Student AS stu JOIN SixMR AS six ON stu.StudentID=six.StudentID WHERE six.ReportID=%s;", (report_id,))
            result = cur.fetchall()
        return result
    
    # Get student's info by id.
    def get_student_info(self, student_id):
        with get_cursor() as cur:
            cur.execute("SELECT * FROM Student WHERE StudentID=%s;", (student_id,))
            result = cur.fetchone()
        return result
    
    # Get supervisor's name and supervisor type by Student id and supervisor email.
    def get_supervisor_name_and_type(self, student_id, email):
        with get_cursor() as cur:
            # Get supervisor id by email
            cur.execute("SELECT StaffID FROM Staff WHERE Email=%s;", (email,))
            supervisor_id = cur.fetchone()['StaffID']
            # Get supervisor name and type by supervisor id and Student id.
            cur.execute("SELECT SupervisorType, CONCAT(FirstName,' ',LastName) AS Name FROM Supervision AS sup JOIN Staff AS stf ON sup.SupervisorID=stf.StaffID WHERE sup.StudentID=%s AND sup.SupervisorID=%s;", (student_id, supervisor_id,))
            result = cur.fetchone()
        return result
    
    # Get E_Table data
    def get_e_table(self, report_id, email, student_id):
        with get_cursor() as cur:
            # Get supervisorID
            cur.execute("""SELECT StaffID FROM Staff WHERE Email=%s;""",(email,))
            supervisor_id = cur.fetchone()['StaffID']
            # Get SupervisionID
            cur.execute("""SELECT SupervisionID FROM Supervision WHERE StudentID=%s AND SupervisorID=%s;""",(student_id,supervisor_id,))
            supervision_id = cur.fetchone()['SupervisionID']
            # Get AssessmentID
            cur.execute("""SELECT AssessmentID FROM SupervisorAssessment WHERE ReportID=%s AND SupervisionID=%s;""",(report_id,supervision_id,))
            assessment_id = cur.fetchone()['AssessmentID']
            # Get E_Table data
            sql = """SELECT e.CriterionID,ac.Criterion,e.Result
                    FROM E_Table AS e
                    JOIN AssessmentCriterion AS ac
                    ON e.CriterionID=ac.CriterionID
                    WHERE e.AssessmentID=%s;"""
            cur.execute(sql, (assessment_id,))
            result = cur.fetchall()
        return result
    
    # Get e_comments and E_ifRecomCrriedOut data from SupervisorAssessment table.
    def get_e_table_rest(self, report_id, email, student_id):
        with get_cursor() as cur:
            # Get supervisorID
            cur.execute("""SELECT StaffID FROM Staff WHERE Email=%s;""",(email,))
            supervisor_id = cur.fetchone()['StaffID']
            # Get SupervisionID
            cur.execute("""SELECT SupervisionID FROM Supervision WHERE StudentID=%s AND SupervisorID=%s;""",(student_id,supervisor_id,))
            supervision_id = cur.fetchone()['SupervisionID']
            # Get AssessmentID
            cur.execute("""SELECT AssessmentID FROM SupervisorAssessment WHERE ReportID=%s AND SupervisionID=%s;""",(report_id,supervision_id,))
            assessment_id = cur.fetchone()['AssessmentID']
            #Get the rest of e_table data.
            cur.execute("""SELECT E_Comments, E_IfRecomCarriedOut FROM SupervisorAssessment WHERE AssessmentID=%s;""",(assessment_id,))
            result = cur.fetchone()
        return result

    # Update E table data.
    def update_e_table(self, report_id, email, student_id, form_data, action):
        with get_cursor() as cur:
            # Get supervisorID
            cur.execute("""SELECT StaffID FROM Staff WHERE Email=%s;""",(email,))
            supervisor_id = cur.fetchone()['StaffID']
            # Get SupervisionID
            cur.execute("""SELECT SupervisionID FROM Supervision WHERE StudentID=%s AND SupervisorID=%s;""",(student_id,supervisor_id,))
            supervision_id = cur.fetchone()['SupervisionID']
            # Get AssessmentID
            cur.execute("""SELECT AssessmentID FROM SupervisorAssessment WHERE ReportID=%s AND SupervisionID=%s;""",(report_id,supervision_id,))
            assessment_id = cur.fetchone()['AssessmentID']
            # Update E_Table data
            for x in form_data.keys():
                if x.startswith('assessment_criterion'):
                    criterion_id = x[20:]
                    result = form_data[x]
                    criterion_id = int(criterion_id)
                    cur.execute("UPDATE E_Table SET Result=%s WHERE AssessmentID=%s AND CriterionID=%s;", (result,assessment_id,criterion_id,))
                if x =='e_comments':
                    comments = form_data[x]
                    cur.execute("UPDATE SupervisorAssessment SET E_Comments=%s WHERE AssessmentID=%s AND ReportID=%s;", (comments,assessment_id,report_id,)) 
                if x =='if_recom_carried_out':
                    result = form_data[x]
                    cur.execute("UPDATE SupervisorAssessment SET E_IfRecomCarriedOut=%s WHERE AssessmentID=%s AND ReportID=%s;", (result,assessment_id,report_id,))
            # Insert CompletionDate into SupervisorAssessment table if 'submit' button is clicked.
            if action == 'submit':
                cur.execute("UPDATE SupervisorAssessment SET CompletionDate=%s,CompletionTime=CURRENT_TIME() WHERE AssessmentID=%s AND ReportID=%s;", (today,assessment_id,report_id,))

    # Update SixMR table convenor rating data and return pg admin's email if ation is 'submit'.
    def update_final_rating(self, report_id, email, form_data, action):
        with get_cursor() as cur:
            if action == 'save':
                cur.execute("UPDATE SixMR SET E_ConvenorHighlight=%s, E_ConvenorRating=%s WHERE ReportID=%s;", (form_data['convenorPgchairhightlight'],form_data['convenor_rating'],report_id,))
                return None
            if action == 'submit':
                # Get current convenor/pgchair's role and id.
                cur.execute("SELECT u.Role, stf.StaffID FROM Staff AS stf JOIN User AS u ON stf.Email=u.Email WHERE stf.Email=%s;", (email,))
                result = cur.fetchone()
                cur.execute("UPDATE SixMR SET E_ConvenorHighlight=%s, E_ConvenorRating=%s, FinaliserID=%s, FinaliserRole=%s, FinalisedDate=%s, FinalisedTime=CURRENT_TIME() WHERE ReportID=%s;", (form_data['convenorPgchairhightlight'],form_data['convenor_rating'],result['StaffID'],result['Role'],today,report_id,))
                # Update status to finalised.
                cur.execute("UPDATE SixMR SET Status='Finalised' WHERE ReportID=%s;", (report_id,))
                # Get pg admin's email.
                cur.execute("SELECT Email FROM User WHERE Role='PG Administrator';")
                result = cur.fetchone()['Email']
                return result

    # Get PG Chair email
    def get_pgchair_email(self):
        with get_cursor() as cur:
            cur.execute("SELECT Email FROM User WHERE Role='PG Chair';")
            result = cur.fetchone()['Email']
        return result  

    # Get PG Admin email
    def get_pgadmin_email(self):
        with get_cursor() as cur:
            cur.execute("SELECT Email FROM User WHERE Role='PG Administrator';")
            result = cur.fetchone()['Email']
        return result      
class SixMRModule:
    def __init__(self, student_id=None, report_id=None, sixmr_instance=None):
        self.student_id = student_id
        self.report_id = report_id
        self.sixmr_instance = SixMR()

    def view_6mr_report(self, student_id, report_id):
        with get_cursor() as cur:
            ####### SECTION A ########
            # Get Reporting Period End Date.
            period_ending = self.sixmr_instance.get_period_ending(report_id)['ReportPeriodEndDate']
            # Get Student profile for Section A other than Scholarship and Employment.
            cur.execute("SELECT Email FROM Student WHERE StudentID=%s;", (student_id,))
            email = cur.fetchone()['Email']
            student_profile = self.sixmr_instance.student_profile(email)
            # Get supervision information.
            supervisors = self.sixmr_instance.student_supervisors(student_id)
            # Get current Scholarship information.
            scholarships = self.sixmr_instance.student_current_scholarship(student_id)
            # Get current employment information.
            employment = self.sixmr_instance.student_current_employment(student_id)
            ####### SECTION B ########
            # Get B_Table data.
            b_table = self.sixmr_instance.get_b_table(report_id)
            b_options = ['Yes','No']
            # Get B_Approval data.
            b_approval = self.sixmr_instance.get_b_approval(report_id)
            approval_options = ['Needed','Approval Given','Not Needed']
            # Get Report Order data
            report_order = self.sixmr_instance.get_6mr_report_order(report_id)
            report_order_table = self.sixmr_instance.get_report_order_table()
            ####### SECTION C ########
            # Get C_Table data
            c_table = self.sixmr_instance.get_c_table(report_id)
            rating_options = ['Very Good', 'Good', 'Satisfactory', 'Unsatisfactory', 'Not Relevant']
            # Get C_Meeting Frequency data. 
            frequency = self.sixmr_instance.get_meeting_frequency(report_id)
            fqc_options = ['Weekly', 'Fortnightly', 'Monthly', 'Every 3 months', 'Half yearly', 'Not at all']
            # C_Feedback period.
            feedback_period = self.sixmr_instance.get_feedback_period(report_id)
            fb_options = ['1 week','2 weeks','1 month','3 months']
            # C_Feedback channel.
            c_feedback_channel_data = self.sixmr_instance.get_c_feedback_channel_table(report_id)
            ####### SECTION D ########
            # D1 table.
            d1_data = self.sixmr_instance.get_d1_data(report_id)
            status_options = ['Completed', 'Incomplete','Select One']
            d1_objective_change = self.sixmr_instance.get_d1_objective_change(report_id)
            # D2 data.
            d2_data = self.sixmr_instance.get_6mr_data(report_id)['D2_CovidEffects']
            # D3 data.
            d3_data = self.sixmr_instance.get_6mr_data(report_id)['D3_AcademicAchievements']
            # D4 data.
            d4_data = self.sixmr_instance.get_d4_data(report_id)
            # D5 data.
            d5_data = self.sixmr_instance.get_d5_data(report_id)
            # D5 total expenditure
            d5_expenditure = self.sixmr_instance.get_d5_expenditure(report_id)
            # D5 comments
            d5_comments = self.sixmr_instance.get_6mr_data(report_id)['D5_Comments']
            ####### SECTION E ########
            # Check if at least 1 supervisor has finished a section E part of the report.
            # and get the assessmentIDs, Completion Date, supervisor names and supervisor types for the finished section E parts.
            sql = """SELECT sa.AssessmentID, sa.CompletionDate, sa.CompletionTime, CONCAT(stf.FirstName,' ',stf.LastName) AS SupervisorName, sup.SupervisorType
                    FROM SupervisorAssessment AS sa
                    JOIN Supervision AS sup
                    ON sa.SupervisionID=sup.SupervisionID
                    JOIN Staff AS stf ON sup.SupervisorID=stf.StaffID
                    WHERE sa.ReportID=%s AND sa.CompletionDate IS NOT NULL;"""
            cur.execute(sql, (report_id,))
            e_assessment_info = cur.fetchall()
            # If no section E has been completed.
            if e_assessment_info == False:
                e_assessment_content = None
            else:
            # If at least 1 section E has been completed, get section E content
                assessment_ids = []
                for row in e_assessment_info:
                    assessment_ids.append(row['AssessmentID'])
                e_assessment_content = []
                for assessment_id in assessment_ids:
                    # Get section E data.
                    # 1.Get E_Table data
                    cur.execute("""SELECT e.CriterionID,ac.Criterion,e.Result FROM E_Table AS e JOIN AssessmentCriterion AS ac ON e.CriterionID=ac.CriterionID WHERE e.AssessmentID=%s;""", (assessment_id,))
                    e_table = cur.fetchall()
                    # 2.Get the rest of the Section E data.
                    cur.execute("""SELECT E_Comments, E_IfRecomCarriedOut FROM SupervisorAssessment WHERE AssessmentID=%s;""",(assessment_id,))
                    e_rest = cur.fetchone()
                    # pack all the e_assessment_info and e_table data into a list of dictionaries.
                    index = assessment_ids.index(assessment_id)
                    e_assessment_content.append({'e_assessment_info':e_assessment_info[index],'e_table':e_table,'e_rest':e_rest})
            e_rating_options = ['Excellent', 'Good', 'Satisfactory', 'Below Average', 'Unsatisfactory']
            e_irco_options = ['Yes', 'No', 'N/A']
            # Section E Convenor/PG Chair part
            # Get the section E convenor/PG Chair assessment content.
            cur.execute("""SELECT * FROM SixMR WHERE ReportID=%s AND Status='Finalised';""",(report_id,))
            final_assessment = cur.fetchone()
            # If the report has been finalised.
            if final_assessment:
                #Get the convenor/pg chair's name,role,FinalisedDate.
                cur.execute("""SELECT CONCAT(stf.FirstName,' ',stf.LastName) AS FinaliserName, six.FinaliserRole, six.FinalisedDate, six.FinalisedTime FROM SixMR AS six JOIN Staff AS stf ON stf.StaffID=six.FinaliserID WHERE six.ReportID=%s;""",(report_id,))
                finaliser_info = cur.fetchone()
                is_finalised = True
            else:
                finaliser_info = None
                is_finalised = False
            ####### SECTION F ########
            # See if section F is included.
            if_section_f = self.sixmr_instance.if_section_f(report_id)
            if if_section_f == 'Yes':
                # Get F_Table data.
                f_table = self.sixmr_instance.get_f_table(report_id)
                # Check if pg chair has resonded to the section f
                cur.execute("""SELECT * FROM F WHERE ReportID=%s AND HasResponded=1;""",(report_id,))
                pgChair_response=cur.fetchone()
                if pgChair_response==None:
                    pgChair_response = False
            else:
                f_table = False
                pgChair_response = False
        
        return render_template('view_6mr_report.html',period_ending=period_ending,
        student_profile=student_profile,supervisors=supervisors,scholarships=scholarships,
        employment=employment,b_table=b_table,b_options=b_options,b_approval=b_approval,
        approval_options=approval_options,report_order=report_order,report_order_table=report_order_table,
        c_table=c_table,rating_options=rating_options,frequency=frequency,fqc_options=fqc_options,
        feedback_period=feedback_period,fb_options=fb_options,c_feedback_channel_data=c_feedback_channel_data,
        d1_data=d1_data,status_options=status_options,d1_objective_change=d1_objective_change,
        d2_data=d2_data,d3_data=d3_data,d4_data=d4_data,d5_data=d5_data,d5_comments=d5_comments,
        d5_expenditure=d5_expenditure,f_table=f_table,student_id=student_id,report_id=report_id,
        e_assessment_content=e_assessment_content,e_rating_options=e_rating_options,e_irco_options=e_irco_options,
        finaliser_info=finaliser_info,final_assessment=final_assessment,pgChair_response=pgChair_response,
        is_finalised=is_finalised)