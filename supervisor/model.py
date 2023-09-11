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
    def __init__(self, email=None, password=None, staff_id=None, period_ending=None):
        self.email = email
        self.password = password
        self.staff_id = staff_id
        self.period_ending = period_ending

    # sql - get staff profile
    def profile_staff(self, email):
        staffinfo_sql = """Select stf.StaffID, CONCAT(stf.FirstName, ' ', stf.LastName) as 'Staff Name', stf.Phone,
                                stf.Email, dep.DepartmentName, dep.Faculty
                            from Staff stf 
                            LEFT JOIN Department dep on stf.DepartmentCode = dep.DepartmentCode
                            where stf.Email = %s;"""
        cur.execute(staffinfo_sql, (email,))
        result = cur.fetchall()[0]
        cur.reset()
        return result
    

    #sql - edit staff profile
    def profile_staff_edit_process(self, phone, email):
        staffinfoedit_sql = """Update Staff Set Phone = %s Where Email = %s;"""
        cur.execute(staffinfoedit_sql,(phone, email))

    

    # sql - get list of the supervisor's supervisees
    def my_supervisees(self, email):
        supervisees_sql = """SELECT subq.StudentID, subq.`Student Name`, subq.ThesisTitle, subq.`Student Email`, subq.SupervisorID, subq.Email
        FROM (
        SELECT DISTINCT stu.StudentID, CONCAT(stu.FirstName,' ', stu.LastName) AS 'Student Name', stu.ThesisTitle, stu.Email AS 'Student Email', sup.SupervisorID, stf.Email 
        FROM Student stu 
        JOIN Supervision sup ON stu.StudentID = sup.StudentID
        JOIN Staff stf ON sup.SupervisorID = stf.StaffID
                            where stf.Email = %s)subq
        ORDER BY subq.`Student Name` DESC;"""
        cur.execute(supervisees_sql, (email,))
        result = cur.fetchall()
        return result    
                       
    # sql - get supervisee's details for their profile 
    def profile_supervisee(self, StudentEmail):
        superviseeinfo_sql = """Select st.StudentID, CONCAT(st.FirstName,' ', st.LastName) as 'Student Name', st.EnrolmentDate, st.Address, st.Phone, 
                            st.Email, st.ModeOfStudy, st.ThesisTitle
                            from Student st
                            LEFT JOIN Department dep on st.DepartmentCode = dep.DepartmentCode
                            where st.Email = %s;"""
        cur.execute(superviseeinfo_sql, (StudentEmail,))
        result = cur.fetchone()
        return result
    
    # sql - get supervisee's current Employment details
    def student_emp(self, StudentEmail):
        student_emo_sql = """select emp.EmploymentID, CONCAT(stf.FirstName,  ' ', stf.LastName) as 'Supervisor Name', emp.SupervisorID, 
                                empt.EmploymentType, emp.WeeklyHours, emp.StartDate, emp.EndDate, emp.StudentID
                                from Student stu
                                LEFT JOIN Employment emp on stu.StudentID = emp.StudentID
                                LEFT JOIN EmploymentType empt on empt.EmploymentTypeID = emp.EmploymentTypeID
                                LEFT JOIN Staff stf on emp.SupervisorID = stf.StaffID
                                Where stu.Email = %s AND emp.EndDate IS NULL;"""
        cur.execute(student_emo_sql, (StudentEmail,))
        result = cur.fetchall()
        return result
      
    # sql - get Student 6mr supervisor details.
    def student_sup(self, StudentEmail):
        student_sup_sql = """select CONCAT(stf.FirstName,  ' ', stf.LastName) as 'Supervisor Name',
                                sup.SupervisorType
                                from Student stu
                                LEFT JOIN Supervision sup on stu.StudentID = sup.StudentID
                                LEFT JOIN Staff stf on sup.SupervisorID = stf.StaffID
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
    
    # sql - get all Student list
    def view_student(self):
        student_list = """select stu.StudentID, CONCAT(stu.FirstName, ' ', stu.LastName) as 'FullName', smr.ReportID
                            from 
                            Student stu
                            LEFT JOIN SixMR smr
                            on stu.StudentID = smr.StudentID"""
        cur.execute(student_list)
        result = cur.fetchall()
        return result
    
    # Get a list of the reports submitted to the supervisor in a selected period.
    def get_supervisor_report_list(self, period_ending, staff_id):
        # first, get this supervisor's supervisees report detail in the selected period.
        sql = """SELECT six.ReportID AS 'Report ID',six.ReportPeriodEndDate AS 'End Date',six.B_ReportOrder AS 'Report Order',six.StudentID AS 'Student ID',CONCAT(stu.FirstName,' ',stu.LastName) AS 'Student Name',six.Status 
                FROM SixMR AS six JOIN Student AS stu 
                ON six.StudentID=stu.StudentID 
                WHERE six.StudentID IN (SELECT sup.StudentID FROM Supervision AS sup WHERE sup.SupervisorID=%s) 
                AND ReportPeriodEndDate=%s 
                AND six.Status NOT IN ('Unfinished','Rejected');"""
        cur.execute(sql, (staff_id,period_ending,))
        result = cur.fetchall()
        if result:
            for x in result:
                # Get the supervisor type to each Student and if the supervisor has completed the Student assessment.
                cur.execute("""SELECT SupervisorType,SupervisionID FROM Supervision WHERE StudentID=%s AND SupervisorID=%s;""", (x['Student ID'],staff_id,))
                sup_type = cur.fetchone()
                x['SupervisorType'] = sup_type['SupervisorType']
                cur.execute("""SELECT CompletionDate FROM SupervisorAssessment WHERE ReportID=%s AND SupervisionID=%s;""", (x['Report ID'],sup_type['SupervisionID'],))
                completion_date = cur.fetchone()['CompletionDate']
                x['CompletionDate'] = completion_date
        # Get the percentage of supervisor assessment completion for each report.
        if result:
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


#  get Student Employment history details
def student_emp_history(email):
    student_emo_history_sql = """select emp.EmploymentID, CONCAT(stf.FirstName,  ' ', stf.LastName) as 'Supervisor Name', emp.SupervisorID, 
                                empt.EmploymentType, emp.WeeklyHours, emp.StartDate, emp.EndDate, emp.StudentID
                                from Student stu
                                LEFT JOIN Employment emp on stu.StudentID = emp.StudentID
                                LEFT JOIN EmploymentType empt on empt.EmploymentTypeID = emp.EmploymentTypeID
                                LEFT JOIN Staff stf on emp.SupervisorID = stf.StaffID
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