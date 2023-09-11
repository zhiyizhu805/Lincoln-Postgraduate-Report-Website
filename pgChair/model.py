import mysql.connector
import connect
from flask import redirect, url_for
from datetime import datetime

current_date = datetime.now().strftime("%Y-%m-%d")
current_time = datetime.now().strftime("%H:%M:%S")
# Database connection.
dbconn = None


def getCursor():
    global dbconn
    global connection
    if dbconn == None:
        connection = mysql.connector.connect(user=connect.dbuser,
                                             password=connect.dbpass, host=connect.dbhost,
                                             database=connect.dbname, autocommit=True)
        dbconn = connection.cursor(dictionary=True)
        return dbconn
    
cur = getCursor()

class User:
    def __init__(self, email=None, password=None, period_ending=None, report_id=None, response=None, action=None):
        self.email = email
        self.password = password
        self.period_ending = period_ending
        self.report_id = report_id
        self.response = response
        self.action = action

# sql - get supervisor's details for their profile 
    def profile_supervisor(self, SupervisorEmail):
        supervisorinfo_sql = """Select CONCAT(stf.FirstName,' ', stf.LastName) as 'Staff Name', stf.Phone,
                            stf.Email, dep.DepartmentName, dep.Faculty
                            from Staff stf     
                            left join Department dep on stf.DepartmentCode = dep.DepartmentCode                       
                            where stf.Email = %s;"""
        cur.execute(supervisorinfo_sql, (SupervisorEmail,))
        result = cur.fetchone()
        return result

# sql - get student's details for their profile 
    def profile_student(self, StudentEmail):
        studentinfo_sql = """Select st.StudentID, CONCAT(st.FirstName,' ', st.LastName) as 'Student Name', st.Email as 'Student Email', st.EnrolmentDate, st.Address, st.Phone, 
                            st.Email, st.ModeOfStudy, st.ThesisTitle
                            from Student st
                            left join Department dep on st.DepartmentCode = dep.DepartmentCode
                            where st.Email = %s;"""
        cur.execute(studentinfo_sql, (StudentEmail,))
        result = cur.fetchone()
        return result
    
# sql - get Student's current Employment details
    def student_emp(self, StudentEmail):
        student_emo_sql = """select emp.EmploymentID, CONCAT(stf.FirstName,  ' ', stf.LastName) as 'Supervisor Name', emp.SupervisorID, 
                                empt.EmploymentType, emp.WeeklyHours, emp.StartDate, emp.EndDate, emp.StudentID
                                from Student stu
                                left join Employment emp on stu.StudentID = emp.StudentID
                                left join EmploymentType empt on empt.EmploymentTypeID = emp.EmploymentTypeID
                                left join Staff stf on emp.SupervisorID = stf.StaffID
                                Where stu.Email = %s AND emp.EndDate IS NULL;"""
        cur.execute(student_emo_sql, (StudentEmail,))
        result = cur.fetchall()
        return result
      
# sql - get Student 6mr supervisor details.
    def student_sup(self, StudentEmail):
        student_sup_sql = """select CONCAT(stf.FirstName,  ' ', stf.LastName) as 'Supervisor Name',
                                sup.SupervisorType
                                from Student stu
                                left join Supervision sup on stu.StudentID = sup.StudentID
                                left join Staff stf on sup.SupervisorID = stf.StaffID
                                Where stu.Email = %s;"""
        cur.execute(student_sup_sql, (StudentEmail,))
        result = cur.fetchall()
        return result
    
# sql - get supervisee's current scholarship info
    def student_scholar(self, StudentEmail):
        student_scholar = """Select sr.SchoRecordID, sch.Name, sch.Value, sr.StartDate, sr.EndDate, sr.StudentID
                            from Student stu
                            join ScholarshipRecord sr on stu.StudentID = sr.StudentID
                            join Scholarship sch on sr.ScholarshipID = sch.ScholarshipID
                            Where stu.Email = %s AND sr.EndDate>CURDATE();"""
        cur.execute(student_scholar, (StudentEmail,))
        result = cur.fetchall()
        return result
    
    # sql - get pgChair profile
    def profile_pgChair(self, email):
        pgChairinfo_sql = """Select CONCAT(stf.FirstName, ' ', stf.LastName) as 'Staff Name', stf.Phone,
                                stf.Email, dep.DepartmentName, dep.Faculty
                            from Staff stf 
                            left join Department dep on stf.DepartmentCode = dep.DepartmentCode
                            where stf.Email = %s;"""
        cur.execute(pgChairinfo_sql, (email,))
        result = cur.fetchone()
        return result

    #sql - edit pgChair profile
    def profile_pgChair_edit_process(self, phone, email):
        pgChairinfoedit_sql = """Update Staff Set Phone = %s Where Email = %s;"""
        cur.execute(pgChairinfoedit_sql,(phone, email))

    
    def get_pgchair_report_list(self, period_ending):
        sql = """SELECT s.ReportID AS 'Report ID', s.ReportPeriodEndDate AS 'End Date', s.B_ReportOrder AS 'Report Order',s.StudentID AS 'Student ID', CONCAT(stu.FirstName, ' ', stu.LastName) as 'Student Name', s.Status, s.IfSectionF
                    FROM SixMR AS s JOIN Student AS stu
                    ON s.StudentID=stu.StudentID
                    WHERE s.ReportPeriodEndDate=%s AND s.Status NOT IN ('Unfinished')
                    ORDER BY s.ReportID DESC;"""
        cur.execute(sql, (period_ending,))
        result = cur.fetchall()
        # Get the percentage of supervisor assessment completion for each report.
        for x in result:
            report_id = x['Report ID']
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
            # Find out if the PG Chair needs to do the final rating.(when the Student's convenor is also a supervisor)
            cur.execute("""SELECT * FROM Supervision WHERE StudentID=%s AND SupervisorID IN (SELECT ConvenorID FROM Department);""", (x['Student ID'],))
            resultdata=cur.fetchall()
            if resultdata:
                x['PgChairToRate'] = True
            else:
                x['PgChairToRate'] = False
            # Check if the PG chair has responded to the section F.
            if x['IfSectionF'] == 'Yes':
                cur.execute("""SELECT HasResponded FROM F WHERE ReportID=%s;""", (report_id,))
                HasReponded = cur.fetchone()['HasResponded']
                if HasReponded == 1:
                    x['HasResponded'] = True
                if HasReponded == 0:
                    x['HasResponded'] = False
            else:
                x['HasResponded'] = False
        
        return result

    # Get the F response content. 
    def get_pgchair_response(self, report_id):
        sql = """SELECT * FROM F WHERE ReportID=%s;"""
        cur.execute(sql, (report_id,))
        result = cur.fetchone()
        return result
    
    # Get the student's details.
    def get_student(self, report_id):
        sql = """SELECT * FROM Student WHERE StudentID=(SELECT StudentID FROM SixMR WHERE ReportID=%s);"""
        cur.execute(sql, (report_id,))
        result = cur.fetchone()
        return result
    
    # Save the F response content and relevant F table columns.
    def update_pgchair_response(self, report_id, response, action):
        if action == 'save':
            sql = """UPDATE F SET Response=%s WHERE ReportID=%s;"""
            cur.execute(sql, (response, report_id))
        if action == 'submit':
            sql = """UPDATE F SET Response=%s, HasResponded=1,ResponseDate=%s, ResponseTime=%s WHERE ReportID=%s;"""
            cur.execute(sql, (response, current_date, current_time, report_id))
            # Get the student's email.
            cur.execute("""SELECT Email FROM Student WHERE StudentID=(SELECT StudentID FROM SixMR WHERE ReportID=%s);""", (report_id,))
            student_email = cur.fetchone()['Email']
            return student_email

def get_all_student():
    student_list = """select stu.StudentID, CONCAT(stu.FirstName, ' ', stu.LastName) as 'FullName', 
            stu.Email, stu.ThesisTitle, stu.EnrolmentDate, stu.Address, stu.Phone, stu.ModeOfStudy, 
                dep.DepartmentName, dep.Faculty, dep.DepartmentCode
            from Student stu
            left join Department dep on stu.DepartmentCode = dep.DepartmentCode
            ORDER BY stu.LastName, stu.FirstName;"""
    cur.execute(student_list)
    result = cur.fetchall()
    return result


def get_all_supervisor():
    supervisors_sql = """SELECT CONCAT(stf.FirstName,' ', stf.LastName) as 'Staff Name', stf.DepartmentCode, 
                            stf.Email, dep.DepartmentName, User.Role
                            from Staff stf 
                            JOIN Department dep ON dep.DepartmentCode=stf.DepartmentCode
                            JOIN User on User.Email=stf.Email
                            where User.Role='Supervisor' ORDER BY stf.LastName, stf.FirstName;"""
    cur.execute(supervisors_sql)
    result = cur.fetchall()
    return result


#  get Student Employment history details
def student_emp_history(email):
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


#  get Student scholarship history details
def student_scho_history(email):
    student_scho_history_sql = """Select sr.ScholarshipID, sr.SchoRecordID, sch.Name, sch.Value, sr.StartDate, sr.EndDate, sr.StudentID
                            from Student stu
                            join ScholarshipRecord sr on stu.StudentID = sr.StudentID
                            join Scholarship sch on sr.ScholarshipID = sch.ScholarshipID
                            Where stu.Email = %s
                            order by EndDate DESC;"""
    cur.execute(student_scho_history_sql, (email,))
    result = cur.fetchall()
    return result
    

class StatusBar:
    def __init__(self, reportid=None):
        pass
    def submission_history_desc_list(self, reportid):
        report_submission_history = """select allUser.FirstName,allUser.LastName,allUser.Email,sh.ReportID,sh.Action,sh.SubmitterRole, sh.Date, sh.Time from (
                                        select FirstName,LastName,Email from Staff
                                        Union 
                                        select FirstName,LastName,Email from Student)
                                        as allUser right join SubmissionHistory sh on sh.SubmitterEmail = allUser.Email
                                        where ReportID=%s
                                        order by sh.Date, sh.Time"""
        cur.execute(report_submission_history , (reportid,))
        submission_history = cur.fetchall()
        submission_history_desc_list = []
        current_status = self.report_status(reportid)
        if current_status['Status'] == "Unfinished":
           desciption = "The 6MR report has been created, Please finish your report and submit."
           submission_history_desc_list.append(desciption)
        elif current_status['Status'] == "Rejected":
           desciption = 'The submitted report has been rejected by the Principle Supervisor.Please editting and resubmit according to the feedback you received.'
           submission_history_desc_list.append(desciption)
        index = 0
        try:
            for single_history in submission_history:
                if 'performance' in single_history["Action"]:
                    index=index+1
                    submission_history_desc=f'{single_history["Action"]}({index}/3)  :  {single_history["SubmitterRole"]} ({single_history["FirstName"]} {single_history["LastName"]}) has {single_history["Action"].lower()} on {single_history["Date"]} {single_history["Time"]}'
                else:
                    submission_history_desc=f'{single_history["Action"]}  :  {single_history["SubmitterRole"]} ({single_history["FirstName"]} {single_history["LastName"]}) has {single_history["Action"].lower()} on {single_history["Date"]} {single_history["Time"]}'
                submission_history_desc_list.append(submission_history_desc)
            return submission_history_desc_list
        except Exception:
            return submission_history_desc_list
    def submission_history_index(self, reportid):
        sql  = """select Action from SubmissionHistory
                    where ReportID=%s
                    order by Date,Time"""
        index = 0
        cur.execute(sql , (reportid,))
        submission_history = cur.fetchall()
        if len(submission_history) == 0:
           index = 1
           return index
        elif len(submission_history) == 1:
            index = 2
            return index
        elif 2 <= len(submission_history) <=4:
            index = 3 
            return index
        elif len(submission_history) == 5:
            index = 4 
            return index
        else:
            index = 5
            return index
    def report_status(self,reportid):
        sql  = "select Status from SixMR where ReportID=%s"
        cur.execute(sql , (reportid,))
        report_status = cur.fetchone()
        return report_status
