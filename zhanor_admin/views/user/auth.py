from datetime import datetime, timedelta
import json
import jwt
from pyramid.csrf import new_csrf_token
from sqlalchemy import or_

from pyramid.httpexceptions import HTTPFound, HTTPUnauthorized
from pyramid.security import (
    remember,
    forget,
)
from pyramid.view import (
    view_config,
)
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.response import Response
from zhanor_admin.common.defs import check_ems_code, generate_ems_code, ip, now
from zhanor_admin.common.mail import MailService
from zhanor_admin.models.user_user import UserUser
from zhanor_admin.subscribers import _
import transaction

@view_config(
    route_name="user.auth.login",
    request_method="GET",
    permission=NO_PERMISSION_REQUIRED,
    renderer="zhanor_admin:templates/user/login.jinja2",
)
def login_view(request):
    user = getattr(request, "user", None)
    if user:
        location = request.route_url("user.dashboard")
        return HTTPFound(location=location)
    return {"title": "user login"}


@view_config(route_name="user.auth.login", renderer="json", request_method="POST")
def login(request):
    settings = request.registry.settings
    referrer = "/user/dashboard"
    came_from = request.params.get("came_from", referrer)
    email = request.params.get("email")
    password = request.params.get("password")
    user = request.dbsession.query(UserUser).filter(UserUser.email == email).first()
    if user is not None:
        if user.check_password(password):
            new_csrf_token(request)
            user.successions = user.successions + 1
            user.maxsuccessions = user.maxsuccessions + 1
            user.logintime = now(request)
            user.loginip = ip(request)
            headers = remember(request, user.id, role="user")
            payload = {
                "userid": user.id,
                "role": "user",
                "exp": now(request) + timedelta(days=1),
            }
            jwt_auth_secret = settings.get("jwt.secret", "zhanor_jin")
            token = jwt.encode(payload, jwt_auth_secret, algorithm="HS256")
            response_data = {"status": 1, "token": token, "message": _("Login Success")}
            response_body = json.dumps(response_data)
            return Response(
                body=response_body,
                content_type="application/json",
                charset="utf-8",
                status=200,
                headerlist=headers,
            )
        else:
            user.loginfailure = user.loginfailure + 1
            response_data = {"status": 0, "message": _("Login failed, Some Error")}
            return HTTPUnauthorized(
                json_body=response_data,
                content_type="application/json",
                charset="utf-8",
            )
    else:
        response_data = {"status": 0, "message": _("Login failed, Some Error")}
        return HTTPUnauthorized(
            json_body=response_data, content_type="application/json", charset="utf-8"
        )


@view_config(
    route_name="user.auth.register",
    request_method="GET",
    permission=NO_PERMISSION_REQUIRED,
    renderer="zhanor_admin:templates/user/register.jinja2",
)
def register_view(request):
    user = getattr(request, "user", None)
    if user:
        location = request.route_url("user.dashboard")
        return HTTPFound(location=location)
    return {"title": _("User Register"), "value": {}}


@view_config(route_name="user.auth.register", renderer="json", request_method="POST")
def register(request):
    email = request.params.get("email")
    mobile = request.params.get("mobile")
    name = request.params.get("name")
    user = (
        request.dbsession.query(UserUser)
        .filter(or_(UserUser.email == email, UserUser.name == name, UserUser.mobile == mobile))
        .first()
    )

    if user is not None:
        return Response(
            json.dumps(
                {
                    "status": 0,
                    "message": _("The email or name or mobile you entered is already registered"),
                    "data": {},
                }
            ),
            content_type="application/json",
            charset="utf-8",
            status=500,
        )
    else:
        try:
            user = UserUser()
            for field in request.POST.keys():
                if field == "password":
                    pw = request.POST["password"]
                    if pw != "":
                        user.set_password(pw)
                else:
                    setattr(user, field, request.POST[field])
            user.user_group_id = 1
            user.avatar = "static/img/avator.png"
            user.level = 0
            user.gender = "male"
            user.bio = ""
            user.balance = 0
            user.score = 0
            user.successions = 0
            user.maxsuccessions = 0
            user.prevtime = now(request)
            user.logintime = now(request)
            user.loginip = ip(request)
            user.loginfailure = "0"
            user.joinip = ip(request)
            user.createtime = now(request)
            user.updatetime = now(request)
            user.verification = "0"
            user.token = ""
            user.status = "normal"
            request.dbsession.add(user)
            transaction.commit()
        except Exception as e:
            request.dbsession.rollback()
            transaction.abort()
            return Response(
                json.dumps({"status": 0, "message": f"Error{e}", "data": {}}),
                content_type="application/json",
                charset="utf-8",
                status=500,
            )

        return Response(
            json.dumps({"status": 1, "message": _("Success"), "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=200,
        )


@view_config(
    route_name="user.auth.forgot.password",
    request_method="GET",
    permission=NO_PERMISSION_REQUIRED,
    renderer="zhanor_admin:templates/user/forgot_password.jinja2",
)
def forgot_password_view(request):
    user = getattr(request, "user", None)
    if user:
        location = request.route_url("user.dashboard")
        return HTTPFound(location=location)
    return {"title": _("User Forgot Password")}


@view_config(
    route_name="user.auth.forgot.password", renderer="json", request_method="POST"
)
def forgot_password(request):
    email = request.params.get("email")
    password = request.params.get("password")
    code = request.params.get("code")

    user = request.dbsession.query(UserUser).filter(UserUser.email == email).first()
    if user is not None:
        check_return_code = check_ems_code(request, "forgot_password", email, code)
        if check_return_code == "-1":
            return Response(
                json.dumps(
                    {
                        "status": 0,
                        "message": _("The verification code has expired."),
                        "data": {},
                    }
                ),
                content_type="application/json",
                charset="utf-8",
                status=500,
            )
        elif check_return_code == "-3":
            return Response(
                json.dumps(
                    {
                        "status": 0,
                        "message": _("Max attempts exceeded. Account temporarily locked. Retry in 30 minutes."),
                        "data": {},
                    }
                ),
                content_type="application/json",
                charset="utf-8",
                status=500,
            )
        elif check_return_code == "0":
            return Response(
                json.dumps(
                    {
                        "status": 0,
                        "message": _("Verification code is incorrect."),
                        "data": {},
                    }
                ),
                content_type="application/json",
                charset="utf-8",
                status=500,
            )
        else:
            if password != "":
                user.set_password(password)
            response_data = {"status": 1, "message": "Change Password Success"}
            response_body = json.dumps(response_data)
            return Response(
                body=response_body,
                content_type="application/json",
                charset="utf-8",
                status=200,
            )
    else:
        response_data = {"status": 0, "message": _("Some Error")}
        return HTTPUnauthorized(
            json_body=response_data, content_type="application/json", charset="utf-8"
        )


@view_config(route_name="user.auth.send.mail", renderer="json", request_method="POST")
def send_mail(request):
    settings = request.registry.settings
    email = request.params.get("email")
    user = request.dbsession.query(UserUser).filter(UserUser.email == email).first()
    if user is not None:
        smtp_host = settings.get("smtp_host", "smtp.qq.com")
        smtp_port = settings.get("smtp_port", "587")
        smtp_username = settings.get("smtp_username", "")
        smtp_password = settings.get("smtp_password", "")
        mail_service = MailService(
            smtp_host, smtp_port, smtp_username, smtp_password
        )
        code = generate_ems_code(request, "forgot_password", email)
        if mail_service.send_email(
            "Verification Code",
            f"Your verification code is: {code}",
            smtp_username,
            [email],
        ):
            return Response(
                body=json.dumps({"status": 1, "message": "Send Success"}),
                content_type="application/json",
                charset="utf-8",
                status=200,
            )
        else:
            return Response(
                json.dumps(
                    {
                        "status": 0,
                        "message": _("Send Verification Code Failed"),
                        "data": {},
                    }
                ),
                content_type="application/json",
                charset="utf-8",
                status=500,
            )
    else:
        response_data = {
            "status": 0,
            "message": _(
                "Send Verification Code Failed, This email address is not valid"
            ),
        }
        return HTTPUnauthorized(
            json_body=response_data, content_type="application/json", charset="utf-8"
        )


@view_config(
    route_name="user.auth.logout",
    permission="user",
    renderer="json",
    request_method="POST",
)
def logout_view(request):
    headers = forget(request, role="user")
    response_data = {"status": 1, "message": _("Logout successful")}
    response_body = json.dumps(response_data)

    response = Response(
        body=response_body,
        content_type="application/json",
        charset="utf-8",
        status=200,
        headerlist=headers,
    )
    return response
    return {}
