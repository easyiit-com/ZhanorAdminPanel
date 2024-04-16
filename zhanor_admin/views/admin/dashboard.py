from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import (
    HTTPSeeOther,
)
from zhanor_admin.models.admin_user import AdminUser

from ...models.admin_log import AdminLog
import logging

@view_config(route_name='admin', permission="admin")
def admin_view(request):
    next_url = request.route_url(
                    "admin.dashboard"
                )
    return HTTPSeeOther(location=next_url)

@view_config(route_name='admin.dashboard',permission='admin', renderer='zhanor_admin:templates/admin/dashboard.jinja2')
def dashboard_view(request):
    user_id = request.authenticated_userid if(request is not None and hasattr(request,'authenticated_userid')) else None
    logging.info(f'dashboard_view====>request.authenticated_userid====>{user_id}')
    logging.info(f"dashboard_view====>request.effective_principals: %s", request.effective_principals)
    if user_id:
        user = request.dbsession.query(AdminUser).get(user_id)
        logging.info(f'dashboard_view====>user====>{user.name}')
    query = request.dbsession.query(AdminLog)
    admin_logs = query.order_by(AdminLog.id.desc()).limit(4).all()
    admin_log_dicts = [admin_log.to_dict() for admin_log in admin_logs]
    return {
            'admin_log': admin_log_dicts,
            "views":0,
            "registration_count":0,                                
            "online_user_count":0,                                 
            "files":0,                                  
            "images":0,
            "total":0,
        }

