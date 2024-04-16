# admin_rule.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError

from zhanor_admin.common.tree import Tree
from ...models.admin_rule import AdminRule
import transaction

# list
@view_config(route_name='admin.admin.rule', permission="admin",renderer='zhanor_admin:templates/admin/admin/rule/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(AdminRule)
        admin_rules = query.order_by(AdminRule.id.desc()).all()
        admin_rule_dicts = [admin_rule.to_dict() for admin_rule in admin_rules]
        response_data = {'status': 1, 'message': 'Success', 'data': admin_rule_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 2000
        query = request.dbsession.query(AdminRule)
        total_count = query.count()
        admin_rule_list = query.order_by(AdminRule.id.asc()).offset((page - 1) * per_page).limit(per_page).all()
        options = {
            'pidname': 'pid',
            'nbsp': '&nbsp;&nbsp;&nbsp;&nbsp;',
            'icon' : ['&nbsp&nbsp&nbsp&nbsp', '├', '└']
        }
        data = [{
                    'id': rule.id,
                    'type': rule.type,
                    'pid': rule.pid,
                    'name': rule.name,
                    'title': rule.title,
                    'icon': rule.icon,
                    'weigh': rule.weigh,
                    'createtime': rule.createtime,
                    'updatetime': rule.updatetime,
                    'status': rule.status
                } for rule in admin_rule_list]
        tree = Tree(options)
        tree.init(data)
        admin_rule_tree_list = tree.getTreeList(tree.getTreeArray(0),field='title')
        pages = (total_count + per_page - 1) // per_page
        return {'admin_rule_list': admin_rule_tree_list,'current_page': page,'total_pages': pages,}

# add
@view_config(route_name='admin.admin.rule.add', permission="admin", renderer='zhanor_admin:templates/admin/admin/rule/add.jinja2')
def add_view(request):
    query = request.dbsession.query(AdminRule)
    admin_rules_menu = query.filter(AdminRule.type == 'menu').all()
    result_instance = AdminRule()
    result_instance.initialize_special_fields()
    return {'value': result_instance,'admin_rules_menu': admin_rules_menu}

# edit
@view_config(route_name='admin.admin.rule.edit',permission="admin", renderer='zhanor_admin:templates/admin/admin/rule/edit.jinja2')
def edit_view(request):
    admin_rule_id = request.matchdict.get('id')
    result = request.dbsession.query(AdminRule).filter(AdminRule.id == admin_rule_id).first()
    return {'value': result}

@view_config(route_name='admin.admin.rule.save', permission="admin", renderer='json', request_method='POST')
def add_or_edit_admin_rule_view(request):
    try:
        admin_rule_id = request.POST.get("id")
        admin_rule = None
        if admin_rule_id:
            admin_rule = (
                request.dbsession.query(AdminRule).filter_by(id=admin_rule_id).one_or_none()
            )
            if admin_rule is None:
                raise Response(
                    json.dumps({"status": 0, "message": "AdminRule not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            admin_rule = AdminRule()
            if hasattr(AdminRule, "createtime"):
                admin_rule.createtime = now(request)

        for field in request.POST.keys():
            clean_field = field.replace("[]", "")
            if clean_field in AdminRule.__table__.columns.keys()and field not in [
                "id",
                "createtime",
                "updatetime",
            ]:
                if field.endswith("[]"):
                    setattr(admin_rule, clean_field, ','.join(map(str, request.POST.getall(field))))
                else:
                    setattr(admin_rule, field, request.POST[field])

        if hasattr(AdminRule, "updatetime"):
            admin_rule.updatetime = now(request)

        if not admin_rule_id:
            request.dbsession.add(admin_rule)
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
@view_config(route_name='admin.admin.rule.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_admin_rule_view(request):
    data = json.loads(request.body)
    admin_rule_ids = data.get('ids', [])
    if not admin_rule_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for admin_rule_id in admin_rule_ids:
            admin_rule = request.dbsession.query(AdminRule).filter(AdminRule.id == admin_rule_id).one()
            request.dbsession.delete(admin_rule)  
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
