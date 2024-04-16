import json
from pyramid.csrf import new_csrf_token
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
from zhanor_admin.common.defs import now
from zhanor_admin.models.admin_user import AdminUser

@view_config(
    route_name="admin.auth.login",
    request_method="GET",
    permission=NO_PERMISSION_REQUIRED,
    renderer="zhanor_admin:templates/admin/login.jinja2",
)
def login_view(request):
    user = getattr(request, "admin", None)
    if user:
        location = request.route_url("admin.dashboard")
        return HTTPFound(location=location)
    return {"title": "login"}


@view_config(route_name="admin.auth.login", renderer="json", request_method="POST")
def login(request):
    
    request.session.flash('User name and password is required')
    
    settings = request.registry.settings
    referrer = "/admin/dashboard"
    came_from = request.params.get("came_from", referrer)
    email = request.params.get("email")
    password = request.params.get("password")
    user = request.dbsession.query(AdminUser).filter(AdminUser.email == email).first()
    if user is not None and user.check_password(password):
        new_csrf_token(request)
        headers = remember(request, user.id, role="admin")
        response_data = {"status": 1, "token": None, "message": "Login Success"}
        response_body = json.dumps(response_data)
        return Response(
            body=response_body,
            content_type="application/json",
            charset="utf-8",
            status=200,
            headerlist=headers,
        )
    else:
        # user.set_password(password)
        response_data = {"status": 0, "message": "Login failed, Some Error"}
        return HTTPUnauthorized(
            json_body=response_data, content_type="application/json", charset="utf-8"
        )

    # return dict(
    #     message=message,
    #     url=request.route_url('admin.login'),
    #     next_url='next_url',
    #     login=login,
    # )


@view_config(route_name="auth.logout", permission="admin", renderer="json", request_method="POST")
def logout_view(request):
    # request.security_policy.forget(request)
    headers = forget(request,role="admin")
    response_data = {'status': 1, 'message': 'Logout successful'}
    response_body = json.dumps(response_data)

    response = Response(
        body=response_body,
        content_type="application/json",
        charset="utf-8",
        status=200,
        headerlist=headers
    )
    return response
    return {}
