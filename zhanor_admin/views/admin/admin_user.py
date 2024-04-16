# admin.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError
from ...models.admin_user import AdminUser
import transaction


 
# list
@view_config(route_name='admin.admin.user', permission="admin",renderer='zhanor_admin:templates/admin/admin/user/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(AdminUser)
        admins = query.order_by(AdminUser.id.desc()).all()
        admin_dicts = [admin.to_dict() for admin in admins]
        response_data = {'status': 1, 'message': 'Success', 'data': admin_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8", 
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 20
        query = request.dbsession.query(AdminUser)
        total_count = query.count()
        admin_list = query.order_by(AdminUser.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page
        return {'admin_list': admin_list,'current_page': page,'total_pages': pages,}

# add
@view_config(route_name='admin.admin.user.add', permission="admin", renderer='zhanor_admin:templates/admin/admin/user/add.jinja2')
def add_view(request):
    result = {}
    return {'value': result}

# edit
@view_config(route_name='admin.admin.user.edit',permission="admin", renderer='zhanor_admin:templates/admin/admin/user/edit.jinja2')
def edit_view(request):
    admin_id = request.matchdict.get('id')
    result = request.dbsession.query(AdminUser).filter(AdminUser.id == admin_id).first()
    return {'value': result}

@view_config(route_name='admin.admin.user.save', permission="admin", renderer='json', request_method='POST')
def add_or_edit_admin_view(request):
    try:
        admin_id = request.POST.get("id")
        admin = None
        if admin_id:
            admin = (
                request.dbsession.query(AdminUser).filter_by(id=admin_id).one_or_none()
            )
            if admin is None:
                raise Response(
                    json.dumps({"status": 0, "message": "AdminUser not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            admin = AdminUser()
            if hasattr(AdminUser, "createtime"):
                admin.createtime = now(request)

        for field in request.POST.keys():
            clean_field = field.replace("[]", "")
            if clean_field in AdminUser.__table__.columns.keys()and field not in [
                "id",
                "createtime",
                "updatetime",
            ]:
                if field == "password":
                    pw = request.POST["password"]
                    if(pw!=''):
                        admin.set_password(pw)
                elif field.endswith("[]"):
                    setattr(admin, clean_field, ','.join(map(str, request.POST.getall(field))))
                else:
                    setattr(admin, field, request.POST[field])

        if hasattr(AdminUser, "updatetime"):
            admin.updatetime = now(request)

        if not admin_id:
            request.dbsession.add(admin)
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
@view_config(route_name='admin.admin.user.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_admin_view(request):
    data = json.loads(request.body)
    admin_ids = data.get('ids', [])
    if not admin_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for admin_id in admin_ids:
            admin = request.dbsession.query(AdminUser).filter(AdminUser.id == admin_id).one()
            request.dbsession.delete(admin)  
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
