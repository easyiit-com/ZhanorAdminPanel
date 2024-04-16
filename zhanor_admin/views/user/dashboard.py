from pyramid.view import view_config
from pyramid.httpexceptions import HTTPFound

from zhanor_admin.models.user_user import UserUser

# from ...models.user_log import UserLog
import logging

@view_config(route_name='user.dashboard', permission='user', renderer='zhanor_admin:templates/user/dashboard.jinja2')
def dashboard_view(request):
    user_id = request.authenticated_userid if(request is not None and hasattr(request,'authenticated_userid')) else None
    logging.info(f'dashboard_view====>request.authenticated_userid====>{user_id}')
    return {
            'balance_log': {},
            "balance":0,
            "score":0,                                
            "credits":0,                                 
            "files":0,                                  
            "images":0,
            "total":0,
        }

