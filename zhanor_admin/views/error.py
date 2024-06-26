import json
import logging
from pyramid.view import (
    exception_view_config,
    forbidden_view_config,
    notfound_view_config,
)
from pyramid.exceptions import BadCSRFToken
from pyramid.httpexceptions import (
    HTTPSeeOther,
)
from pyramid.response import Response


@exception_view_config(BadCSRFToken)
def csrf_validation_failure(exc, request):
    response_data = {
        "status": 0,
        "message": "CSRF token missing or incorrect.",
        "data": {},
    }
    return Response(
        json.dumps(response_data),
        content_type="application/json",
        charset="utf-8",
        status=400,
    )


@forbidden_view_config(renderer="zhanor_admin:templates/403.jinja2")
def forbidden_view(exc, request):
    if request.path.startswith("/admin"):
        if request.method in ("POST", "DELETE"):
            return Response(
                json.dumps({"status": 0, "message": f"Need Login.", "data": {}}),
                content_type="application/json",
                charset="utf-8",
                status=403,
            )
        next_url = request.route_url("admin.auth.login")
        return HTTPSeeOther(location=next_url)
    else:
        if request.method in ("POST", "DELETE"):
            return Response(
                json.dumps({"status": 0, "message": f"User Need Login.", "data": {}}),
                content_type="application/json",
                charset="utf-8",
                status=403,
            )
        next_url = request.route_url("user.auth.login")
        return HTTPSeeOther(location=next_url)


@notfound_view_config(renderer="zhanor_admin:templates/404.jinja2")
def notfound_view(request):
    if request.matched_route is not None:
        route_name = request.matched_route.name
    request.response.status = 404
    if request.method in ("POST", "DELETE"):
        return Response(
            json.dumps({"status": 0, "message": f"Page Not Found.", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=404,
        )
    return {"route_name": route_name}
