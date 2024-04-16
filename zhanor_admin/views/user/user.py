import json
from pyramid.httpexceptions import HTTPSeeOther, HTTPFound, HTTPUnauthorized
from pyramid.view import (
    view_config,
)
from pyramid.response import Response
from zhanor_admin.common.defs import now
from zhanor_admin.models.user_user import UserUser
import transaction

from zhanor_admin.models.user_balance_log import UserBalanceLog
from zhanor_admin.models.user_score_log import UserScoreLog


@view_config(route_name="user", request_method="GET")
def user_view(request):
    user = getattr(request, "user", None)
    if user:
        location = request.route_url("user.dashboard")
        return HTTPFound(location=location)


@view_config(
    route_name="user.profile",
    permission="user",
    renderer="zhanor_admin:templates/user/profile.jinja2",
)
def profile_view(request):
    user_id =  request.user.id
    result = request.dbsession.query(UserUser).filter(UserUser.id == user_id).first()
    return {"value": result}


@view_config(
    route_name="user.profile.save",
    permission="user",
    renderer="json",
    request_method="POST",
)
def profile_save_view(request):
    try:
        user_id =  request.user.id
        user = None
        if user_id:
            user = request.dbsession.query(User).filter_by(id=user_id).one_or_none()
            if user is None:
                raise Response(
                    json.dumps({"status": 0, "message": "User not found.", "data": {}}),
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
        if hasattr(UserUser, "updatetime"):
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
    
    
    
@view_config(
    route_name="user.balance.log",
    permission="user",
    renderer="zhanor_admin:templates/user/balance_log.jinja2",
)
def balance_log_view(request):
    user_id =  request.user.id
    page = int(request.GET.get('page', 1))
    per_page = 20
    query = request.dbsession.query(UserBalanceLog)
    total_count = query.count()
    user_balance_log_list = query.filter_by(user_id=user_id).order_by(UserBalanceLog.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    pages = (total_count + per_page - 1) // per_page
    return {'user_balance_log_list': user_balance_log_list,'current_page': page,'total_pages': pages,}



@view_config(
    route_name="user.score.log",
    permission="user",
    renderer="zhanor_admin:templates/user/score_log.jinja2",
)
def scroe_log_view(request):
    user_id =  request.user.id
    page = int(request.GET.get('page', 1))
    per_page = 20
    query = request.dbsession.query(UserScoreLog)
    total_count = query.count()
    user_score_log_list = query.filter_by(user_id=user_id).order_by(UserScoreLog.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    pages = (total_count + per_page - 1) // per_page
    return {'user_score_log_list': user_score_log_list,'current_page': page,'total_pages': pages,}