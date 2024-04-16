# user_balance_log.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError
from ...models.user_balance_log import UserBalanceLog
import transaction

# list
@view_config(route_name='admin.user.balance.log', permission="admin",renderer='zhanor_admin:templates/admin/user/balance_log/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(UserBalanceLog)
        user_balance_logs = query.order_by(UserBalanceLog.id.desc()).all()
        user_balance_log_dicts = [user_balance_log.to_dict() for user_balance_log in user_balance_logs]
        response_data = {'status': 1, 'message': 'Success', 'data': user_balance_log_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 20
        query = request.dbsession.query(UserBalanceLog)
        total_count = query.count()
        user_balance_log_list = query.order_by(UserBalanceLog.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page
        return {'user_balance_log_list': user_balance_log_list,'current_page': page,'total_pages': pages,}
 
 
@view_config(route_name='admin.user.balance.log.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_user_balance_log_view(request):
    data = json.loads(request.body)
    user_balance_log_ids = data.get('ids', [])
    if not user_balance_log_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for user_balance_log_id in user_balance_log_ids:
            user_balance_log = request.dbsession.query(UserBalanceLog).filter(UserBalanceLog.id == user_balance_log_id).one()
            request.dbsession.delete(user_balance_log)  
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
