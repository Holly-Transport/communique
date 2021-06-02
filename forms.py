from flask_wtf import FlaskForm
from flask_ckeditor import CKEditorField
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, IntegerField
from wtforms.validators import DataRequired, URL


class CreatePostForm(FlaskForm):
    title = StringField("Blog Post Title", validators=[DataRequired()])
    subtitle = StringField("Subtitle", validators=[DataRequired()])
    date = StringField("Date (Month DD, YYYY)")
    # author = StringField("Your Name", validators=[DataRequired()])
    img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
    body = CKEditorField("Blog Content", validators=[DataRequired()])
    submit = SubmitField("Submit Post")

class Registration(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired()])
    password =PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Register")

class Login(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class Comments(FlaskForm):
    text = CKEditorField("Comment", validators=[DataRequired()])
    submit = SubmitField("Comment")

class PortfolioForm(FlaskForm):
    topic = StringField("Topic", validators=[DataRequired()])
    title = StringField("Title", validators=[DataRequired()])
    date = StringField("Date (Month DD, YYYY)")
    img_url = StringField("Image URL")
    port_url = StringField("Portfolio URL")
    body = StringField("Project Description", validators=[DataRequired()])
    submit = SubmitField("Submit Post")