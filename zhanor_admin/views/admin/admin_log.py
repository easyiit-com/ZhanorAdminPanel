# admin_log.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError
from ...models.admin_log import AdminLog
import transaction

# list
@view_config(route_name='admin.admin.log', permission="admin",renderer='zhanor_admin:templates/admin/admin/log/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(AdminLog)
        admin_logs = query.order_by(AdminLog.id.desc()).all()
        admin_log_dicts = [admin_log.to_dict() for admin_log in admin_logs]
        response_data = {'status': 1, 'message': 'Success', 'data': admin_log_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 20
        query = request.dbsession.query(AdminLog)
        total_count = query.count()
        admin_log_list = query.order_by(AdminLog.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page
        return {'admin_log_list': admin_log_list,'current_page': page,'total_pages': pages,}


# delete
@view_config(route_name='admin.admin.log.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_admin_log_view(request):
    data = json.loads(request.body)
    admin_log_ids = data.get('ids', [])
    if not admin_log_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for admin_log_id in admin_log_ids:
            admin_log = request.dbsession.query(AdminLog).filter(AdminLog.id == admin_log_id).one()
            request.dbsession.delete(admin_log)  
        transaction.commit()
    except Exception as e:
        request.dbsession.rollback() 
        transaction.abort()
        return Response(
            json.dumps({"status": 0, "message": f"Error{e}", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    return Response(
        json.dumps({'status': 1, 'message': 'Success', 'data': {}}),
        content_type="application/json",
        charset="utf-8",
        status=200
    )
