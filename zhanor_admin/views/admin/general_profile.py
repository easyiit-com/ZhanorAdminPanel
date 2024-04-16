# general_config.py
import json
from pyramid.view import view_config
from pyramid.response import Response
import transaction
import logging

from zhanor_admin.common.defs import now
from zhanor_admin.models.admin_user import AdminUser


# list
@view_config(
    route_name="admin.general.profile", permission='admin', renderer="zhanor_admin:templates/admin/general/profile.jinja2"
)
def profile_view(request):
    admin_id = request.admin.id
    result = request.dbsession.query(AdminUser).filter(AdminUser.id == admin_id).first()
    return {'value': result} 

@view_config(route_name="admin.general.profile.save", permission='admin', renderer="json", request_method="POST")
def profile_save_view(request):
    try:
        user_id =  request.admin.id
        user = None
        if user_id:
            user = request.dbsession.query(AdminUser).filter_by(id=user_id).one_or_none()
            if user is None:
                raise Response(
                    json.dumps({"status": 0, "message": "AdminUser not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )

        for field in request.POST.keys():
            if field == "password":
                pw = request.POST["password"]
                if(pw!=''):
                    user.set_password(pw)
            else:
               setattr(user, field, request.POST[field])
        if hasattr(AdminUser, "updatetime"):
            user.updatetime = now(request)
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
        json.dumps({"status": 1, "message": "Success", "data": {}}),
        content_type="application/json",
        charset="utf-8",
        status=200,
    )