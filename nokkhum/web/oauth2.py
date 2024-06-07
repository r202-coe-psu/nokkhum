from flask import g, config, session, redirect, url_for, current_app
from flask_login import current_user, login_user
from authlib.integrations.flask_client import OAuth
import requests
import datetime

from .. import models
import mongoengine as me


def fetch_token(name):
    token = models.OAuth2Token.objects(
        name=name, user=current_user._get_current_object()
    ).first()
    return token.to_dict()


def update_token(name, token):
    item = models.OAuth2Token(
        name=name, user=current_user._get_current_object()
    ).first()
    item.token_type = token.get("token_type", "Bearer")
    item.access_token = token.get("access_token")
    item.refresh_token = token.get("refresh_token")
    item.expires = datetime.datetime.utcfromtimestamp(token.get("expires_at"))

    item.save()
    return item


oauth2_client = OAuth()


def create_user_google(user_info):
    user = models.User(
        username=user_info.get("email"),
        picture_url=user_info.get("picture"),
        email=user_info.get("email"),
        first_name=user_info.get("given_name"),
        last_name=user_info.get("family_name"),
        status="active",
    )
    user.save()
    return user


def create_user_line(user_info):
    name = user_info.get("name", "")
    names = ["", ""]
    if name:
        names = name.split(" ")
        if len(names) < 2:
            names.append("")

    user = models.User(
        username=user_info.get("email", name),
        subid=user_info.get("sub"),
        picture_url=user_info.get("picture"),
        email=user_info.get("email", ""),
        first_name=names[0],
        last_name=names[1],
        status="active",
    )
    user.save()
    return user


def create_user_facebook(user_info):
    user = models.User(
        username=user_info.get("email"),
        picture_url=f"http://graph.facebook.com/{user_info.get('sub')}/picture?type=large",
        email=user_info.get("email"),
        first_name=user_info.get("first_name"),
        last_name=user_info.get("last_name"),
        status="active",
    )
    user.save()
    return user


def create_user_engpsu(user_info):
    user = models.User(
        username=user_info.get("username"),
        email=user_info.get("email"),
        first_name=user_info.get("first_name").title(),
        last_name=user_info.get("last_name").title(),
        status="active",
    )
    # user.resources[client.engpsu.name] = user_info
    if user_info["username"].isdigit():
        user.roles.append("student")
    else:
        user.roles.append("staff")

    user.save()
    return user


def create_user_psu(user_info, user=None):
    if not user:
        user = models.User(
            username=user_info.get("username"),
            email=user_info.get("email"),
            first_name=user_info.get("first_name").title(),
            last_name=user_info.get("last_name").title(),
            first_name_th=user_info.get("first_name_th", ""),
            last_name_th=user_info.get("last_name_th", ""),
            # system_id=user_info.get("psu_id", user_info.get("username")),
            status="active",
        )
    else:
        user.first_name = user_info.get("first_name", "").title()
        user.last_name = user_info.get("last_name", "").title()
        user.first_name_th = user_info.get("first_name_th", "")
        user.last_name_th = user_info.get("last_name_th", "")
        user.email = user_info.get("email")
        user.username = user_info.get("username")

    user.save()

    if user_info["username"].isdigit():
        if "student" not in user.roles:
            user.roles.append("student")
    else:
        if "staff" not in user.roles:
            user.roles.append("staff")

    user.save()
    return user


def get_user_info(remote, token):
    userinfo = dict()

    if remote.name == "google":
        # resp = remote.get("userinfo")
        # return resp.json()
        # print(token)
        userinfo = token["userinfo"]
    elif remote.name == "facebook":
        USERINFO_FIELDS = [
            "id",
            "name",
            "first_name",
            "middle_name",
            "last_name",
            "email",
            "website",
            "gender",
            "locale",
        ]
        USERINFO_ENDPOINT = "me?fields=" + ",".join(USERINFO_FIELDS)
        resp = remote.get(USERINFO_ENDPOINT)
        userinfo = resp.json()
    elif remote.name == "line":
        id_token = token.get("id_token")
        # print("id_token", id_token)
        resp = requests.post(
            "https://api.line.me/oauth2/v2.1/verify",
            data={"id_token": str(id_token), "client_id": remote.client_id},
        )

        # resp = requests.get(
        #     "https://api.line.me/v2/profile",
        #     headers={"Authorization": f"Bearer {token.get('access_token')}"},
        # )

        userinfo = resp.json()
    elif remote.name == "engpsu":
        userinfo_response = remote.get("userinfo")
        userinfo = userinfo_response.json()

    elif remote.name == "psu":
        AUTHLIB_SSL_VERIFY = current_app.config.get("AUTHLIB_SSL_VERIFY_PSU", False)
        # token = remote.authorize_access_token(verify=AUTHLIB_SSL_VERIFY)
        userinfo = token.get("userinfo")
        if not userinfo:
            userinfo_response = remote.get("userinfo", verify=AUTHLIB_SSL_VERIFY)
            userinfo = userinfo_response.json()

    return userinfo


def handle_authorized_oauth2(remote, token):
    # print(remote.name)
    # print(token)

    user_info = get_user_info(remote, token)

    user = None
    if remote.name in ["engpsu", "psu"]:
        user = models.User.objects(username=user_info.get("username")).first()
    elif "email" in user_info and user_info["email"]:
        user = models.User.objects(me.Q(email=user_info.get("email"))).first()
    elif "sub" in user_info:
        user = models.User.objects(subid=user_info.get("sub")).first()

    print(">>>", user)
    if not user:
        if remote.name == "google":
            user = create_user_google(user_info)
        elif remote.name == "facebook":
            user = create_user_facebook(user_info)
        elif remote.name == "line":
            user = create_user_line(user_info)
        elif remote.name == "engpsu":
            user = create_user_engpsu(user_info)
        elif remote.name == "psu":
            user = create_user_psu(user_info)

    login_user(user)

    user.last_login_date = datetime.datetime.now()
    user.resources[remote.name] = user_info
    user.save()

    if token:
        oauth2token = models.OAuth2Token(
            name=remote.name,
            user=user,
            access_token=token.get("access_token"),
            token_type=token.get("token_type"),
            refresh_token=token.get("refresh_token", None),
            expires=datetime.datetime.utcfromtimestamp(token.get("expires_in")),
        )
        oauth2token.save()

    next_uri = session.get("next", None)
    if next_uri:
        session.pop("next")
        return redirect(next_uri)
    return redirect(url_for("dashboard.index"))


def handle_authorize(remote, token, user_info):
    if not user_info:
        return redirect(url_for("accounts.login"))

    user = models.User.objects(
        me.Q(username=user_info.get("name")) | me.Q(email=user_info.get("email"))
    ).first()
    if not user:
        user = models.User(
            username=user_info.get("name"),
            email=user_info.get("email"),
            first_name=user_info.get("given_name", ""),
            last_name=user_info.get("family_name", ""),
            status="active",
        )
        user.resources[remote.name] = user_info
        email = user_info.get("email")
        if email[: email.find("@")].isdigit():
            user.roles.append("student")
        user.save()

    login_user(user)

    if token:
        oauth2token = models.OAuth2Token(
            name=remote.name,
            user=user,
            access_token=token.get("access_token"),
            token_type=token.get("token_type"),
            refresh_token=token.get("refresh_token", None),
            expires=datetime.datetime.utcfromtimestamp(token.get("expires_in")),
        )
        oauth2token.save()
    next_uri = session.get("next", None)
    if next_uri:
        session.pop("next")
        return redirect(next_uri)
    return redirect(url_for("dashboard.index"))


def init_oauth(app):
    oauth2_client.init_app(app, fetch_token=fetch_token, update_token=update_token)

    # oauth2_client.register("engpsu")
    oauth2_client.register("psu")
    # oauth2_client.register("google")
