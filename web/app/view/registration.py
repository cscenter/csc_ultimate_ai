from flask import flash, redirect
from flask_appbuilder._compat import as_unicode
from flask_appbuilder.fieldwidgets import BS3TextFieldWidget, BS3PasswordFieldWidget
from flask_appbuilder.forms import DynamicForm
from flask_appbuilder.security.registerviews import RegisterUserDBView
from flask_appbuilder.security.sqla.manager import SecurityManager
from flask_babel import lazy_gettext
from flask_wtf.recaptcha import RecaptchaField
from wtforms import BooleanField, PasswordField, StringField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_appbuilder.security.sqla.models import User

from web.app import db_session


class AppRegisterUserDBForm(DynamicForm):
    username = StringField(
        lazy_gettext("User Name"),
        validators=[DataRequired(), Length(min=4, max=25)],
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

    def form_get(self, form):
        # if form:
        #     print(form)
        super().form_get(form)

    def form_post(self, form):
        if form:
            username = form.username.data
            with db_session() as session:
                result = session.query(User.username).filter_by(username=username).all()
                if result and len(result) > 0:
                    flash(as_unicode(lazy_gettext(f"Username '{username}' already exists.")), "danger")
                    return redirect(self.get_redirect())
        super().form_post(form)


# return redirect(self.get_redirect())

class AppSecurityManager(SecurityManager):
    registeruserdbview = AppRegisterUserDBView
