# admin_group.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError
from ...models.admin_group import AdminGroup
import transaction

# list
@view_config(route_name='admin.admin.group', permission="admin",renderer='zhanor_admin:templates/admin/admin/group/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(AdminGroup)
        admin_groups = query.order_by(AdminGroup.id.desc()).all()
        admin_group_dicts = [admin_group.to_dict() for admin_group in admin_groups]
        response_data = {'status': 1, 'message': 'Success', 'data': admin_group_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 20
        query = request.dbsession.query(AdminGroup)
        total_count = query.count()
        admin_group_list = query.order_by(AdminGroup.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page
        return {'admin_group_list': admin_group_list,'current_page': page,'total_pages': pages,}

# add
@view_config(route_name='admin.admin.group.add', permission="admin", renderer='zhanor_admin:templates/admin/admin/group/add.jinja2')
def add_view(request):
    result = {}
    return {'value': result}

# edit
@view_config(route_name='admin.admin.group.edit', renderer='zhanor_admin:templates/admin/admin/group/edit.jinja2')
def edit_view(request):
    admin_group_id = request.matchdict.get('id')
    result = request.dbsession.query(AdminGroup).filter(AdminGroup.id == admin_group_id).first()
    return {'value': result}

@view_config(route_name='admin.admin.group.save', permission="admin", renderer='json', request_method='POST')
def add_or_edit_admin_group_view(request):
    try:
        admin_group_id = request.POST.get("id")
        admin_group = None
        if admin_group_id:
            admin_group = (
                request.dbsession.query(AdminGroup).filter_by(id=admin_group_id).one_or_none()
            )
            if admin_group is None:
                raise Response(
                    json.dumps({"status": 0, "message": "AdminGroup not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            admin_group = AdminGroup()
            if hasattr(AdminGroup, "createtime"):
                admin_group.createtime = now(request)

        for field in request.POST.keys():
            clean_field = field.replace("[]", "")
            if clean_field in AdminGroup.__table__.columns.keys()and field not in [
                "id",
                "createtime",
                "updatetime",
            ]:
                if field.endswith("[]"):
                    setattr(admin_group, clean_field, ','.join(map(str, request.POST.getall(field))))
                else:
                    setattr(admin_group, field, request.POST[field])

        if hasattr(AdminGroup, "updatetime"):
            admin_group.updatetime = now(request)

        if not admin_group_id:
            request.dbsession.add(admin_group)
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
@view_config(route_name='admin.admin.group.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_admin_group_view(request):
    data = json.loads(request.body)
    admin_group_ids = data.get('ids', [])
    if not admin_group_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for admin_group_id in admin_group_ids:
            admin_group = request.dbsession.query(AdminGroup).filter(AdminGroup.id == admin_group_id).one()
            request.dbsession.delete(admin_group)  
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
