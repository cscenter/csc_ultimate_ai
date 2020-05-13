import logging

from flask import flash, redirect, url_for, current_app
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

log = logging.getLogger(__name__)


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
        validators=[DataRequired(),Length(min=3, max=25)],
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

    # Workaround
    def send_email(self, register_user):
        try:
            from flask_mail import Mail, Message
        except Exception:
            log.error("Install Flask-Mail to use User registration")
            return False
        app = self.appbuilder.get_app
        mail = Mail(app)
        msg = Message()
        msg.subject = self.email_subject
        # !WARNING! Workaround
        # I can't find how to configure Flask for case when it works on localhost and use nginx proxy with another host.
        # url_for - makes url with localhost but another host required.
        external_host = app.config['EXTERNAL_APP_HOST']
        hash = register_user.registration_hash
        url = f"http://{external_host}/register/activation/{hash}"

        msg.html = self.render_template(
            self.email_template,
            url=url,
            username=register_user.username,
            first_name=register_user.first_name,
            last_name=register_user.last_name,
        )
        msg.recipients = [register_user.email]
        try:
            mail.send(msg)
        except Exception as e:
            log.error("Send email exception: {0}".format(str(e)))
            return False
        return True


# return redirect(self.get_redirect())

class AppSecurityManager(SecurityManager):
    registeruserdbview = AppRegisterUserDBView
