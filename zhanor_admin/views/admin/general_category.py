# category.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError
from ...models.general_category import GeneralCategory
import transaction

# list
@view_config(route_name='admin.general.category', permission="admin",renderer='zhanor_admin:templates/admin/general/category/index.jinja2')
def index_view(request): 
    if request.is_xhr:
        query = request.dbsession.query(GeneralCategory)
        categorys = query.order_by(GeneralCategory.id.desc()).all()
        category_dicts = [category.to_dict() for category in categorys]
        response_data = {'status': 1, 'message': 'Success', 'data': category_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 20
        query = request.dbsession.query(GeneralCategory)
        total_count = query.count()
        category_list = query.order_by(GeneralCategory.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page
        return {'category_list': category_list,'current_page': page,'total_pages': pages,}

# add
@view_config(route_name='admin.general.category.add', permission="admin", renderer='zhanor_admin:templates/admin/general/category/add.jinja2')
def add_view(request):
    result = {}
    return {'value': result}

# edit
@view_config(route_name='admin.general.category.edit', renderer='zhanor_admin:templates/admin/general/category/edit.jinja2')
def edit_view(request):
    category_id = request.matchdict.get('id')
    result = request.dbsession.query(GeneralCategory).filter(GeneralCategory.id == category_id).first()
    return {'value': result}

@view_config(route_name='admin.general.category.save', permission="admin", renderer='json', request_method='POST')
def add_or_edit_category_view(request):
    try:
        category_id = request.POST.get("id")
        category = None
        if category_id:
            category = (
                request.dbsession.query(GeneralCategory).filter_by(id=category_id).one_or_none()
            )
            if category is None:
                raise Response(
                    json.dumps({"status": 0, "message": "GeneralCategory not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            category = GeneralCategory()
            if hasattr(GeneralCategory, "createtime"):
                category.createtime = now(request)

        for field in request.POST.keys():
            clean_field = field.replace("[]", "")
            if clean_field in GeneralCategory.__table__.columns.keys()and field not in [
                "id",
                "createtime",
                "updatetime",
            ]:
                if field.endswith("[]"):
                    setattr(category, clean_field, ','.join(map(str, request.POST.getall(field))))
                else:
                    setattr(category, field, request.POST[field])

        if hasattr(GeneralCategory, "updatetime"):
            category.updatetime = now(request)

        if not category_id:
            request.dbsession.add(category)
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
@view_config(route_name='admin.general.category.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_category_view(request):
    data = json.loads(request.body)
    category_ids = data.get('ids', [])
    if not category_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for category_id in category_ids:
            category = request.dbsession.query(GeneralCategory).filter(GeneralCategory.id == category_id).one()
            request.dbsession.delete(category)  
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
