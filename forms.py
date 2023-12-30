from flask_wtf import FlaskForm,CSRFProtect
from wtforms import StringField, PasswordField,SubmitField,EmailField,FloatField,DateField,TextAreaField,IntegerField,SelectField,FormField,FieldList
from wtforms.validators import DataRequired,Email

class register_form(FlaskForm):
    choices = ['Employee',"Manager"]
    fname = StringField("First Name",validators=[DataRequired()])
    lname = StringField("Last Name",validators=[DataRequired()])
    user_type = SelectField("User Type",choices=choices,validators=[DataRequired()])
    email = EmailField("Email",validators=[Email()])
    submit = SubmitField("Register")


class login_form(FlaskForm):
    email = EmailField("Email",validators=[Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Login")

class chnage_pass(FlaskForm):
    new_password= PasswordField("New Password",validators=[DataRequired()])
    confrim_password= PasswordField("Confrim Password",validators=[DataRequired()])
    submit = SubmitField("Change Password")

class items_form(FlaskForm):
    name = StringField("Item Name",validators=[DataRequired()])
    brand_name = StringField("Brand Name",validators=[DataRequired()])
    price= FloatField("Price",validators=[DataRequired()])
    stock= IntegerField("Stock",validators=[DataRequired()])
    quantity= IntegerField("Price",validators=[DataRequired()])
    expiry = DateField("Expiry Date",validators=[DataRequired()])
    submit=SubmitField("Add Item")

class manage_user_form(FlaskForm):
    choices = ['Employee',"Manager"]
    fname = StringField("First Name",validators=[DataRequired()])
    lname = StringField("Last Name",validators=[DataRequired()])
    user_type = SelectField("User Type",choices=choices,validators=[DataRequired()])
    email = EmailField("Email",validators=[Email()])
    password = PasswordField("Password",validators=[DataRequired()])
    submit = SubmitField("Save Changes")

class mail_form(FlaskForm):
    reciver = EmailField("Email",validators=[Email()])
    subject = StringField('Subject',validators=[DataRequired()])
    body = TextAreaField('Mails',validators=[DataRequired()])
    send = SubmitField("Send")

    
    
class serach_form(FlaskForm):
    search =StringField("Search",validators=[DataRequired()])
    search_btn = SubmitField("Search")