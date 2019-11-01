from flask import (Blueprint,
                   render_template,
                   url_for,
                   redirect)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash

from nokkhum import models
from .. import forms
from .. import oauth2
import datetime

module = Blueprint('accounts', __name__)


@module.route('/login', methods=('GET', 'POST'))
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = forms.accounts.LoginForm()
    if not form.validate_on_submit():
        print(form.errors)
        return render_template('/accounts/login.html',
                               form=form)

    print(form.data)
    user = models.User.objects(
            email=form.email.data).first()
    if not user:
        return render_template('/accounts/login.html',
                               form=form,
                               not_user_error=True)

    if not user.check_password(form.password.data):
        return render_template('/accounts/login.html',
                               form=form,
                               invalid_pass_error=True)

    login_user(user, remember=True)

    return redirect(url_for('dashboard.index'))


@module.route('/register', methods=('GET', 'POST'))
def register():
    form = forms.accounts.RegisterForm()
    if models.User.objects(email=form.email.data).first():
        return render_template('/accounts/register.html', form=form)

    if not form.validate_on_submit():
        return render_template('/accounts/register.html', form=form)

    pass_hash = generate_password_hash(form.password.data, "sha256")
    user = models.User(email=form.email.data,
                       password=pass_hash,
                       organization=form.organization.data,
                       first_name=form.first_name.data,
                       last_name=form.last_name.data,
                       created_date=datetime.datetime.now(),
                       updated_date=datetime.datetime.now())
    user.save()
    return render_template('/accounts/register_success.html', form=form)


@module.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('site.index'))


@module.route('/accounts')
@login_required
def index():

    return render_template('/accounts/index.html')


@module.route('/accounts/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = forms.accounts.Profile(
            obj=current_user,
            )
    if not form.validate_on_submit():
        return render_template('/accounts/edit-profile.html', form=form)

    user = current_user._get_current_object()
    user.first_name = form.first_name.data
    user.last_name = form.last_name.data
    user.organization = form.organization

    user.save()

    return redirect(url_for('accounts.index'))


@module.route('/login-engpsu')
def login_engpsu():
    client = oauth2.oauth2_client
    redirect_uri = url_for('accounts.authorized_engpsu',
                           _external=True)
    response = client.engpsu.authorize_redirect(redirect_uri)
    return response


@module.route('/authorized-engpsu')
def authorized_engpsu():
    client = oauth2.oauth2_client
    try:
        token = client.engpsu.authorize_access_token()
    except Exception as e:
        print(e)
        return redirect(url_for('accounts.login'))

    userinfo_response = client.engpsu.get('userinfo')
    userinfo = userinfo_response.json()

    user = models.User.objects(username=userinfo.get('username')).first()

    if not user:
        user = models.User(
                username=userinfo.get('username'),
                email=userinfo.get('email'),
                first_name=userinfo.get('first_name'),
                last_name=userinfo.get('last_name'),
                status='active')
        user.resources[client.engpsu.name] = userinfo
        # if 'staff_id' in userinfo.keys():
        #     user.roles.append('staff')
        # elif 'student_id' in userinfo.keys():
        #     user.roles.append('student')
        if userinfo['username'].isdigit():
            user.roles.append('student')
        else:
            user.roles.append('staff')

        user.save()

    login_user(user)

    oauth2token = models.OAuth2Token(
            name=client.engpsu.name,
            user=user,
            access_token=token.get('access_token'),
            token_type=token.get('token_type'),
            refresh_token=token.get('refresh_token', None),
            expires=datetime.datetime.fromtimestamp(
                token.get('expires_in'))
            )
    oauth2token.save()

    return redirect(url_for('dashboard.index'))

