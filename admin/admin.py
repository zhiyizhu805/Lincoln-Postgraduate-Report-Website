from flask import Blueprint, request, render_template, redirect, url_for, flash, session, current_app
import bcrypt
from collections import Counter
from datetime import datetime,date
from flask_mail import Mail, Message
from admin.model import Student, User, StudentPagination, Department, Scholarship,  ScholarshipRecored, EmailSender, Staff, EmploymentRecord, Report, Supervisor, Convenor, EmailSenderToMany, AnalysisReportData, PGChair, SixMRModule
# create admin blue print, use its own children templates and define route pattern
admin = Blueprint('admin', __name__,
                  template_folder='templates', url_prefix='/admin')


# create instance from model class
student = Student()
user = User()
pagination = StudentPagination()
department = Department()
scholarship = Scholarship()
schRecord = ScholarshipRecored()
emailSender = EmailSender()
staff = Staff()
employment = EmploymentRecord()
report = Report()
supervisor = Supervisor()
convenor = Convenor()
emailSenderToMany = EmailSenderToMany()
analysisReportData = AnalysisReportData()
PGChair = PGChair()
sixMRModule = SixMRModule()
@admin.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            return render_template('dashboard.html')
    else:
        return render_template('accessDenied.html')

# rendering list of students and their status


@admin.route('/students', defaults={'page': 1})
@admin.route('/students/page/<int:page>')
def students(page):
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            # rendering studentlist with page limit, modify limit(students number) as you wish
            pageResults = pagination.createPagination(limit=10, page=page)
            studentList = pageResults[3]
            totalPages = pageResults[0]
            prev = pageResults[2]
            next = pageResults[1]
            depList = Department.fetch_dep_list(session['username'])
            return render_template('students.html', studentList=studentList, totalPages=totalPages, prev=prev, next=next, page=page, depList=depList)
    else:
        return render_template('accessDenied.html')


@admin.route('/admin/approveStudent', methods=["POST"])
@admin.route('/approveStudent', methods=["POST"])
def approveStudent():
    email = request.form.get("email")
    name = request.form.get("name")
    user.updateStatus(email)
    emailSender.sendEmail(email, f"Kia ora {name},\n\nwe are happy to advise your application to register with Lincoln University's Postgraduate Monitoring System has been approved.\n\nRegards,\n\nLUPGMS")
    return redirect(url_for('admin.students'))


@admin.route('/admin/rejectStudent', methods=["POST"])
@admin.route('/rejectStudent', methods=["POST"])
def rejectStudent():
    email = request.form.get("email")
    name = request.form.get("name")
    user.rejectUser(email)
    emailSender.sendEmail(
        email, f"Kia ora {name},\n\nUnfortunately your request to register with Lincoln University's Postgraduate Monitoring System has been rejected as the details you provided did not match our records.\n\nRegards,\n\nLUPGMS")
    return redirect(url_for('admin.students'))


@admin.route('/registerStudent')
def registerStudent():
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            # fetch department data and render in dropdown list
            # depList = department.fetch_dep_list()
            # schList = scholarship.fetch_sch_list()
            # set the enrolment data less than today's date
            # today = datetime.now().date()
            # staffList = staff.fetchStaff()
            return render_template('registerStudent.html')
    else:
        return render_template('accessDenied.html')


@admin.route('admin/addStudent', methods=["POST"])
def addStudent():
    id = request.form.get("id")
    fname = request.form.get("fname")
    lname = request.form.get("lname")

    address = request.form.get("address")
    phone = request.form.get("phone")
    email = request.form.get("email")
    pwd = request.form.get("pwd")
    hashed_pwd = user.hashPwd(pwd)

    user.insertNew(email, hashed_pwd, 'Student', 'Change password')
    student.insertNew(id, fname, lname, address,
                      phone, email)

    emailSender.sendEmail(
        email, f"Kia ora {fname} {lname}, You are now registered to use Lincoln University's Postgraduate Monitoring System.  Your initial password to login is {pwd}.")
    return redirect(url_for('admin.students'))


@admin.route('/reportList')
def reportList():
    filterList = []
    filterMsg = ""
    clauseStr = "true"
    dep = request.args.get('department')
    period = request.args.get('period')
    repStatus = request.args.get('repStatus')
    studentSearch = request.args.get('studentSearch')
    if studentSearch:
        searchName = "%" + str(studentSearch) + "%"
        # searchId = int(studentSearch)
        clauseStr = f"student.StudentID = '{studentSearch}' or student.FirstName like '{searchName}' or student.LastName like '{searchName}'"
    else:
        if dep:
            filterList.append(f"student.DepartmentCode = '{dep}'")
        if period:
            filterList.append(f"sixmr.ReportPeriodEndDate = '{period}'")
        if repStatus:
            if repStatus == 'Completed' :
                filterList.append("sixmr.Status = 'Finalised'")
            elif repStatus == 'Uncomplete':
                filterList.append("not sixmr.Status = 'Finalised'")                
            else:
                filterList.append("sixmr.ReportID is null")
        clauseDivider = ' && '
        clauseStr = clauseDivider.join(filterList)
    # reportsFiltered = report.fetchReportFiltered(clauseStr)
    # reports = report.fetchReportFullList()
    # reports = report.fetchReportTest()

    if dep or period or repStatus or studentSearch:
        reports = report.fetchReportFiltered(clauseStr)
    else:
        reports = report.fetchReportFullList()
    
    reportsWithStatus = []
    
    for rep in reports:
        status = report.fetchReportStatus(rep['ReportID'])
        # orderDiff = report.getCurrentReportOrder()["reportOrder"] - report.fetchexistedReportNum(rep['StudentID'])
        if len(status) == 6:
                reportsWithStatus.append(
                    {
                        'StudentID': rep['StudentID'],
                        'name': rep['name'],
                        'email': rep['Email'],
                        'Dep': rep['DepartmentCode'],
                        'ReportID': rep['ReportID'],
                        'period': rep['ReportPeriodEndDate'],
                       
                        'Status': rep['Status'],
                        'Completion': 100,
                        'Order': rep['B_ReportOrder'],


                    }
                )
        if len(status) == 5:
                reportsWithStatus.append(
                    {
                        'StudentID': rep['StudentID'],
                        'name': rep['name'],
                        'email': rep['Email'],
                        'Dep': rep['DepartmentCode'],
                        'ReportID': rep['ReportID'],
                        'period': rep['ReportPeriodEndDate'],
                       
                        'Status': rep['Status'],
                        'Completion': 83.33,
                        'Order': rep['B_ReportOrder'],


                    }
                )
        if len(status) == 4:
                reportsWithStatus.append(
                    {
                        'StudentID': rep['StudentID'],
                        'name': rep['name'],
                        'email': rep['Email'],
                        'Dep': rep['DepartmentCode'],
                        'ReportID': rep['ReportID'],
                        'period': rep['ReportPeriodEndDate'],
                       
                        'Status': rep['Status'],
                        'Completion': 66.67,
                        'Order': rep['B_ReportOrder'],

                    }
                )
        if len(status) == 3:
                reportsWithStatus.append(
                    {
                        'StudentID': rep['StudentID'],
                        'name': rep['name'],
                        'email': rep['Email'],
                        'Dep': rep['DepartmentCode'],
                        'ReportID': rep['ReportID'],
                        'period': rep['ReportPeriodEndDate'],
                       
                        'Status': rep['Status'],
                        'Completion': 50,
                        'Order': rep['B_ReportOrder'],

                    }
                )
        if len(status) == 2:
                reportsWithStatus.append(
                    {
                        'StudentID': rep['StudentID'],
                        'name': rep['name'],
                        'email': rep['Email'],
                        'Dep': rep['DepartmentCode'],
                        'ReportID': rep['ReportID'],
                        'period': rep['ReportPeriodEndDate'],
                        
                        'Status': rep['Status'],
                        'Completion': 33.33,
                        'Order': rep['B_ReportOrder'],

                    }
                )
        if len(status) == 1:
                reportsWithStatus.append(
                    {
                        'StudentID': rep['StudentID'],
                        'name': rep['name'],
                        'email': rep['Email'],
                        'Dep': rep['DepartmentCode'],
                        'ReportID': rep['ReportID'],
                        'period': rep['ReportPeriodEndDate'],
                       
                        'Status': rep['Status'],
                        'Completion': 16.67,
                        'Order': rep['B_ReportOrder'],

                    }
                )
        if len(status) == 0:
                reportsWithStatus.append(
                    {
                        'StudentID': rep['StudentID'],
                        'name': rep['name'],
                        'email': rep['Email'],
                        'Dep': rep['DepartmentCode'],
                        'ReportID': rep['ReportID'],
                        'period': rep['ReportPeriodEndDate'],
                       
                        'Status': rep['Status'],
                        'Completion': 3,
                        'Order': rep['B_ReportOrder'],


                    }
                )
              

    # emailList = report.fetchEmailList(1)
    
    
    studentList = report.fetchStudentHelper()
    suspendedStuId = report.fetchSupspendedStuId()
    for student in studentList:
        if student['StudentID'] not in suspendedStuId:
            orderDiff = report.getCurrentReportOrder()["reportOrder"] - report.fetchexistedReportNum(student['StudentID'])
            for i in range(0,orderDiff):
                orderDiff = orderDiff - 1
                test = report.getCurrentReportOrder()["reportOrder" ]
                if (not dep and not period and not dep and not repStatus) or (dep==student['DepartmentCode'] and repStatus not in ['Completed','Uncomplete'])  or repStatus=='Norecord':
                    reportsWithStatus.append(
                        {
                            'StudentID': student['StudentID'],
                            'name': student['name'],
                            'email': student['StudentID'],
                            'Dep': student['DepartmentCode'],
                            'ReportID': "",
                            'period':"" ,
                            
                            'Status': "Not Started",
                            'Completion': 0,
                            'Order': '',


                        }
                    )
    # reportsWithStatus.sort()
    if len(reports) == 0 and len(reportsWithStatus)==len(report.fetchReportFullList()):
        filterMsg = "No Matching Report!Please Try Again!"
    return render_template('reportList.html', reportsWithStatus=reportsWithStatus, dep=dep, period=period, repStatus=repStatus, filterMsg=filterMsg)


@admin.route('/reportTracker')
def tracker():
    reportId = request.args.get('reportId')
    existingReportId = report.fetchReportID()
    reportIsExsited = False
    errorMsg = ""
    supervisors = []
    conDetail = []
    pgcDetail = PGChair.fetchPGChairDetail()
    stuSubmittedTime = ""
    supPSubmittedTime = ""
    supA1SubmittedTime = ""
    supA2SubmittedTime = ""
    conSubmittedTime = ""
    student = 0
    statusPoint = 0
    completion = 0
    sixmrStatus = ""
    finalRole = ""
    fetchedReport = None
    supsDetail=[]
    supEmailList = []
    submitEmailList = []
    unSubmitSupEmailList = []
    supReminderList = []
    if reportId:
        if {'ReportID': int(reportId)} in existingReportId:
            reportIsExsited = True
            student = report.fetchStudent(int(reportId))
            supervisors = supervisor.fetchSupList(student['StudentID'])
            conDetail = convenor.fetchConvenor(student['StudentID'])
            supsDetail = supervisor.fetchSupList(student['StudentID'])
            for sup in supsDetail:
                supEmailList.append(sup['Email'])
            reId = report.fetchSubmittedReportId()
            if int(reportId) in reId:
                stuResult = report.fetchSubmittedTime(
                    int(reportId), 'Student')
                if stuResult:
                    stuSubmittedTime = stuResult[0]
                supPResult = report.fetchSubmittedTime(
                    int(reportId), 'Principal Supervisor')
                if supPResult:
                    supPSubmittedTime = supPResult[0]
                supAResult = report.fetchSubmittedTime(
                    int(reportId), 'Associate Supervisor')
                if supAResult:
                    if len(supAResult) == 1:
                        supA1SubmittedTime = supAResult[0]
                    if len(supAResult) == 2:
                        supA1SubmittedTime = supAResult[0]
                        supA2SubmittedTime = supAResult[1]
                conResult = report.fetchSubmittedTime(
                    int(reportId), 'Convenor')
                if conResult:
                    conSubmittedTime = conResult[0]

    
            fetchedReport = report.fetchReportStatus(reportId)
            for db in fetchedReport:
                submitEmailList.append(db["SubmitterEmail"])
            statusPoint = len(fetchedReport)
            if statusPoint >2 and statusPoint <6 :
                unSubmitSupEmailList  = list(set(supEmailList)^set(submitEmailList[2: statusPoint]))
            if len(unSubmitSupEmailList) > 0:
                for sup in unSubmitSupEmailList:
                    supName = supervisor.fetchSupName(sup)
                    supReminderList.append({
                        'supName':supName,
                        'supEmail':sup
                    })

            completion = round((statusPoint/6)*100,2)
            sixmrStatus = report.fetchSixmrStatus(reportId)

            finalRole = report.fetchReportFinalRole(student['StudentID'])
    if reportId and reportIsExsited == False:
        errorMsg = "The system has no record of a report with this ID"
    
    return render_template('reportTrackerNew.html', student=student, reportId=reportId, statusPoint=statusPoint, completion=completion, reportIsExsited=reportIsExsited, errorMsg=errorMsg, supervisors=supervisors, conDetail=conDetail, stuSubmittedTime=stuSubmittedTime, supPSubmittedTime=supPSubmittedTime, supA1SubmittedTime=supA1SubmittedTime, supA2SubmittedTime=supA2SubmittedTime, conSubmittedTime=conSubmittedTime,
                           sixmrStatus=sixmrStatus, finalRole=finalRole,fetchedReport=fetchedReport,pgcDetail=pgcDetail,supsDetail=supsDetail, supReminderList=supReminderList,unSubmitSupEmailList=unSubmitSupEmailList )


@admin.route('admin/trackerReminderStudent', methods=["POST"])
def trackerReminderStudent():
    email = request.form.get("email")
    name = request.form.get("name")
    reportId = request.form.get("reportId")
    emailSender.sendEmail(
        email, f"Kia ora {name}, Please submit your 6MR as soon as possible.")
    return redirect(url_for('admin.tracker', reportId=reportId))


@admin.route('admin/trackerReminderSupP', methods=["POST"])
def trackerReminderSupP():
    email = request.form.get("email")
    name = request.form.get("name")
    reportId = request.form.get("reportId")
    emailSender.sendEmail(
        email, f"Kia ora Principal Supervisor {name}, your student has submitted their 6MR information, please submit your part as soon as possible.")
    return redirect(url_for('admin.tracker', reportId=reportId))



@admin.route('admin/remindSupervisor', methods=["POST"])
def remindSupervisor():
    email = request.form.get("email")
    # name = request.form.get("name")
    reportId = request.form.get("reportId")
    emailSenderToMany.sendEmail(
        email, f"Kia ora Supervisor(s), Your student has submitted their 6MR information. Please finish your part as soon as possible.")
    return redirect(url_for('admin.tracker', reportId=reportId))


@admin.route('admin/trackerReminderCon', methods=["POST"])
def trackerReminderCon():
    email = request.form.get("email")
    name = request.form.get("name")
    reportId = request.form.get("reportId")
    emailSender.sendEmail(
        email, f"Kia ora convenor(PG Chair) {name}, supervisors have submitted 6MR, please submit your part as soon as possible.")
    return redirect(url_for('admin.tracker', reportId=reportId))


@admin.route('admin/remindStudent', methods=["POST"])
def remindStudent():
    email = request.form.get("email")
    name = request.form.get("name")
    emailSender.sendEmail(
        email, f"Kia ora {name}, Please start your 6MR as soon as possible.")
    
    return redirect(url_for('admin.reportList'))


@admin.route('admin/confirmReport', methods=["POST"])
def confirmReport():
    reportId = request.form.get("reportId")
    emailList = report.fetchEmailList(reportId)
    emailSenderToMany.sendEmail(
        emailList, "Your 6MR has been submitted successfully, thank you!")
    
    return redirect(url_for('admin.reportList'))


@admin.route('/sixmrCompletion')
def sixmrCompletion():
    selectedPeriod = request.args.get('selectedPeriod')

    # set up current period as default value
    # selectedPeriod = '2023-06-30'
    if selectedPeriod:
        selectedPeriod = selectedPeriod
    else:
        selectedPeriod = '2023-06-30'
    suspendeStuNumSOLA = analysisReportData.countSuspendedStudentWithPeriod('SOLA', selectedPeriod)
    suspendeStuNumDEM = analysisReportData.countSuspendedStudentWithPeriod('DEM', selectedPeriod)
    suspendeStuNumDTSS = analysisReportData.countSuspendedStudentWithPeriod('DTSS', selectedPeriod)
    stuNumSOLA = analysisReportData.fetchStudentNumWithDepCode('SOLA') - suspendeStuNumSOLA
    stuNumDEM = analysisReportData.fetchStudentNumWithDepCode('DEM') - suspendeStuNumDEM
    stuNumDTSS = analysisReportData.fetchStudentNumWithDepCode('DTSS') - suspendeStuNumDTSS
    repNumSOLA = analysisReportData.fetchReportNum('SOLA', selectedPeriod)
    repNumDEM = analysisReportData.fetchReportNum('DEM', selectedPeriod)
    repNumDTSS = analysisReportData.fetchReportNum('DTSS', selectedPeriod)
    return render_template('sixmrCompletion.html', stuNumSOLA=stuNumSOLA, stuNumDEM=stuNumDEM, stuNumDTSS=stuNumDTSS, repNumSOLA=repNumSOLA, repNumDEM=repNumDEM, repNumDTSS=repNumDTSS, selectedPeriod=selectedPeriod)


@admin.route('/studentPerformance')
def studentPerformance():
    studentList = analysisReportData.fetchStudentList()
    performanceList = []
    for student in studentList:
        ratingList = analysisReportData.fetchReportRating(student['StudentID'])
        periodList = analysisReportData.fetchReportPeriodList(student['StudentID'])
        # rating1 = ""
        # rating2 = ""
        # rating3 = ""
        ratings = []
        if '2022-06-30' not in periodList:
            if analysisReportData.checkIfStudentSuspended(student['StudentID'], '2022-06-30'):
                # rating1 = 'X'
                ratings.append('X')
            else:
                ratings.append(' ')
               
        else:
            # rating1 = ratingList[0]['2022-06-30']
            ratings.append(ratingList[0]['2022-06-30'])
        if '2022-12-31' not in periodList:
            if analysisReportData.checkIfStudentSuspended(student['StudentID'], '2022-12-31'):
                # rating2 = 'X'  
                ratings.append('X')
            else:
                ratings.append(' ')  
        else:
            # rating2 = ratingList[1]['2022-12-31']
            ratings.append(ratingList[1]['2022-12-31'])
        if '2023-06-30' not in periodList:
            if analysisReportData.checkIfStudentSuspended(student['StudentID'], '2023-06-30'):
                ratings.append('X')
            else:
                ratings.append(' ')
        else:
            # rating3 = ratingList[2]['2023-06-30']
            ratings.append(ratingList[2]['2023-06-30'])

        operation = ''
        if not ratings[2] or ratings[2]==' ':
            operation = 'Pending'
        if ratings[2] == "R":
            operation = 'Meeting'
        if ratings[2] == "O" and ratings[1] == "O":
            operation = 'Reminder'
        if ratings[2] == "O" and ratings[1] != "O":
            operation = 'Follow Up'
        
        convenorName = convenor.fetchConvenor(student['StudentID'])['convenorName']
        convenorEmail = convenor.fetchConvenor(student['StudentID'])['Email']
        performanceList.append({
            'studentName': student['name'],
            'studentId':student['StudentID'],
            'studentEmail': student['Email'],
            'dep':student['DepartmentCode'],
            'sup':analysisReportData.fetchSupList(student['StudentID']),
            'convenorName': convenorName,
            'convenorEmail':convenorEmail,
            # 'rating1':rating1,
            # 'rating2':rating2,
            # 'rating3':rating3,
            'ratings':ratings,
            'operation':operation,
            
        })
   
    return render_template('studentPerformance.html', performanceList=performanceList)

@admin.route('/individulPerformance/<studentId>')
def individulPerformance(studentId):
    
    period1 = '2022-06-30'
    period2 = '2022-12-31'
    period3 = '2023-06-30'
    reportIdPeriod1 = analysisReportData.fetchIndividulReportId(studentId,period1 )
    reportIdPeriod2 = analysisReportData.fetchIndividulReportId(studentId,period2 )
    reportIdPeriod3 = analysisReportData.fetchIndividulReportId(studentId,period3 )
    supervisionIDList = analysisReportData.fetchSupervisionIDList(studentId)
    resultNumSup1PeriodExcList = []
    resultNumSup1PeriodGoodList = []
    resultNumSup1PeriodSatList = []
    resultNumSup1PeriodBAList = []
    resultNumSup1PeriodUnSatList = []
    resultNumSup2PeriodExcList = []
    resultNumSup2PeriodGoodList = []
    resultNumSup2PeriodSatList = []
    resultNumSup2PeriodBAList = []
    resultNumSup2PeriodUnSatList = []
    resultNumSup3PeriodExcList = []
    resultNumSup3PeriodGoodList = []
    resultNumSup3PeriodSatList = []
    resultNumSup3PeriodBAList = []
    resultNumSup3PeriodUnSatList = []
    #sup1
    if reportIdPeriod1:
        resultNumSup1Period1Exc = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[0], "Excellent")
        resultNumSup1PeriodExcList.append(resultNumSup1Period1Exc)
        resultNumSup1Period1Good = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[0], "Good")
        resultNumSup1PeriodGoodList.append(resultNumSup1Period1Good)
        resultNumSup1Period1Sat = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[0], "Satisfactory")
        resultNumSup1PeriodSatList.append(resultNumSup1Period1Sat)
        resultNumSup1Period1BA = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[0], "Below Average")
        resultNumSup1PeriodBAList.append(resultNumSup1Period1BA)
        resultNumSup1Period1UnSat = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[0], "Unsatisfactory")
        resultNumSup1PeriodUnSatList.append(resultNumSup1Period1UnSat)
    else:
        resultNumSup1PeriodExcList.append("")
        resultNumSup1PeriodGoodList.append("")
        resultNumSup1PeriodSatList.append("")
        resultNumSup1PeriodBAList.append("")
        resultNumSup1PeriodUnSatList.append("")

    if reportIdPeriod2:
        resultNumSup1Period2Exc = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[0], "Excellent")
        resultNumSup1PeriodExcList.append(resultNumSup1Period2Exc)
        resultNumSup1Period2Good = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[0], "Good")
        resultNumSup1PeriodGoodList.append(resultNumSup1Period2Good)
        resultNumSup1Period2Sat = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[0], "Satisfactory")
        resultNumSup1PeriodSatList.append(resultNumSup1Period2Sat)
        resultNumSup1Period2BA = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[0], "Below Average")
        resultNumSup1PeriodBAList.append(resultNumSup1Period2BA)
        resultNumSup1Period2UnSat = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[0], "Unsatisfactory")
        resultNumSup1PeriodUnSatList.append(resultNumSup1Period2UnSat)
    else:
        resultNumSup1PeriodExcList.append("")
        resultNumSup1PeriodGoodList.append("")
        resultNumSup1PeriodSatList.append("")
        resultNumSup1PeriodBAList.append("")
        resultNumSup1PeriodUnSatList.append("")
    if reportIdPeriod3:
        resultNumSup1Period3Exc = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[0], "Excellent")
        resultNumSup1PeriodExcList.append(resultNumSup1Period3Exc)
        resultNumSup1Period3Good = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[0], "Good")
        resultNumSup1PeriodGoodList.append(resultNumSup1Period3Good)
        resultNumSup1Period3Sat = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[0], "Satisfactory")
        resultNumSup1PeriodSatList.append(resultNumSup1Period3Sat)
        resultNumSup1Period3BA = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[0], "Below Average")
        resultNumSup1PeriodBAList.append(resultNumSup1Period3BA)
        resultNumSup1Period3UnSat = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[0], "Unsatisfactory")
        resultNumSup1PeriodUnSatList.append(resultNumSup1Period3UnSat)
    else:
        resultNumSup1PeriodExcList.append("")
        resultNumSup1PeriodGoodList.append("")
        resultNumSup1PeriodSatList.append("")
        resultNumSup1PeriodBAList.append("")
        resultNumSup1PeriodUnSatList.append("")
    #sup2
    if reportIdPeriod1:
        resultNumSup2Period1Exc = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[1], "Excellent")
        resultNumSup2PeriodExcList.append(resultNumSup2Period1Exc)
        resultNumSup2Period1Good = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[1], "Good")
        resultNumSup2PeriodGoodList.append(resultNumSup2Period1Good)
        resultNumSup2Period1Sat = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[1], "Satisfactory")
        resultNumSup2PeriodSatList.append(resultNumSup2Period1Sat)
        resultNumSup2Period1BA = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[1], "Below Average")
        resultNumSup2PeriodBAList.append(resultNumSup2Period1BA)
        resultNumSup2Period1UnSat = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[1], "Unsatisfactory")
        resultNumSup2PeriodUnSatList.append(resultNumSup2Period1UnSat)
    else:
        resultNumSup2PeriodExcList.append("")
        resultNumSup2PeriodGoodList.append("")
        resultNumSup2PeriodSatList.append("")
        resultNumSup2PeriodBAList.append("")
        resultNumSup2PeriodUnSatList.append("")

    if reportIdPeriod2:
        resultNumSup2Period2Exc = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[1], "Excellent")
        resultNumSup2PeriodExcList.append(resultNumSup2Period2Exc)
        resultNumSup2Period2Good = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[1], "Good")
        resultNumSup2PeriodGoodList.append(resultNumSup2Period2Good)
        resultNumSup2Period2Sat = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[1], "Satisfactory")
        resultNumSup2PeriodSatList.append(resultNumSup2Period2Sat)
        resultNumSup2Period2BA = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[1], "Below Average")
        resultNumSup2PeriodBAList.append(resultNumSup2Period2BA)
        resultNumSup2Period2UnSat = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[1], "Unsatisfactory")
        resultNumSup2PeriodUnSatList.append(resultNumSup2Period2UnSat)
    else:
        resultNumSup2PeriodExcList.append("")
        resultNumSup2PeriodGoodList.append("")
        resultNumSup2PeriodSatList.append("")
        resultNumSup2PeriodBAList.append("")
        resultNumSup2PeriodUnSatList.append("")
    if reportIdPeriod3:
        resultNumSup2Period3Exc = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[1], "Excellent")
        resultNumSup2PeriodExcList.append(resultNumSup2Period3Exc)
        resultNumSup2Period3Good = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[1], "Good")
        resultNumSup2PeriodGoodList.append(resultNumSup2Period3Good)
        resultNumSup2Period3Sat = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[1], "Satisfactory")
        resultNumSup2PeriodSatList.append(resultNumSup2Period3Sat)
        resultNumSup2Period3BA = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[1], "Below Average")
        resultNumSup2PeriodBAList.append(resultNumSup2Period3BA)
        resultNumSup2Period3UnSat = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[1], "Unsatisfactory")
        resultNumSup2PeriodUnSatList.append(resultNumSup2Period3UnSat)
    else:
        resultNumSup2PeriodExcList.append("")
        resultNumSup2PeriodGoodList.append("")
        resultNumSup2PeriodSatList.append("")
        resultNumSup2PeriodBAList.append("")
        resultNumSup2PeriodUnSatList.append("")
    #sup3
    if reportIdPeriod1:
        resultNumSup3Period1Exc = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[2], "Excellent")
        resultNumSup3PeriodExcList.append(resultNumSup3Period1Exc)
        resultNumSup3Period1Good = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[2], "Good")
        resultNumSup3PeriodGoodList.append(resultNumSup3Period1Good)
        resultNumSup3Period1Sat = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[2], "Satisfactory")
        resultNumSup3PeriodSatList.append(resultNumSup3Period1Sat)
        resultNumSup3Period1BA = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[2], "Below Average")
        resultNumSup3PeriodBAList.append(resultNumSup3Period1BA)
        resultNumSup3Period1UnSat = analysisReportData.fetchReportResult(reportIdPeriod1, supervisionIDList[2], "Unsatisfactory")
        resultNumSup3PeriodUnSatList.append(resultNumSup3Period1UnSat)
    else:
        resultNumSup3PeriodExcList.append("")
        resultNumSup3PeriodGoodList.append("")
        resultNumSup3PeriodSatList.append("")
        resultNumSup3PeriodBAList.append("")
        resultNumSup3PeriodUnSatList.append("")

    if reportIdPeriod2:
        resultNumSup3Period2Exc = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[2], "Excellent")
        resultNumSup3PeriodExcList.append(resultNumSup3Period2Exc)
        resultNumSup3Period2Good = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[2], "Good")
        resultNumSup3PeriodGoodList.append(resultNumSup3Period2Good)
        resultNumSup3Period2Sat = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[2], "Satisfactory")
        resultNumSup3PeriodSatList.append(resultNumSup3Period2Sat)
        resultNumSup3Period2BA = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[2], "Below Average")
        resultNumSup3PeriodBAList.append(resultNumSup3Period2BA)
        resultNumSup3Period2UnSat = analysisReportData.fetchReportResult(reportIdPeriod2, supervisionIDList[2], "Unsatisfactory")
        resultNumSup3PeriodUnSatList.append(resultNumSup3Period2UnSat)
    else:
        resultNumSup3PeriodExcList.append("")
        resultNumSup3PeriodGoodList.append("")
        resultNumSup3PeriodSatList.append("")
        resultNumSup3PeriodBAList.append("")
        resultNumSup3PeriodUnSatList.append("")
    if reportIdPeriod3:
        resultNumSup3Period3Exc = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[2], "Excellent")
        resultNumSup3PeriodExcList.append(resultNumSup3Period3Exc)
        resultNumSup3Period3Good = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[2], "Good")
        resultNumSup3PeriodGoodList.append(resultNumSup3Period3Good)
        resultNumSup3Period3Sat = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[2], "Satisfactory")
        resultNumSup3PeriodSatList.append(resultNumSup3Period3Sat)
        resultNumSup3Period3BA = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[2], "Below Average")
        resultNumSup3PeriodBAList.append(resultNumSup3Period3BA)
        resultNumSup3Period3UnSat = analysisReportData.fetchReportResult(reportIdPeriod3, supervisionIDList[2], "Unsatisfactory")
        resultNumSup3PeriodUnSatList.append(resultNumSup3Period3UnSat)
    else:
        resultNumSup3PeriodExcList.append("")
        resultNumSup3PeriodGoodList.append("")
        resultNumSup3PeriodSatList.append("")
        resultNumSup3PeriodBAList.append("")
        resultNumSup3PeriodUnSatList.append("")
    
    #dataset for pie
    # period = '2023-06-30'
    # excNum = resultNumSup1Period3Exc + resultNumSup2Period3Exc + resultNumSup3Period3Exc
    # goodNum = resultNumSup1Period3Good + resultNumSup2Period3Good + resultNumSup3Period3Good
    # satNum = resultNumSup1Period3Sat + resultNumSup2Period3Sat + resultNumSup3Period3Sat
    # baNum = resultNumSup1Period3BA + resultNumSup2Period3BA + resultNumSup3Period3BA
    # unsatNum = resultNumSup1Period3UnSat + resultNumSup2Period3UnSat + resultNumSup3Period3UnSat
    return render_template('individulPerformance.html', studentId=studentId, resultNumSup1PeriodExcList=resultNumSup1PeriodExcList, resultNumSup1PeriodGoodList=resultNumSup1PeriodGoodList,
                           resultNumSup1PeriodSatList=resultNumSup1PeriodSatList,resultNumSup1PeriodBAList=resultNumSup1PeriodBAList,resultNumSup1PeriodUnSatList=resultNumSup1PeriodUnSatList, resultNumSup2PeriodExcList=resultNumSup2PeriodExcList, resultNumSup2PeriodGoodList=resultNumSup2PeriodGoodList,
                           resultNumSup2PeriodSatList=resultNumSup2PeriodSatList,resultNumSup2PeriodBAList=resultNumSup2PeriodBAList,resultNumSup2PeriodUnSatList=resultNumSup2PeriodUnSatList,  resultNumSup3PeriodExcList=resultNumSup3PeriodExcList, resultNumSup3PeriodGoodList=resultNumSup3PeriodGoodList,
                           resultNumSup3PeriodSatList=resultNumSup3PeriodSatList,resultNumSup3PeriodBAList=resultNumSup3PeriodBAList,resultNumSup3PeriodUnSatList=resultNumSup3PeriodUnSatList)

@admin.route('admin/studentPerformanceReminder', methods=["POST"])
def studentPerformanceReminder():
    email = request.form.get("email")
    name = request.form.get("name")
   
    emailSender.sendEmail(
        email, f"Kia ora {name}, your 6MR indicates your progress has been modest. Please meet with your Convenor to discuss.")
    
    return redirect(url_for('admin.studentPerformance'))

@admin.route('admin/arrangeMeeting', methods=["POST"])
def arrangeMeeting():
    studentEmail = request.form.get("studentEmail")
    convenorEmail = request.form.get("convenorEmail")
    studentName = request.form.get("studentName")
    convenorName = request.form.get("studentName")
    email = [studentEmail,convenorEmail]
    emailSenderToMany.sendEmail(
        email, f"Kia ora, a review meeting has been scheduled between student({studentName}) and the Convenor({convenorName}) in relation to academic progress. Please attend on time.")
    
    return redirect(url_for('admin.studentPerformance'))

@admin.route('admin/followupReminder', methods=["POST"])
def followupReminder():
    email = request.form.get("convenorEmail")
    studentName = request.form.get("studentName")
    convenorName = request.form.get("studentName")
   
    emailSender.sendEmail(
        email, f"Kia ora {convenorName}, please follow up with {studentName}'s supervisors regarding their recent 6MR.")
    
    return redirect(url_for('admin.studentPerformance'))

@admin.route('/facultyPerformance')
def facultyPerformance():
    criterionValue = ""
    criterionList = analysisReportData.fetchCriterionList()
    formanceOverAllCurrent = analysisReportData.fetchFacultyPerformanceOverAllCurrent()
    studentNum = analysisReportData.fetchStudentNum()
    reportNumCurrent = analysisReportData.fetchReportNumCurrent()
    filterList = []
    clauseStr = "true"
    dep = request.args.get('department')
    period = request.args.get('period')
    criterionId = request.args.get('criterion')
    criterion = "Over All"
    
    if dep:
        filterList.append(f"student.DepartmentCode = '{dep}'")
        studentNum = analysisReportData.fetchStudentNumWithDepCode(dep)
        reportNumCurrent = analysisReportData.fetchReportNumFiltered(
            period, dep)
    if period:
        filterList.append(f"sixmr.ReportPeriodEndDate = '{period}'")
    if criterionId:
        filterList.append(f"c_table.CriterionID = '{criterionId}'")
        criterionValue = int(criterionId)
        criterion = analysisReportData.fetchCriterion(criterionId)
    if period and not dep:
        reportNumCurrent = analysisReportData.fetchReportNumFilteredPeriod(
            period)
    clauseDivider = ' && '
    clauseStr = clauseDivider.join(filterList)
    if dep or period or criterionId:
        veryGoodNum = analysisReportData.fetchFacultyPerformanceFiltered(
            'Very Good', clauseStr)
        goodNum = analysisReportData.fetchFacultyPerformanceFiltered(
            'Good', clauseStr)
        satisfactoryNum = analysisReportData.fetchFacultyPerformanceFiltered(
            'Satisfactory', clauseStr)
        unsatisfactorNum = analysisReportData.fetchFacultyPerformanceFiltered(
            'Unsatisfactor', clauseStr)
        notRelevantNum = analysisReportData.fetchFacultyPerformanceFiltered(
            'Not relevant', clauseStr)
        formanceOverAllCurrent = {
            'veryGoodNum': veryGoodNum,
            'goodNum': goodNum,
            'satisfactoryNum': satisfactoryNum,
            'unsatisfactorNum': unsatisfactorNum,
            'notRelevantNum': notRelevantNum,
        }
    return render_template('facultyPerformance.html', criterionList=criterionList, formanceOverAllCurrent=formanceOverAllCurrent, studentNum=studentNum, reportNumCurrent=reportNumCurrent, dep=dep, period=period, criterionValue=criterionValue, criterion=criterion)


@admin.route('/facultyPerformance/OverPeriod')
def facultyPerformanceOverPeriod():

    period3VeryGood = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2023-06-30", "Very Good")
    period2VeryGood = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-12-31", "Very Good")
    period1VeryGood = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-06-30", "Very Good")

    period3Good = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2023-06-30", "Good")
    period2Good = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-12-31", "Good")
    period1Good = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-06-30", "Good")

    period3Satisfactory = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2023-06-30", "Satisfactory")
    period2Satisfactory = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-12-31", "Satisfactory")
    period1Satisfactory = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-06-30", "Satisfactory")

    period3Unsatisfactor = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2023-06-30", "Unsatisfactory")
    period2Unsatisfactor = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-12-31", "Unsatisfactory")
    period1Unsatisfactor = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-06-30", "Unsatisfactory")

    period3NotRelevant = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2023-06-30", "Not Relevant")
    period2NotRelevant = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-12-31", "Not Relevant")
    period1NotRelevant = analysisReportData.fetchFacultyPerformanceOverPeriod(
        "2022-06-30", "Not Relevant")

    return render_template('facultyPerformanceOverPeriod.html', period3VeryGood=period3VeryGood,
                           period2VeryGood=period2VeryGood,  period1VeryGood=period1VeryGood,
                           period1Good=period1Good, period2Good=period2Good, period3Good=period3Good,
                           period3Satisfactory=period3Satisfactory, period2Satisfactory=period2Satisfactory, period1Satisfactory=period1Satisfactory,
                           period3Unsatisfactor=period3Unsatisfactor, period2Unsatisfactor=period2Unsatisfactor, period1Unsatisfactor=period1Unsatisfactor,
                           period3NotRelevant=period3NotRelevant, period2NotRelevant=period2NotRelevant, period1NotRelevant=period1NotRelevant)


@admin.route('/analysisReport')
def analysisReport():
    return render_template('analysisReport.html')

# shan and claire's part
@admin.route('/convenors')
def convenors():
    if 'loggedin' in session:
            if session['role'] == "PG Administrator":
                # rendering convenorlist
                convenorList = Convenor.convenorList(session['username'])
                return render_template('convenors.html', convenorList=convenorList)
    else:
        return render_template('accessDenied.html')
    
@admin.route('/convenors/update', methods=['POST'])
def update_convenor():
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            phone = request.form['phone']
            depcode = request.form['departmentcode']
            id = request.form['staffid']
            convenor = Staff.update_staff(id, phone, depcode, id)
            flash('Profile has been updated successfully!', 'success')
            return redirect(url_for('admin.convenors'))
    else:
        return render_template('accessDenied.html')
    

@admin.route('/supervisors')
def supervisors():
    if 'loggedin' in session:
            if session['role'] == "PG Administrator":
                # rendering supervisorlist
                supervisorList = Supervisor.supervisorList(session['username'])
                depList = Department.fetch_dep_list(session['username'])
                return render_template('supervisors.html', supervisorList=supervisorList, depList=depList)
    else:
        return render_template('accessDenied.html')
    
@admin.route('/supervisors/update', methods=['POST'])
def update_supervisor():
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            phone = request.form['phone']
            depcode = request.form['departmentcode']
            id = request.form['staffid']
            supervisor = Staff.update_staff(id, phone, depcode, id)
            flash('Profile has been updated successfully!', 'success')
            return redirect(url_for('admin.supervisors'))
    else:
        return render_template('accessDenied.html')
    
@admin.route('/pgChair')
def pgChair():
    if 'loggedin' in session:
            if session['role'] == "PG Administrator":
                # rendering pgChairlist
                pgChairList = PGChair.pgChairList()
                return render_template('pgChair.html', pgChairList=pgChairList)
    else:
        return render_template('accessDenied.html')
    
@admin.route('/pgChair/update', methods=['POST'])
def update_pgChair():
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            phone = request.form['phone']
            depcode = request.form['departmentcode']
            id = request.form['staffid']
            pgChair = Staff.update_staff(id, phone, depcode, id)
            flash('Profile has been updated successfully!', 'success')
            return redirect(url_for('admin.pgChair'))
    else:
        return render_template('accessDenied.html')


@admin.route('/students/update', methods=['POST'])
def update_student():
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            address = request.form['address']
            phone = request.form['phone']
            MOS = request.form['modeofstudy']
            thesis = request.form['thesistitle']
            depcode = request.form['departmentcode']
            id = request.form['studentid']
            student = Student.update_student(id, address, phone, MOS, thesis, depcode, id)
            flash('Profile has been updated successfully!', 'success')
            return redirect(url_for('admin.students'))
    else:
        return render_template('accessDenied.html')
    
@admin.route('/reportList/viewReport/<reportId>')
def viewReport(reportId):
    # return render_template('viewReport.html',reportId=reportId)
    studentId = report.fetchStudent(reportId)['StudentID']
    return sixMRModule.view_6mr_report(studentId,reportId)

@admin.route('/studentemscho/<studentid>', methods=['GET', 'POST'])
def studentemscho(studentid):
    if 'loggedin' in session:
        # get scholarship information
        scholarships = student.student_scholarship(studentid)
        # get employment informaton
        employment = student.student_employment(studentid)
        return render_template('studentemscho.html', scholarships=scholarships, employment=employment)
    else:
        return render_template('accessDenied.html')

@admin.route('/student/suspend/<studentid>', methods=['GET'])
def suspend_student(studentid):
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            student.suspend_student(studentid)
            flash('Student has been suspended!', 'success')
            return redirect(url_for('admin.students'))
    else:
        return render_template('accessDenied.html')

@admin.route('/student/unsuspend/<studentid>', methods=['GET'])
def unsuspend_student(studentid):
    if 'loggedin' in session:
        if session['role'] == "PG Administrator":
            student.unsuspend_student(studentid)
            flash('Student has been unsuspended!', 'success')
            return redirect(url_for('admin.students'))
    else:
        return render_template('accessDenied.html')