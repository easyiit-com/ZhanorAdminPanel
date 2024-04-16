# user_group.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError
from ...models.user_group import UserGroup
import transaction

# list
@view_config(route_name='admin.user.group', permission="admin",renderer='zhanor_admin:templates/admin/user/group/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(UserGroup)
        user_groups = query.order_by(UserGroup.id.desc()).all()
        user_group_dicts = [user_group.to_dict() for user_group in user_groups]
        response_data = {'status': 1, 'message': 'Success', 'data': user_group_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 20
        query = request.dbsession.query(UserGroup)
        total_count = query.count()
        user_group_list = query.order_by(UserGroup.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page
        return {'user_group_list': user_group_list,'current_page': page,'total_pages': pages,}

# add
@view_config(route_name='admin.user.group.add', permission="admin", renderer='zhanor_admin:templates/admin/user/group/add.jinja2')
def add_view(request):
    result = {}
    return {'value': result}

# edit
@view_config(route_name='admin.user.group.edit', renderer='zhanor_admin:templates/admin/user/group/edit.jinja2')
def edit_view(request):
    user_group_id = request.matchdict.get('id')
    result = request.dbsession.query(UserGroup).filter(UserGroup.id == user_group_id).first()
    return {'value': result}

@view_config(route_name='admin.user.group.save', permission="admin", renderer='json', request_method='POST')
def add_or_edit_user_group_view(request):
    try:
        user_group_id = request.POST.get("id")
        user_group = None
        if user_group_id:
            user_group = (
                request.dbsession.query(UserGroup).filter_by(id=user_group_id).one_or_none()
            )
            if user_group is None:
                raise Response(
                    json.dumps({"status": 0, "message": "UserGroup not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            user_group = UserGroup()
            if hasattr(UserGroup, "createtime"):
                user_group.createtime = now(request)

        for field in request.POST.keys():
            clean_field = field.replace("[]", "")
            if clean_field in UserGroup.__table__.columns.keys()and field not in [
                "id",
                "createtime",
                "updatetime",
            ]:
                if field.endswith("[]"):
                    setattr(user_group, clean_field, ','.join(map(str, request.POST.getall(field))))
                else:
                    setattr(user_group, field, request.POST[field])

        if hasattr(UserGroup, "updatetime"):
            user_group.updatetime = now(request)

        if not user_group_id:
            request.dbsession.add(user_group)
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
@view_config(route_name='admin.user.group.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_user_group_view(request):
    data = json.loads(request.body)
    user_group_ids = data.get('ids', [])
    if not user_group_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for user_group_id in user_group_ids:
            user_group = request.dbsession.query(UserGroup).filter(UserGroup.id == user_group_id).one()
            request.dbsession.delete(user_group)  
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
