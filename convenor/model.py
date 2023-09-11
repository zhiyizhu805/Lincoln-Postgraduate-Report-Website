   
import mysql.connector

import connect

from flask import redirect, url_for

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
    def __init__(self, email=None, password=None,staff_id=None,period_ending=None,student_id=None):
        self.email = email
        self.password = password
        self.staff_id = staff_id
        self.period_ending = period_ending
        self.student_id = student_id

#sql - get convenor's profile
    def profile_convenor(self, email):
        convenor_sql = """Select CONCAT(stf.FirstName, ' ', stf.LastName) as 'Staff Name', stf.Phone,
                                stf.Email, dep.DepartmentName, dep.Faculty
                            from Staff stf 
                            left join Department dep on stf.DepartmentCode = dep.DepartmentCode
                            where stf.Email = %s;"""
        cur.execute(convenor_sql, (email,))
        result = cur.fetchone()
        return result
    
#sql - edit convenor profile   
    def convenor_profile_edit_process(self, phone, email):
        convenor_edit_sql = """Update Staff Set Phone = %s Where Email = %s;"""
        cur.execute(convenor_edit_sql,(phone, email))
        cur.reset()
        return redirect (url_for("convenor.profile_edit"))

#sql - get list of the students in the convenor's Department
    def my_students(self, email):
        students_sql = """SELECT CONCAT(stu.FirstName,' ', stu.LastName) as 'Student Name',  stu.Email as 'Student Email',
                            stu.ThesisTitle, stu.DepartmentCode, dep.DepartmentName,
                            stf.Email 
                            from Student stu 
                            join Department dep on stu.DepartmentCode = dep.DepartmentCode
                            join Staff stf on dep.ConvenorID = stf.StaffID
                            where stf.Email = %s ORDER BY stu.LastName, stu.FirstName;"""
        cur.execute(students_sql, (email,))
        result = cur.fetchall()
        return result

#sql - obtain Convenor's Department Code
    def department(self, email):
        department_sql = """SELECT stf.DepartmentCode  
                            from Staff stf 
                            where stf.Email = %s;"""
        cur.execute(department_sql, (email,))
        result = cur.fetchone()
        return result
    
#sql - get list of the supervisors in the Convenor's department
    def my_supervisors(self, department_code):
        supervisors_sql = """SELECT CONCAT(stf.FirstName,' ', stf.LastName) as 'Staff Name', stf.DepartmentCode, 
                            stf.Email, dep.DepartmentName, User.Role
                            from Staff stf 
                            JOIN Department dep ON dep.DepartmentCode=stf.DepartmentCode
                            JOIN User on User.Email=stf.Email
                            where User.Role='Supervisor' AND stf.DepartmentCode = %s ORDER BY stf.LastName, stf.FirstName;"""
        cur.execute(supervisors_sql, (department_code,))
        result = cur.fetchall()
        return result
   
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
    
# sql - get list of the convenor's supervisees 
    def my_supervisees(self, email):
        supervisees_sql = """SELECT subq.StudentID, subq.`Student Name`, subq.ThesisTitle, subq.`Student Email`, subq.SupervisorID, subq.Email
        FROM (
        SELECT DISTINCT stu.StudentID, CONCAT(stu.FirstName,' ', stu.LastName) AS 'Student Name', stu.ThesisTitle, stu.Email AS 'Student Email', sup.SupervisorID, stf.Email 
        FROM Student stu 
        JOIN Supervision sup ON stu.StudentID = sup.StudentID
        JOIN Staff stf ON sup.SupervisorID = stf.StaffID
                            where stf.Email = %s)subq
        ORDER BY subq.`Student Name`;"""
        cur.execute(supervisees_sql, (email,))
        result = cur.fetchall()
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
      
# sql - get student 6mr supervisor details.
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
                            Where stu.Email = %s AND sr.EndDate>curdate();"""
        cur.execute(student_scholar, (StudentEmail,))
        result = cur.fetchall()
        return result
    

     # Get all the reports from the convenor's dept in the chosen period in a list.
    def get_convenor_report_list(self, period_ending, staff_id):
        sql = """SELECT s.ReportID AS 'Report ID',s.ReportPeriodEndDate AS 'End Date',s.B_ReportOrder AS 'Report Order',s.StudentID AS 'Student ID', CONCAT(stu.FirstName,' ',stu.LastName) AS 'Student Name',s.Status AS Status
                FROM SixMR AS s
                JOIN Student AS stu
                ON s.StudentID=stu.StudentID
                WHERE stu.DepartmentCode=(SELECT Department.DepartmentCode FROM Department WHERE ConvenorID=%s)
                AND s.Status IN ('Performance rating pending','Final rating pending','Finalised')
                AND s.ReportPeriodEndDate=%s;"""
        cur.execute(sql, (staff_id,period_ending))
        result = cur.fetchall()
        if result:
            # check if this convenor is also the student's supervisor
            for x in result:
                cur.execute("SELECT * FROM Supervision WHERE StudentID=%s AND SupervisorID=%s", (x['Student ID'],staff_id))
                data = cur.fetchone()
                if data:
                    x['IsSupervisor'] = True
                    # Check if the convenor has finished the supervisor assessment.
                    cur.execute("SELECT CompletionDate FROM SupervisorAssessment WHERE ReportID=%s AND SupervisionID=(SELECT SupervisionID FROM Supervision WHERE StudentID=%s AND SupervisorID=%s);", (x['Report ID'],x['Student ID'],staff_id))
                    checkresult = cur.fetchone()
                    if checkresult['CompletionDate'] != None:
                        x['HasAssessed'] = True
                    else:
                        x['HasAssessed'] = False
                else:
                    x['IsSupervisor'] = False
                    x['HasAssessed'] = False
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
        return result
    
    # Get report finaliser(convenor/pg chair) info.
    def get_report_finaliser(self, email):
        sql = """SELECT CONCAT(stf.FirstName,' ',stf.LastName) AS 'FinaliserName', u.Role AS 'FinaliserRole' 
                FROM Staff AS stf 
                JOIN User AS u ON u.Email=stf.Email
                WHERE stf.Email=%s;"""
        cur.execute(sql, (email,))
        result = cur.fetchone()
        return result
    
    def get_final_assessment(self, report_id):
        # Get the section E convenor/PG Chair assessment content.
        cur.execute("""SELECT * FROM SixMR WHERE ReportID=%s;""",(report_id,))
        result = cur.fetchone()
        return result
    
    # get student's email from student_id
    def get_student_email(self, student_id):
        sql = """SELECT Email FROM Student WHERE StudentID=%s;"""
        cur.execute(sql, (student_id,))
        result = cur.fetchone()['Email']
        return result
    
    def get_supervisor_emails(self, student_id):
        sql = """SELECT Email FROM Staff WHERE StaffID IN (SELECT SupervisorID FROM Supervision WHERE StudentID=%s);"""
        cur.execute(sql, (student_id,))
        result = cur.fetchall()
        return result
    

#  get student Employment history details
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


#  get student scholarship history details
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