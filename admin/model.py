import bcrypt
import mysql.connector
from flask import (Flask, flash, make_response, redirect, render_template,
                   request, session, url_for, current_app)
import math
from flask_mail import Mail, Message
import connect
from datetime import date
from contextlib import contextmanager
from student.model import SixMR

# Database connection.
@contextmanager
def getCursor():
    connection = mysql.connector.connect(user=connect.dbuser,
                                         password=connect.dbpass, 
                                         host=connect.dbhost,
                                         database=connect.dbname, 
                                         autocommit=True)
    cursor = connection.cursor(dictionary=True, buffered=True)
    try:
        yield cursor
    finally:
        cursor.close()
        connection.close()


class Student:
    def __init__(self, id=None, fname=None, lname=None, enrolldate=None, address=None, phone=None, email=None, MOS=None, thesis=None, depcode=None):
        self.id = id
        self.fname = fname
        self.lname = lname
        self.enrolldate = enrolldate
        self.address = address
        self.phone = phone
        self.email = email
        self.MOS = MOS
        self.thesis = thesis
        self.depcode = depcode

    def fetch_student(self):
        with getCursor() as cur:
            sql = """select Student.StudentID, CONCAT(Student.FirstName," ",Student.LastName) as name, Student.Email,
            Student.EnrolmentDate, Student.Address, Student.Phone, Student.ModeOfStudy, Student.ThesisTitle, Student.DepartmentCode,
            User.Status from Student
                    inner join User on Student.Email = User.Email
                        order by Student.StudentID;"""
            cur.execute(sql)
            studentList = cur.fetchall()
        return studentList
    
    def fetch_student_id(self, id):
        with getCursor() as cur:
            sql = """select Student.StudentID, CONCAT(Student.FirstName," ",Student.LastName) as name, Student.Email,
            Student.EnrolmentDate, Student.Address, Student.Phone, Student.ModeOfStudy, Student.ThesisTitle, Student.DepartmentCode
            from Student where StudentID = %s;"""
            cur.execute(sql,(id))
            studentDetail = cur.fetchall()
        return studentDetail
    
    def update_student(self, address, phone, MOS, thesis, depcode, id):
        with getCursor() as cur:
            sql = """update Student set Student.Address = %s, Student.Phone = %s, Student.ModeOfStudy = %s, Student.ThesisTitle = %s, Student.DepartmentCode = %s
                where StudentID = %s;"""
            cur.execute(sql,(address, phone, MOS, thesis, depcode, id))


    def insertNew(self, id, fname, lname, address, phone, email):
        with getCursor() as cur:
            sql = """INSERT INTO Student (StudentID,FirstName,LastName,Address,Phone,Email) VALUES (%s, %s, %s, %s,%s, %s);"""
            cur.execute(sql, (id, fname, lname, address,
                        phone, email))

    def student_scholarship(self, id):
        with getCursor() as cur:
            sql = """SELECT sch.Name, sch.Value, sr.StartDate, sr.EndDate
                    FROM ScholarshipRecord AS sr 
                    LEFT JOIN Scholarship AS sch 
                    ON sr.ScholarshipID=sch.ScholarshipID
                    WHERE sr.StudentID=%s ORDER BY EndDate DESC;"""
            cur.execute(sql, (id,))
            result = cur.fetchall()
        return result
    
    
    def student_employment(self, id):
        with getCursor() as cur:
            sql = """SELECT et.EmploymentType, CONCAT(s.FirstName,' ',s.LastName) AS Name, em.WeeklyHours, em.StartDate, em.EndDate
                    FROM Employment AS em
                    LEFT JOIN EmploymentType AS et
                    ON em.EmploymentTypeID=et.EmploymentTypeID
                    LEFT JOIN Staff AS s
                    ON em.SupervisorID=s.StaffID 
                    WHERE em.StudentID=%s ORDER BY StartDate DESC;"""
            cur.execute(sql, (id,))
            result = cur.fetchall()
        return result
    
    def suspend_student(self, id):
        with getCursor() as cur:
            cur.execute("UPDATE User SET Status='Suspended' WHERE Email=(SELECT Email FROM Student WHERE StudentID=%s)", (id,))
            cur.execute("INSERT INTO Suspend_Record (StudentID, SuspendPeriod) VALUES (%s, %s)", (id, date.today()))
    
    def unsuspend_student(self, id):
        with getCursor() as cur:
            cur.execute("UPDATE User SET Status='Active' WHERE Email=(SELECT Email FROM Student WHERE StudentID=%s)", (id,))
            cur.execute("DELETE FROM Suspend_Record WHERE StudentID=%s", (id,))
    

class User:
    def __init__(self, email=None, pwd=None, role=None, status=None):
        self.email = email
        self.pwd = pwd
        self.role = role
        self.status = status

    def updateStatus(self, email):
        with getCursor() as cur:
            sql = """update User set User.Status = %s where User.Email = %s"""
            cur.execute(sql, ('Complete profile', email))

    def rejectUser(self, email):
        with getCursor() as cur:
            sql = """delete from User where User.Email = %s"""
            cur.execute(sql, (email,))

    def insertNew(self, email, pwd, role, status):
        with getCursor() as cur:
            sql = """INSERT INTO User VALUES (%s, %s, %s, %s);"""
            cur.execute(sql, (email, pwd, role, status))

    def hashPwd(self, pwd):
        # Generate a salt using bcrypt
        salt = bcrypt.gensalt()
        # Encode the password as bytes using utf-8 encoding
        bytes = pwd.encode('utf-8')
        # Hash the password using bcrypt and the generated salt
        password_hashed = bcrypt.hashpw(bytes, salt)
        # Return the hashed password
        return password_hashed


class StudentPagination:
    def __int__(self, limit=int, page=int):
        self.limit = limit
        self.page = page

    def createPagination(self, limit, page):
        with getCursor() as cur:
            offset = page*limit - limit
            sql = "select * from Student"
            cur.execute(sql)
            student = cur.fetchall()
            total_row = len(student)
            total_page = math.ceil(total_row/limit)
            next = page + 1
            prev = page - 1
            sql_limit = """select Student.StudentID, CONCAT(Student.FirstName," ",Student.LastName) as name, Student.Email,
            Student.EnrolmentDate, Student.Address, Student.Phone, Student.ModeOfStudy, Student.ThesisTitle, Student.DepartmentCode,
            User.Status from Student
                    inner join User on Student.Email = User.Email
                        order by Student.StudentID limit %s OFFSET %s;"""
            cur.execute(sql_limit, (limit, offset))
            studentList = cur.fetchall()
            paginationBuilder = [total_page, next, prev, studentList]
        return paginationBuilder


class Department:
    def __init__(self, code=None, name=None):
        self.code = code
        self.name = name

    def fetch_dep_list(self):
        with getCursor() as cur:
            sql = """select Department.DepartmentCode, Department.DepartmentName from Department"""
            cur.execute(sql)
            depList = cur.fetchall()
        return depList


class Scholarship:
    def __init__(self, id=None, name=None):
        self.id = id
        self.name = name

    def fetch_sch_list(self):
        with getCursor() as cur:
            sql = """select Scholarship.ScholarshipID, Scholarship.Name from Scholarship"""
            cur.execute(sql)
            schList = cur.fetchall()
        return schList


class ScholarshipRecored:
    def __init__(self, r_id=None, student_id=None, sch_id=None, tenure=None, endDate=None):
        self.r_id = r_id
        self.student_id = student_id
        self.sch_id = sch_id
        self.tenure = tenure
        self.endDate = endDate

    def insertNew(self, student_id, sch_id, tenure, endDate):
        with getCursor() as cur:
            sql = """INSERT INTO ScholarshipRecord (StudentID, ScholarshipID, Tenure, EndDate)
                        VALUES (%s, %s, %s, %s);;"""
        cur.execute(sql, (student_id, sch_id, tenure, endDate))


class EmailSender:
    def __init__(self, email=None, msgContent=None):
        self.email = email
        self.msgContent = msgContent

    def sendEmail(self, email, msgContent):
        current_app.config['MAIL_SERVER'] = "smtp.gmail.com"
        current_app.config['MAIL_PORT'] = 465
        current_app.config['MAIL_USERNAME'] = "system.lupgms.lincoln@gmail.com"
        current_app.config['MAIL_PASSWORD'] = "ibqrfvzclnoksvsm"
        current_app.config['MAIL_USE_TLS'] = False
        current_app.config['MAIL_USE_SSL'] = True
        mail = Mail(current_app)
        recip = [email]
        msg = Message("Message from Lincoln University Postgraduate Monitoring System", sender="test@lincoln.com", recipients=recip)
        msg.body = msgContent
        mail.send(msg)


class Staff:
    def __init__(self, id=None):
        self.id = id

    def fetchStaff(self):
        with getCursor() as cur:
            sql = """select Staff.StaffID, CONCAT(Staff.FirstName,' ', Staff.LastName)as name from Staff"""
            cur.execute(sql)
            staffList = cur.fetchall()
        return staffList
    
    def update_staff(self, phone, depcode, id):
        with getCursor() as cur:
            sql = """update Staff set Staff.Phone = %s, Staff.DepartmentCode = %s
                where StaffID = %s;"""
            cur.execute(sql,(phone, depcode, id))


class EmploymentRecord:
    def __init__(self, r_id=None, student_id=None, staff_id=None, empType=None, weeklyHours=None):
        self.r_id = r_id
        self.student_id = student_id
        self.staff_id = staff_id
        self.empType = empType
        self.weeklyHours = weeklyHours

    def insertNew(self, student_id, staff_id, empType, weeklyHours):
        with getCursor() as cur:
            sql = """INSERT INTO Employment (StudentID, SupervisorID, EmploymentType, WeeklyHours)
                        VALUES (%s, %s, %s, %s);;"""
            cur.execute(sql, (student_id, staff_id, empType, weeklyHours))


class Report:
    def __init__(self, report_id=None, student_id=None, role=None, dep=None, period=None, repStatus=None, clauseStr=None, studentName=None):
        self.report_id = report_id
        self.student_id = student_id
        self.role = role
        self.dep = dep
        self.period = period
        self.repStatus = repStatus
        self.clauseStr = clauseStr
        self.studentName = studentName

    def fetchReportFiltered(self, clauseStr):
        with getCursor() as cur:
            sql = f"""select Student.StudentID,Student.Email, Student.DepartmentCode, CONCAT(Student.FirstName," ",Student.LastName) as name,
                SixMR.ReportID, SixMR.ReportPeriodEndDate,SixMR.Status, SixMR.B_ReportOrder 
                    from Student left join SixMR on SixMR.StudentID=Student.StudentID 
                    inner join User on Student.Email=User.Email where User.Role='Student' and User.Status='Active' and 
                    {clauseStr}              
                    """

            cur.execute(sql)
            reports = cur.fetchall()
        return reports

    def getCurrentReportOrder(self):
        monthOfToday = date.today().month
        yearOfToday = date.today().year
        currentPeriod = ""
        if monthOfToday <= 6:
            currentPeriod = f"{yearOfToday}-06-30"
        else:
            currentPeriod = f"{yearOfToday}-12-31" 
        
        with getCursor() as cur:
            sql = """SELECT DATEDIFF(%s, Student.EnrolmentDate) as days from Student"""
            cur.execute(sql,(currentPeriod,))
            dbResult = cur.fetchone()
            days = dbResult['days']
            reportOrder = round(days/182.5)
            dbObj = {
                "currentPeriod":currentPeriod,
                "reportOrder" : reportOrder,
            }
        return dbObj
    
    def fetchexistedReportNum(self,student_id):
        with getCursor() as cur:
            sqlExistedReport = """select COUNT(SixMR.StudentID) as reportNum from SixMR where SixMR.StudentID=%s"""
            cur.execute(sqlExistedReport, (student_id,))
            dbResultExistedReport = cur.fetchone()
            existedReportNum =  dbResultExistedReport['reportNum']
        return existedReportNum

    def fetchStudentHelper(self):
        with getCursor() as cur:
            sql = """select Student.StudentID, Student.Email, CONCAT(Student.FirstName," ",Student.LastName) as name, Student.DepartmentCode from Student
                        inner join User on Student.Email=User.Email where User.Role='Student' and User.Status='Active'"""
            cur.execute(sql)
            dbResult = cur.fetchall()
        return dbResult

    def fetchReportFullList(self):
        with getCursor() as cur:
            sql = """select Student.StudentID,Student.Email, Student.DepartmentCode, CONCAT(Student.FirstName," ",Student.LastName) as name,
                SixMR.ReportID, SixMR.ReportPeriodEndDate,SixMR.Status, SixMR.B_ReportOrder 
                    from Student left join SixMR on SixMR.StudentID=Student.StudentID 
                    inner join User on Student.Email=User.Email where User.Role='Student' and User.Status='Active'            
                    """
            cur.execute(sql)
            reports = cur.fetchall()
        return reports

    def fetchReportStatus(self, report_id):
        with getCursor() as cur:
            sql = """select SubmissionHistory.SubmissionID, SubmissionHistory.SubmitterEmail, SubmissionHistory.SubmitterRole, SubmissionHistory.Date,  SubmissionHistory.Time 
                    from SubmissionHistory where ReportID=%s order by SubmissionHistory.Time"""
            cur.execute(sql, (report_id,))
            results = cur.fetchall()
        return results

    def fetchReportID(self):
        with getCursor() as cur:
            sql = """select SixMR.ReportID from SixMR"""
            cur.execute(sql)
            reportId = cur.fetchall()
        return reportId

    def fetchStudent(self, report_id):
        with getCursor() as cur:
            sql = """select SixMR.StudentID, Student.Email, CONCAT(Student.FirstName," ",Student.LastName) as name from SixMR 
            inner join Student on SixMR.StudentID = Student.StudentID 
            where ReportID=%s"""
            cur.execute(sql, (report_id,))
            student = cur.fetchone()
        return student

    def fetchSubmittedTime(self, report_id, role):
        with getCursor() as cur:
            sql = """select SubmissionHistory.Date,SubmissionHistory.Time from SubmissionHistory
                where ReportID=%s and SubmitterRole=%s """
            cur.execute(sql, (report_id, role))
            submittedTime = cur.fetchall()
        return submittedTime

    def fetchSubmittedReportId(self):
        with getCursor() as cur:
            sql = """select SubmissionHistory.ReportID from SubmissionHistory"""
            cur.execute(sql)
            result = cur.fetchall()
            submittedReportId = []
            for data in result:
                submittedReportId.append(data['ReportID'])
        return submittedReportId

    def fetchEmailList(self, report_id):
        with getCursor() as cur:
            sql = """select SubmissionHistory.SubmitterEmail from SubmissionHistory
                        where SubmissionHistory.ReportID=%s"""
            cur.execute(sql, (report_id,))
            result = cur.fetchall()
            emailList = []
            for data in result:
                emailList.append(data['SubmitterEmail'])
        return emailList
    def fetchSixmrStatus(self, report_id):
        with getCursor() as cur:
            sql = """select SixMR.Status from SixMR where ReportID=%s"""
            cur.execute(sql,(report_id,))
            dbResult = cur.fetchone()
            sixmrStatus = dbResult['Status']
        return sixmrStatus
    def fetchReportFinalRole(self, student_id):
        with getCursor() as cur:
            sqlSup = """select Supervision.SupervisorID from Supervision where Supervision.StudentID=%s """
            cur.execute(sqlSup,(student_id,))
            dbSup = cur.fetchall()
            supIdList = []
            for db in dbSup:
                supIdList.append(db['SupervisorID'])
            sqlCon = """select Department.ConvenorID from Department"""
            cur.execute(sqlCon)
            dbCon = cur.fetchall()
            conIdList = []
            for db in dbCon:
                conIdList.append(db['ConvenorID'])
            finalRole = 'Convenor'
            for supId in supIdList:
                if conIdList.count(supId) > 0:
                    finalRole = 'PG Chair'
        return finalRole
    def fetchSupspendedStuId(self):
        with getCursor() as cur:
            sql = """select Suspend_Record.StudentID from Suspend_Record"""
            cur.execute(sql)
            dbResult = cur.fetchall()
            suspendedStuId = []
            for db in dbResult:
                suspendedStuId.append(db['StudentID'])
        return suspendedStuId

class PGChair:
    def __init__(self) -> None:
        pass
    def fetchPGChairDetail(self):
        with getCursor() as cur:
            sql = """SELECT CONCAT(Staff.FirstName, ' ', Staff.LastName) as pgcName, Staff.Email FROM Staff
                inner join User on User.Email = Staff.Email where User.Role='PG Chair';"""   
            cur.execute(sql)
            dbResult = cur.fetchall()
            pgChair = dbResult[0]
        return pgChair
    
    def pgChairList(self):
        with getCursor() as cur:
            sql = """select Staff.StaffID, CONCAT(Staff.FirstName, ' ', Staff.LastName) as 'Staff Name',
                    Staff.Email,  Staff.Phone, Staff.DepartmentCode
                    from Staff
                    join User on Staff.Email = User.Email
                    where User.role = 'PG Chair';"""
            cur.execute(sql)
            pgChairList = cur.fetchall()
        return pgChairList

class Supervisor:
    def __init__(self, studentId=None, email=None):
        self.studentId = studentId
        self.email = email
    def fetchEmailList(self, studentId):
        with getCursor() as cur:
            sql = """select Supervision.SupervisorID, Supervision.SupervisorType,CONCAT(Staff.FirstName,' ', Staff.LastName)as supervisorName, Staff.Email
                    from Supervision inner join Staff on Supervision.SupervisorID = Staff.StaffID
                    where Supervision.StudentID = %s"""
            cur.execute(sql, (studentId,))
            result = cur.fetchall()
            emailList = []
            for data in result:
                emailList.append(data['Email'])
        return emailList

    def fetchSupList(self, studentId):
        with getCursor() as cur:
            sql = """select Supervision.SupervisorID, Supervision.SupervisorType,CONCAT(Staff.FirstName,' ', Staff.LastName)as supervisorName, Staff.Email
                    from Supervision inner join Staff on Supervision.SupervisorID = Staff.StaffID
                    where Supervision.StudentID = %s"""
            cur.execute(sql, (studentId,))
            supervisors = cur.fetchall()
        return supervisors

    def fetchSupName(self, email):
        with getCursor() as cur:
            sql = """select CONCAT(Staff.FirstName,' ', Staff.LastName)as supervisorName from Staff where Staff.Email=%s"""
            cur.execute(sql,(email,))
            dbResult = cur.fetchone()
            supName = dbResult['supervisorName']
        return supName
    
    def supervisorList(self):
        with getCursor() as cur:
            sql = """select Staff.StaffID, CONCAT(Staff.FirstName, ' ', Staff.LastName) as 'Staff Name',
                    Staff.Email,  Staff.Phone, Staff.DepartmentCode
                    from Staff
                    join User on Staff.Email = User.Email
                    where User.role = 'Supervisor';"""
            cur.execute(sql)
            supervisorList = cur.fetchall()
        return supervisorList

class Convenor:
    def __init__(self, studentId=None):
        self.studentId = studentId

    def fetchConvenor(self, studentId):
        with getCursor() as cur:
            sql = """select Student.StudentID, CONCAT(Staff.FirstName,' ', Staff.LastName)as convenorName, Staff.Email from Student
                    inner join Department on Student.DepartmentCode=Department.DepartmentCode
                    inner join Staff on Staff.StaffID = Department.ConvenorID
                    where Student.StudentID=%s"""
            cur.execute(sql, (studentId,))
            convenor = cur.fetchone()
        return convenor

    def convenorList(self):
        with getCursor() as cur:
            sql = """select Staff.StaffID, CONCAT(Staff.FirstName, ' ', Staff.LastName) as 'Staff Name',
                    Staff.Email,  Staff.Phone, Staff.DepartmentCode
                    from Staff
                    join User on Staff.Email = User.Email
                    where User.role = 'Convenor';"""
            cur.execute(sql)
            convenorList = cur.fetchall()
        return convenorList
    
class EmailSenderToMany:
    def __init__(self, email=None, msgContent=None):
        self.email = email
        self.msgContent = msgContent

    def sendEmail(self, email, msgContent):
        current_app.config['MAIL_SERVER'] = "smtp.gmail.com"
        current_app.config['MAIL_PORT'] = 465
        current_app.config['MAIL_USERNAME'] = "system.lupgms.lincoln@gmail.com"
        current_app.config['MAIL_PASSWORD'] = "ibqrfvzclnoksvsm"
        current_app.config['MAIL_USE_TLS'] = False
        current_app.config['MAIL_USE_SSL'] = True
        mail = Mail(current_app)
        recip = email
        msg = Message("Message from Lincoln University Postgraduate Monitoring System", sender="test@lincoln.com", recipients=recip)
        msg.body = msgContent
        mail.send(msg)


class AnalysisReportData:
    def __init__(self, depCode=None, reportPeriod=None, result=None, clauseStr=None, dep=None, criterionId=None, studentId=None, reportId=None, supervisionId=None, assResult=None):
        self.depCode = depCode
        self.reportPeriod = reportPeriod
        self.result = result
        self.clauseStr = clauseStr
        self.criterionId = criterionId
        self.studentId=studentId
        self.supervisionId = supervisionId
        self.reportId = reportId
        self.assResult = assResult
    def fetchStudentNumWithDepCode(self, depcode):
        with getCursor() as cur:
            sql = """select COUNT(*) AS stuNumber from Student 
                        inner join User on User.Email = Student.Email
                        where User.Role = 'Student' and User.Status = 'Active' 
                        and DepartmentCode=%s"""
            cur.execute(sql, (depcode,))
            result = cur.fetchone()
            number = result['stuNumber']
        return number

    def fetchReportNum(self, depcode, reportPeriod):
        with getCursor() as cur:
            sql = """select COUNT(*) AS repNumber from Student 
                    inner join SixMR on Student.StudentID = SixMR.StudentID 
                    where Student.DepartmentCode=%s and SixMR.Status = 'Finalised' and SixMR.ReportPeriodEndDate = %s """
            cur.execute(sql, (depcode, reportPeriod))
            result = cur.fetchone()
            number = result['repNumber']
        return number

    def fetchCriterionList(self):
        with getCursor() as cur:
            sql = """select * from EvaluationCriterion"""
            cur.execute(sql)
            result = cur.fetchall()
            criterionList = []
            dblength = len(result)
            for index, data in enumerate(result):
                if index != dblength-1:
                    criterionList.append(data)
        return criterionList

    def fetchFacultyPerformanceOverAllCurrent(self):
        with getCursor() as cur:
            facultyPerformanceOverAllCurrent = {}
            sqlVeryGood = """select COUNT(C_Table.CriterionID) as veryGoodNum  from C_Table
            inner join SixMR on SixMR.ReportID = C_Table.ReportID
            where  SixMR.ReportPeriodEndDate = '2023-06-30' and C_Table.Result='Very Good'"""
            cur.execute(sqlVeryGood)
            resultVeryGood = cur.fetchone()
            veryGoodNum = resultVeryGood['veryGoodNum']

            sqlGood = """select COUNT(C_Table.CriterionID) as goodNum  from C_Table
            inner join SixMR on SixMR.ReportID = C_Table.ReportID
            where  SixMR.ReportPeriodEndDate = '2023-06-30' and C_Table.Result='Good'"""
            cur.execute(sqlGood)
            resultGood = cur.fetchone()
            goodNum = resultGood['goodNum']

            sqlSatisfactory = """select COUNT(C_Table.CriterionID) as satisfactoryNum  from C_Table
            inner join SixMR on SixMR.ReportID = C_Table.ReportID
            where  SixMR.ReportPeriodEndDate = '2023-06-30' and C_Table.Result='Satisfactory'"""
            cur.execute(sqlSatisfactory)
            resultSatisfactory = cur.fetchone()
            satisfactoryNum = resultSatisfactory['satisfactoryNum']

            sqlUnsatisfactor = """select COUNT(C_Table.CriterionID) as unsatisfactorNum  from C_Table
            inner join SixMR on SixMR.ReportID = C_Table.ReportID
            where  SixMR.ReportPeriodEndDate = '2023-06-30' and C_Table.Result='Unsatisfactory'"""
            cur.execute(sqlUnsatisfactor)
            resultUnsatisfactor = cur.fetchone()
            unsatisfactorNum = resultUnsatisfactor['unsatisfactorNum']

            sqlNotRelevant = """select COUNT(C_Table.CriterionID) as notRelevantNum  from C_Table
            inner join SixMR on SixMR.ReportID = C_Table.ReportID
            where  SixMR.ReportPeriodEndDate = '2023-06-30' and C_Table.Result='Not Relevant'"""
            cur.execute(sqlNotRelevant)
            resultNotRelevant = cur.fetchone()
            notRelevantNum = resultNotRelevant['notRelevantNum']

            facultyPerformanceOverAllCurrent = {
                'veryGoodNum': veryGoodNum,
                'goodNum': goodNum,
                'satisfactoryNum': satisfactoryNum,
                'unsatisfactorNum': unsatisfactorNum,
                'notRelevantNum': notRelevantNum,
            }
        return facultyPerformanceOverAllCurrent

    def fetchStudentNum(self):
        with getCursor() as cur:
            sql = """select COUNT(*) AS stuNumber from Student 
                        inner join User on User.Email = Student.Email
                        where User.Role = 'Student' and User.Status = 'Active'
                        """
            cur.execute(sql)
            result = cur.fetchone()
            studentNum = result['stuNumber']
        return studentNum

    def fetchReportNumCurrent(self):
        with getCursor() as cur:
            sql = """select COUNT(*) as reportNumCurrent from SixMR            
            where  SixMR.ReportPeriodEndDate = '2023-06-30' and SixMR.Status  = 'Finalised'"""
            cur.execute(sql)
            result = cur.fetchone()
            reportNumCurrent = result['reportNumCurrent']
        return reportNumCurrent

    def fetchFacultyPerformanceFiltered(self, result, clauseStr):
        with getCursor() as cur:
            sql = f"""select COUNT(C_Table.CriterionID) as countedNum  from C_Table
            inner join SixMR on SixMR.ReportID = C_Table.ReportID
            inner join Student on Student.StudentID = SixMR.StudentID
            where C_Table.Result='{result}' && {clauseStr}"""
            cur.execute(sql)
            result = cur.fetchone()
            countedNum = result['countedNum']
        return countedNum

    def countSuspendedStudentWithPeriod(self,depCode,reportPeriod ):
        with getCursor() as cur:
            sql = """SELECT COUNT(Suspend_Record.StudentID) AS suspendeStuNum FROM Suspend_Record 
                inner join Student on Student.StudentID = Suspend_Record.StudentID 
                where Student.DepartmentCode=%s and Suspend_Record.SuspendPeriod=%s ;"""
            cur.execute(sql,(depCode,reportPeriod))
            dbResult = cur.fetchone()
            suspendeStuNum = dbResult['suspendeStuNum']
        return suspendeStuNum

    def fetchReportNumFiltered(self, reportPeriod, depCode):
        with getCursor() as cur:
            sql = """select COUNT(*) as reportNum from SixMR 
                    inner join Student on Student.StudentID = SixMR.StudentID
            where  SixMR.ReportPeriodEndDate = %s and Student.DepartmentCode = %s  and SixMR.Status  = 'Finalised'"""
            cur.execute(sql, (reportPeriod, depCode))
            result = cur.fetchone()
            reportNum = result['reportNum']
        return reportNum

    def fetchReportNumFilteredPeriod(self, reportPeriod):
        with getCursor() as cur:
            sql = """select COUNT(SubmissionHistory.ReportID) as reportNum from SubmissionHistory
                    inner join SixMR on SixMR.ReportID = SubmissionHistory.ReportID
                    inner join Student on Student.StudentID = SixMR.StudentID
            where  SixMR.ReportPeriodEndDate = %s   and SubmissionHistory.SubmitterRole = 'Student'"""
            cur.execute(sql, (reportPeriod,))
            result = cur.fetchone()
            reportNum = result['reportNum']
        return reportNum

    def fetchFacultyPerformanceOverPeriod(self, reportPeriod, result):
        with getCursor() as cur:
            sql = """select COUNT(C_Table.CriterionID) as countedNum  from C_Table
            inner join SixMR on SixMR.ReportID = C_Table.ReportID
            where  SixMR.ReportPeriodEndDate = %s and C_Table.Result=%s"""
            cur.execute(sql, (reportPeriod, result))
            dbResult = cur.fetchone()
            countedNum = dbResult['countedNum']
        return countedNum

    def fetchCriterion(self, criterionId):
        with getCursor() as cur:
            sql = """SELECT * FROM EvaluationCriterion where CriterionID=%s"""
            cur.execute(sql,(criterionId,))
            dbResult = cur.fetchone()
            criterion = dbResult['Criterion']
        return criterion 
    def fetchStudentList(self):
        with getCursor() as cur:
            sqlStu = """select Student.StudentID, Student.Email, CONCAT(Student.FirstName," ",Student.LastName) as name, Student.DepartmentCode from Student
                        inner join User on Student.Email=User.Email where User.Role='Student' and User.Status='Active'"""
            cur.execute(sqlStu)
            dbStu = cur.fetchall()
        return dbStu
    def fetchSupList(self, studentId):
        with getCursor() as cur:
            sqlSup = """select Supervision.SupervisorType, CONCAT(Staff.FirstName,' ', Staff.LastName) as SupName 
                from Student
                inner join User on Student.Email = User.Email
                inner join Supervision on Student.StudentID = Supervision.StudentID
                inner join Staff on Staff.StaffID = Supervision.SupervisorID
                where User.Role = 'Student' and User.Status = 'Active' and Student.StudentID= %s;"""
            cur.execute(sqlSup, (studentId,))
            dbSup = cur.fetchall()
            supList = []
            for sup in dbSup:
                supList.append(
                sup['SupName']
                )
        return supList
    def fetchReportRating(self,studentId):
        with getCursor() as cur:
            sql="""select SixMR.ReportPeriodEndDate, SixMR.E_ConvenorRating from SixMR
            where SixMR.StudentID = %s and SixMR.Status = 'Finalised' 
            order by SixMR.ReportPeriodEndDate"""
            cur.execute(sql,(studentId,))
            dbResult = cur.fetchall()
            ratingLsit = []
            
            for db in dbResult:
                ratingLsit.append({
                    str(db['ReportPeriodEndDate']): db['E_ConvenorRating'],
                })
        return ratingLsit
    def fetchReportPeriodList(self,studentId):
        with getCursor() as cur:
            sql="""select SixMR.ReportPeriodEndDate, SixMR.E_ConvenorRating from SixMR
            where SixMR.StudentID = %s and SixMR.Status = 'Finalised' 
            order by SixMR.ReportPeriodEndDate"""
            cur.execute(sql,(studentId,))
            dbResult = cur.fetchall()
            periodLsit = []
            for db in dbResult:
                periodLsit.append(
                    str(db['ReportPeriodEndDate']),
                )
        return periodLsit
    def checkIfStudentSuspended(self,studentId,reportPeriod):
        with getCursor() as cur:
            sql = """SELECT * FROM Suspend_Record where Suspend_Record.StudentID=%s and Suspend_Record.SuspendPeriod=%s order by Suspend_Record.SuspendPeriod"""
            cur.execute(sql, (studentId,reportPeriod))
            dbResult = cur.fetchall()
            if len(dbResult) == 0:
                studentIsSuspended = False
            else:
                studentIsSuspended = True
        return studentIsSuspended
    def fetchIndividulReportId(self,studentId,reportPeriod):
        with getCursor() as cur:
            sql = """select SixMR.ReportID from SixMR where SixMR.StudentID=%s and SixMR.ReportPeriodEndDate=%s and SixMR.Status='Finalised'"""
            cur.execute(sql,(studentId,reportPeriod))
            dbResult = cur.fetchone()
            if dbResult:
                reportId = dbResult['ReportID']
            else:
                reportId = None
        return reportId
    def fetchSupervisionIDList(self,studentId):
        with getCursor() as cur:
            sql = """select Supervision.SupervisionID from Supervision where Supervision.StudentID = %s"""
            cur.execute(sql,(studentId,))
            dbResult = cur.fetchall()
            supervisionIDList = []
            for db in dbResult:
                supervisionIDList.append(db['SupervisionID'])
        return supervisionIDList
    def fetchReportResult(self,reportId, supervisionId, assResult):
        with getCursor() as cur:
            sql = """select COUNT(E_Table.AssessmentID) as resultNum from E_Table
                left join SupervisorAssessment on SupervisorAssessment.AssessmentID = E_Table.AssessmentID
                where SupervisorAssessment.ReportID=%s and SupervisorAssessment.SupervisionID = %s and E_Table.Result=%s;"""
            cur.execute(sql,(reportId, supervisionId, assResult))
            dbResult = cur.fetchone()
            resultNum = dbResult['resultNum']
        return resultNum
class SixMRModule:
    def __init__(self, student_id=None, report_id=None, sixmr_instance=None):
        self.student_id = student_id
        self.report_id = report_id
        self.sixmr_instance = SixMR()

    def view_6mr_report(self, student_id, report_id):
        with getCursor() as cur:
            ####### SECTION A ########
            # Get Reporting Period End Date.
            period_ending = self.sixmr_instance.get_period_ending(report_id)['ReportPeriodEndDate']
            # Get Student profile for Section A other than Scholarship and employment.
            cur.execute("SELECT Email FROM Student WHERE StudentID=%s;", (student_id,))
            email = cur.fetchone()['Email']
            student_profile = self.sixmr_instance.student_profile(email)
            # Get Supervision information.
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
            
        return render_template('viewReport.html',period_ending=period_ending,
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