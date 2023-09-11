from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SubmitField, SelectField,  TextAreaField, validators,IntegerField, ValidationError
from datetime import datetime

class ReportingPeriod(FlaskForm):
    """Form for selecting 6MR reporting period"""
    year = SelectField('Year:', choices=[(year, str(year)) for year in range(1950, 2101)], default = datetime.now().year)
    period = SelectField('Period:', choices = [('-06-30', 'Jan - Jun'),('-12-31', 'Jul - Dec')] )
    submit = SubmitField('Start A Report')

class MyReportsReportingPeriod(FlaskForm):
    """Form for selecting 6MR reporting period"""
    year = SelectField('Year:', choices=[(year, str(year)) for year in range(1950, 2101)], default = datetime.now().year)
    period = SelectField('Period:', choices = [('-06-30', 'Jan - Jun'),('-12-31', 'Jul - Dec')] )
    submit = SubmitField('Continue')