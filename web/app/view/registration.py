from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, BS3PasswordFieldWidget
from flask_appbuilder.forms import DynamicForm
from flask_appbuilder.security.registerviews import RegisterUserDBView
from flask_appbuilder.security.sqla.manager import SecurityManager
from flask_babel import lazy_gettext
from flask_wtf.recaptcha import RecaptchaField
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, EqualTo


class AppRegisterUserDBForm(DynamicForm):
    username = StringField(
        lazy_gettext("User Name"),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    first_name = StringField(
        lazy_gettext("First Name"),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    last_name = StringField(
        lazy_gettext("Last Name"),
        validators=[DataRequired()],
        widget=BS3TextFieldWidget(),
    )
    email = StringField(
        lazy_gettext("Email"),
        validators=[DataRequired(), Email()],
        widget=BS3TextFieldWidget(),
    )
    password = PasswordField(
        lazy_gettext("Password"),
        description=lazy_gettext(
            "Please use a good password policy,"
            " this application does not check this for you"
        ),
        validators=[DataRequired()],
        widget=BS3PasswordFieldWidget(),
    )
    conf_password = PasswordField(
        lazy_gettext("Confirm Password"),
        description=lazy_gettext("Please rewrite the password to confirm"),
        validators=[EqualTo("password", message=lazy_gettext("Passwords must match"))],
        widget=BS3PasswordFieldWidget(),
    )


class AppRegisterUserDBView(RegisterUserDBView):
    form = AppRegisterUserDBForm


class AppSecurityManager(SecurityManager):
    registeruserdbview = AppRegisterUserDBView
