# Group 12: Lincoln University's Postgraduate Monitoring System
This project delivers a Flask web app to automate the reporting process for the PhD programme operated by Lincoln University’s Faculty of Environment, Society and Design (the Faculty). 

On 30 June and 31 December each year, a report (6MR) must be submitted in relation to each PhD student. The purpose of the 6MR is to monitor student progress, obtain student evaluations of the Faculty’s performance and enable students to raise any concerns about supervisors and administrative staff. Each 6MR is completed by a student, before input is gathered from supervisors, a Department Convenor and on some occasions the Postgraduate Chair. The Postgraduate Administrator oversees the timely completion of 6MRs and uses data from them to produce reports regarding student and Faculty performance. 

Users can login to the system with their email and password. Dummy data has been created to illustrate the app's various features. The email for each fictitious user can be found in the 'user' table created by the project's SQL file. Every user has the system password '12345678' (please note the passwords in the database have been salted and hashed). The system also generates emails. These can be observed if a user has a Gmail account (each having a Gmail password of 'Lincoln@123').

## Table of contents
1. [System users](#users)
2. [Layout of the app](#layout)
3. [PG Administrator](#administrator)
4. [Students](#students)
5. [Supervisors](#supervisors)
6. [Convenors](#convenors)
7. [PG Chair](#chair)
8. [Installation](#installation)
9. [Credits](#credits)

<a name="users"></a>
## 1. System users
The users of the system are: 

* __Postgraduate (PG) Administrator__: responsible for all students' administrative issues, including managing the 6MR reporting process
* __Postgraduate (PG) Chair__: works with the PG Administrator and Department Convenors to ensure the 6MR process runs smoothly
* __Department Convenor__: manages matters relating to students within their Department
* __Supervisors__: one or more supervisors are assigned to every student. A supervisor may also be a Department Convenor. 
* __Students__: enrolled to complete a PhD programme.

The users progress each 6MR through the following reporting process: 
1. A student completes the mandatory Sections A to D of the 6MR. They have the option of completing Section F to raise concerns about supervisors or administrative staff with the PG Chair. 
2. Any Section F concerns are raised with the PG Chair for review and response. All other sections of the 6MR are made available to the student's Principal Supervisor. The Principal Supervisor may accept the 6MR, and the student will be informed of the acceptance via email. Alternatively, the Principal Supervisor can reject the 6MR, in which case notification of the rejection and feedback will be provided to the student via email. The student may then resubmit Sections A to D to the Principal Supervisor.  
3. Following acceptance by the Principal Supervisor, all of a student's supervisors must complete Section E of the 6MR. When this is done the student will be provided with a green, orange or red status from their Convenor except in cases where their Convenor is also their supervisor. In those circumstances the status will be provided by the PG Chair. 
4. 6MRs that have gone through the above steps are considered complete. Those that contributed to the 6MR will receive an email confirming it is finalised. The PG Administrator will be able to access reports based on information in the finalised 6MR. 

The email address and password for every user is found in the 'user' table created by the SQL file in this repository. For ease of reference, some example logins are included in the user interface descriptions below. 

<a name="layout"></a>
## 2. Layout of the app
The app has been structured with Flask Blueprint (Blueprint). This approach organises the logic into subdirectories. The app features five ‘blueprints’ for the System’s five user groups. Each blueprints encapsulates the functionality for a user group, such as views, templates, and other resources. There is also a general utility module (the ‘account’ blueprint) covering features such as logging in and validation. 

<a name="administrator"></a>
## 3. PG Administrator

The login details for the PG Administrator's interface are: 

 | Email                            | Password |
 | :------------------------------- | :------- |
 | lupgms.lincoln@gmail.com         | 12345678 |
 
This interface allows the PG Administrator to: 
*	Register a student to use the system
*	Approve or decline an application by a student to register with the System
*	View a list of all students, supervisors and convenors in the Faculty
*	View and edit all staff and student profile information
*	Track the progress of all 6MRs within the System
*	View completed 6MRs
*	View reports regarding the Faculty’s performance and the status achieved by the students.
*	Send emails to advise a student that they have successfully registered with the System, advise a student and their supervisors when a 6MR is finalised, and advise any person delaying the progress of a 6MR that they need to act. 
*	Compare the green/orange/red ratings received by each student in the current and immediately prior 6MR and email the appropriate persons to take action if appropriate e.g. if a first orange is received an email should be sent to the student's PG Convenor.  

<a name="students"></a>
## 4. Students
The student interface allows students to:
*	View and edit their personal information, including a complete employment and scholarship history 
*	Complete the student section of every required 6MR  
*	Track the progress of 6MRs through the reporting process via the 'My Reports' section of the interface.
*	View completed 6MRs.

It is noteworthy that: 
* only registered students can login to the system
* if a student registers themselves via the link on the home page, they will be unable to login until the PG Administrator approves their application
* when a student logs in for the first time, they will be asked to complete their profile details
* suspended students are unable to login to the system
* a student cannot start a new 6MR if they have started but not yet submitted their section of another 6MR.

Some example student login details include: 

| Type of student                                | Email                             | Password |
| :--------------------------------------------- | :-------------------------------- | :------- |
| Student with no 6MR for current period         | zhiyi.zhu@lincolnuni.ac.nz        | 12345678 |
| Student who has started but not completed a 6MR| alison.heath@lincolnuni.ac.nz     | 12345678 |
| Suspended student                              | mister.suspended@lincolnuni.ac.nz | 12345678 |
| Student with incomplete profile                | complete.profile@lincolnuni.ac.nz | 12345678 |
| Student who must update their password         | change.password@lincolnuni.ac.nz  | 12345678 |
| Student who has registered but is not approved | approval.required@lincolnuni.ac.nz| 12345678 |
| Student with Gmail email account\*             | dtss.student.lincolnuni@gmail.com | 12345678 |
\* Please note the password for the Gmail account is _Lincoln@123_

<a name="supervisors"></a>
## 5. Supervisors
The supervisors' interface can be explored with the login: 

| Email                            | Password |
| :------------------------------- | :------- |
| john.doe.lincolnuni@gmail.com    | 12345678 |

The interface gives supervisors the ability to: 
*	View and edit their personal information
*	View of list of all their supervisees and each supervisee’s personal profile information
*	In the case of a principal supervisor, accept or reject Section A to D of a student’s 6MR when they have completed it. 
*	View supervisees’ fully finalised 6MRs and partially complete 6MRs (excluding Section F) that have been completed by the student 
*	Complete Section E of supervisees’ 6MRs
*	Track the progress of 6MRs through the reporting process

<a name="convenors"></a>
## 6. Convenors
It is possible for a convenor to also be a supervisor. The convenors' interface can be viewed using the following login details:

| User                             | Email                            | Password |
| :------------------------------- | :------------------------------- | :------- |
| Convenor who is not a supervisor | dem.convenor.lincolnuni@gmail.com| 12345678 |
| Convenor who is a supervisor     | emily.lee.lincolnuni@gmail.com   | 12345678 |

The system allows convenors to: 
*	View and edit their personal information
*	View a list of all supervisors and all students within the convenor’s department and their personal profile information
*	View fully finalised 6MRs for all students in the Department, and partially completed 6MRs (excluding Section F) that require a rating by the convenor. 
*	Complete the green/orange/red status rating on every 6MR, except where the student has a supervisor who is also their convenor
*	Track the progress of 6MRs through the reporting process.

<a name="chair"></a>
## 7. PG Chair
The login details for the PG Chair's interface are: 

 | Email                            | Password |
 | :------------------------------- | :------- |
 | jacob.lopez.lincolnuni@gmail.com | 12345678 |

Upon logging in, the PG Chair can: 
* View and edit their personal information
*	View a list of all supervisors and students within the Faculty and their personal profile information
*	View partially completed 6MRs where	a student has completed Section F of their 6MR, or a student has a supervisor who is also their convenor.  
*	Provide a response to any Section F comments made by a student. 
*	Provide a green/orange/red status for a 6MR where a student has a supervisor who is also their convenor. 
*	View finalised 6MRs 
*	Track the progress of 6MRs through the reporting process.

<a name="installation"></a>
## 8. Installation

Install with pip:

$ pip install -r requirements.txt

<a name="credits"></a>
## 9. Credits
This app has been developed by the following students as part of Lincoln University's COMP639 course:
*	Alison Heath (Student ID: 1151854)
*	Vicky Kang (Student ID: 1155049)
*	Shan Lu (Student ID: 1149887)
*	Jason Tang (Student ID: 1153108) 
*	Claire Zhai (Student ID: 1155237)
*	Zhiyi Zhu (Student ID: 1152455)

Images used in this project were sourced from [Unsplash](https://www.unsplash.com).

## 10. Screenshots
<img src="/static/img/screenshots/19.jpg" width="600"/>
<img src="/static/img/screenshots/20.jpg" width="600"/>
<img src="/static/img/screenshots/01.jpg" width="600"/>
<img src="/static/img/screenshots/02.jpg" width="600"/>
<img src="/static/img/screenshots/03.jpg" width="600"/>
<img src="/static/img/screenshots/04.jpg" width="600"/>
<img src="/static/img/screenshots/05.jpg" width="600"/>
<img src="/static/img/screenshots/06.jpg" width="600"/>
<img src="/static/img/screenshots/07.jpg" width="600"/>
<img src="/static/img/screenshots/08.jpg" width="600"/>
<img src="/static/img/screenshots/09.jpg" width="600"/>
<img src="/static/img/screenshots/10.jpg" width="600"/>
<img src="/static/img/screenshots/11.jpg" width="600"/>
<img src="/static/img/screenshots/12.jpg" width="600"/>
<img src="/static/img/screenshots/13.jpg" width="600"/>
<img src="/static/img/screenshots/14.jpg" width="600"/>
<img src="/static/img/screenshots/15.jpg" width="600"/>
<img src="/static/img/screenshots/16.jpg" width="600"/>
<img src="/static/img/screenshots/17.jpg" width="600"/>
<img src="/static/img/screenshots/18.jpg" width="600"/>

