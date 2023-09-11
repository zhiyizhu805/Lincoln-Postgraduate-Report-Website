import bcrypt
import mysql.connector


import connect

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
    def __init__(self, email=None, password=None):
        self.email = email
        self.password = password

    def find_user_by_email(self, email):
        cur.execute("SELECT * FROM User WHERE Email=%s", (email,))
        result = cur.fetchone()
        return result


    def hashPsw(self, psw):
        # Generate a salt using bcrypt
        salt = bcrypt.gensalt()
        # Encode the password as bytes using utf-8 encoding
        bytes = psw.encode('utf-8')
        # Hash the password using bcrypt and the generated salt
        password_hashed = bcrypt.hashpw(bytes, salt)
        # Return the hashed password
        return password_hashed
    # check userinput with system hashed password

    def check_password(self, psw, hashed_psw):
        # Encode the password to be checked as bytes using utf-8 encoding
        bytes_psw = psw.encode('utf-8')
        bytes_hashed_psw = hashed_psw.encode('utf-8')
        # Check if the given password matches the hashed password using bcrypt
        return bcrypt.checkpw(bytes_psw, bytes_hashed_psw)

    def get_user_info(self, email):
        """Get the user info from the database."""
        cur.execute("SELECT * FROM User WHERE Email = %s", (email,))
        user = cur.fetchone()
        # Get user's full name and combine with email,role and Status
        if user['Role'] == "Student":
            cur.execute(
                "SELECT FirstName, LastName FROM Student WHERE Email = %s", (email,))
            name = cur.fetchone()
            user["FirstName"] = name["FirstName"]
            user["LastName"] = name["LastName"]
        if user['Role'] != "Student":
            cur.execute(
                "SELECT FirstName, LastName FROM Staff WHERE Email = %s", (email,))
            name = cur.fetchone()
            user["FirstName"] = name["FirstName"]
            user["LastName"] = name["LastName"]
        return user
    def change_user_status(self, status,email):
        cur.execute("UPDATE User SET Status = %s WHERE Email = %s",
                    (status, email))

    def change_password(self, email, password):
        """Change the password in the database."""
        # hash password using hashPsw function
        password_hashed = self.hashPsw(password)
        cur.execute("UPDATE User SET PW = %s WHERE Email = %s",
                    (password_hashed, email))
        # Change the status to active after updating password.
        cur.execute(
            "UPDATE User SET Status = 'Active' WHERE Email = %s", (email,))
        
    def creat_new_user(self,Email, PW):
         cur.execute(
            "Insert User (Email, PW, Role, Status) VALUES (%s,%s,'Student','Approval required')", (Email, PW))
    
    def check_if_convenor(self, Email):
        """If they user's role is a supervisor, double check to see if they are a convenor."""
        # Get user's ID
        cur.execute("SELECT StaffID FROM Staff WHERE Email = %s", (Email,))
        staff = cur.fetchone()
        staff_id = staff["StaffID"]
        # Get if it's a convenor
        cur.execute("SELECT * FROM Department WHERE ConvenorID=%s", (staff_id,))
        result = cur.fetchall()
        if result:
            return True
        else:
            return False
        

class Student:
    def __init__(self,studentid=None):
        self.studentid = studentid

        ''' insert new student info'''
    def find_student_by_studentid(self,studentid):
        cur.execute("SELECT * FROM Student WHERE StudentID=%s", (studentid,))
        Student = cur.fetchone()
        return Student
    def find_studentid_by_email(self,email):
        cur.execute("SELECT * FROM Student WHERE Email=%s", (email,))
        Student = cur.fetchone()
        studentID = Student['StudentID']
        return studentID
        
    def register_student(self,StudentID, FirstName, LastName,Address, Phone, Email):
        cur.execute("""insert into Student(StudentID, FirstName, LastName, Address, Phone, Email) 
                    VALUES (%s,%s,%s,%s,%s,%s)""",(StudentID, FirstName, LastName, Address, Phone, Email))
        
    def complete_myprofile_info(self, EnrolmentDate, ModeOfStudy, ThesisTitle, DepartmentCode,StudentID):
        cur.execute("update Student set EnrolmentDate = %s, ModeOfStudy=%s, ThesisTitle=%s, DepartmentCode=%s where StudentID = %s",(EnrolmentDate, ModeOfStudy, ThesisTitle, DepartmentCode,StudentID))
        
    def supervision(self,studentid,principle_supervisor,associate_supervisor1,associate_supervisor2):
        cur.execute("insert into Supervision(StudentID, SupervisorID, SupervisorType) VALUES (%s,%s,%s)",(studentid,principle_supervisor,'Principal Supervisor'))
        cur.execute("insert into Supervision(StudentID, SupervisorID, SupervisorType) VALUES (%s,%s,%s)",(studentid,associate_supervisor1,'Associate Supervisor'))
        cur.execute("insert into Supervision(StudentID, SupervisorID, SupervisorType) VALUES (%s,%s,%s)",(studentid,associate_supervisor2,'Associate Supervisor'))
        

class Scholarship:
    def __init__(self,studentid=None):
        self.studentid = studentid
    def add_scholarship_details(self,scholarships):
            for scholarship in scholarships:
                studentid = scholarship['studentid']
                scholarshipID = scholarship['scholarshipID']
                start_date = scholarship['start_date']
                end_date = scholarship['end_date']
                cur.execute("INSERT INTO ScholarshipRecord (StudentID,ScholarshipID,StartDate, EndDate) VALUES (%s,%s,%s,%s)",(studentid,scholarshipID,start_date,end_date))
    def get_all_scholarship_name(self):
        cur.execute("SELECT ScholarshipID, Name, Value FROM Scholarship;")
        all_scholarship_name = cur.fetchall()
        return all_scholarship_name
        


class Employment:
    def __init__(self,studentid=None):
        self.studentid = studentid
    def add_additional_employment_details(self,employments):
        print('1')
        for employment in employments:
            studentid = employment['studentid']
            supervisorname = employment['supervisorname']
            employmenttype = employment['employmenttype']
            weeklyhours = employment['weeklyhours']
            StartDate = employment['StartDate']
            EndDate = employment['EndDate']
            if EndDate =='':
                EndDate = None
        cur.execute("INSERT INTO Employment (StudentID, SupervisorID, EmploymentTypeID, WeeklyHours,StartDate, EndDate) VALUES (%s,%s,%s,%s,%s,%s)",(studentid,supervisorname,employmenttype,weeklyhours,StartDate, EndDate))
        print('3')

    
class Department:
    def __init__(self):
       pass
    def get_dept_name(self):
        cur.execute("SELECT distinct DepartmentCode, DepartmentName, Faculty, ConvenorID FROM Department order by DepartmentName;")
        Depts = cur.fetchall()
        return Depts
    def get_all_staff_name(self):
        cur.execute("SELECT StaffID,FirstName,LastName FROM Staff order by FirstName;")
        all_staff_name = cur.fetchall()
        return all_staff_name 
    # def get_all_staff_name(self):
    #     cur.execute("SELECT STAFFID,FIRSTNAME,LASTNAME FROM Staff order by FIRSTNAME;")
    #     all_staff_name = cur.fetchall()
    #     staff_list = [(staff["STAFFID"], staff["FIRSTNAME"], staff["LASTNAME"]) for staff in all_staff_name]
    #     return staff_list
