# user.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError
from ...models.user_user import UserUser
import transaction

# list
@view_config(route_name='admin.user.user', permission="admin",renderer='zhanor_admin:templates/admin/user/user/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(UserUser)
        users = query.order_by(UserUser.id.desc()).all()
        user_dicts = [user.to_dict() for user in users]
        response_data = {'status': 1, 'message': 'Success', 'data': user_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 20
        query = request.dbsession.query(UserUser)
        total_count = query.count()
        user_list = query.order_by(UserUser.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page
        return {'user_list': user_list,'current_page': page,'total_pages': pages,}

# add
@view_config(route_name='admin.user.user.add', permission="admin", renderer='zhanor_admin:templates/admin/user/user/add.jinja2')
def add_view(request):
    result = {}
    return {'value': result}

# edit
@view_config(route_name='admin.user.user.edit', permission="admin", renderer='zhanor_admin:templates/admin/user/user/edit.jinja2')
def edit_view(request):
    user_id = request.matchdict.get('id')
    result = request.dbsession.query(UserUser).filter(UserUser.id == user_id).first()
    return {'value': result}

@view_config(route_name='admin.user.user.save', permission="admin", renderer='json', request_method='POST')
def add_or_edit_user_view(request):
    try:
        user_id = request.POST.get("id")
        user = None
        if user_id:
            user = (
                request.dbsession.query(UserUser).filter_by(id=user_id).one_or_none()
            )
            if user is None:
                raise Response(
                    json.dumps({"status": 0, "message": "User not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            user = UserUser()
            if hasattr(UserUser, "createtime"):
                user.createtime = now(request)

        for field in request.POST.keys():
            clean_field = field.replace("[]", "")
            if clean_field in UserUser.__table__.columns.keys()and field not in [
                "id",
                "createtime",
                "updatetime",
            ]:
                if field == "password":
                    pw = request.POST["password"]
                    if(pw!=''):
                        user.set_password(pw)
                elif field.endswith("[]"):
                    setattr(user, clean_field, ','.join(map(str, request.POST.getall(field))))
                else:
                    setattr(user, field, request.POST[field])

        if hasattr(UserUser, "updatetime"):
            user.updatetime = now(request)

        if not user_id:
            request.dbsession.add(user)
        transaction.commit()
    except Exception as e:
        request.dbsession.rollback() 
        transaction.abort()
        return Response(
            json.dumps({"status": 0, "message": f"Error{e}", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status = 500
        )
  
    return Response(
            json.dumps({'status': 1, 'message': 'Success', 'data': {}}),
            content_type="application/json",
            charset="utf-8",
            status = 200
        )
# delete
@view_config(route_name='admin.user.user.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_user_view(request):
    data = json.loads(request.body)
    user_ids = data.get('ids', [])
    if not user_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for user_id in user_ids:
            user = request.dbsession.query(UserUser).filter(UserUser.id == user_id).one()
            request.dbsession.delete(user)  
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
