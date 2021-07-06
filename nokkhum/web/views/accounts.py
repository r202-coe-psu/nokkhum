from flask import (
    Blueprint,
    render_template,
    url_for,
    redirect,
    current_app,
    make_response,
)
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from flask_principal import Identity, identity_changed, AnonymousIdentity

from nokkhum import models
from .. import forms
from .. import oauth2
import datetime

module = Blueprint("accounts", __name__)


@module.route("/login", methods=("GET", "POST"))
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    return render_template("/accounts/login.html")


@module.route("/logout")
@login_required
def logout():
    logout_user()
    yesterday = datetime.datetime.now() + datetime.timedelta(days=-1)
    response = make_response(redirect(url_for("site.index")))
    response.set_cookie("remember_token", "", expires=yesterday)
    identity_changed.send(
        current_app._get_current_object(), identity=AnonymousIdentity()
    )
    return response


@module.route("/accounts")
@login_required
def index():

    return render_template("/accounts/index.html")


@module.route("/accounts/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = forms.accounts.Profile(
        obj=current_user,
    )
    if not form.validate_on_submit():
        return render_template("/accounts/edit-profile.html", form=form)

    user = current_user._get_current_object()
    user.first_name = form.first_name.data
    user.last_name = form.last_name.data
    user.organization = form.organization.data

    user.save()

    return redirect(url_for("accounts.index"))


@module.route("/login-engpsu")
def login_engpsu():
    client = oauth2.oauth2_client
    redirect_uri = url_for("accounts.authorized_engpsu", _external=True)
    response = client.engpsu.authorize_redirect(redirect_uri)
    return response


@module.route("/authorized-engpsu")
def authorized_engpsu():
    client = oauth2.oauth2_client
    try:
        token = client.engpsu.authorize_access_token()
    except Exception as e:
        print(e)
        return redirect(url_for("accounts.login"))

    userinfo_response = client.engpsu.get("userinfo")
    userinfo = userinfo_response.json()

    user = models.User.objects(username=userinfo.get("username")).first()

    if not user:
        user = models.User(
            username=userinfo.get("username"),
            email=userinfo.get("email"),
            first_name=userinfo.get("first_name"),
            last_name=userinfo.get("last_name"),
            status="active",
        )
        user.resources[client.engpsu.name] = userinfo
        # if 'staff_id' in userinfo.keys():
        #     user.roles.append('staff')
        # elif 'student_id' in userinfo.keys():
        #     user.roles.append('student')
        if userinfo["username"].isdigit():
            user.roles.append("student")
        else:
            user.roles.append("staff")

        user.save()

    login_user(user, remember=True)

    oauth2token = models.OAuth2Token(
        name=client.engpsu.name,
        user=user,
        access_token=token.get("access_token"),
        token_type=token.get("token_type"),
        refresh_token=token.get("refresh_token", None),
        expires=datetime.datetime.fromtimestamp(token.get("expires_in")),
    )
    oauth2token.save()
    identity_changed.send(
        current_app._get_current_object(), identity=Identity(user.roles)
    )

    return redirect(url_for("dashboard.index"))
