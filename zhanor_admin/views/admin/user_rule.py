# user_rule.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError

from zhanor_admin.common.tree import Tree
from ...models.user_rule import UserRule
import transaction

# list
@view_config(route_name='admin.user.rule', permission="admin",renderer='zhanor_admin:templates/admin/user/rule/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(UserRule)
        user_rules = query.order_by(UserRule.id.asc()).all()
        user_rule_dicts = [user_rule.to_dict() for user_rule in user_rules]
        response_data = {'status': 1, 'message': 'Success', 'data': user_rule_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 2000
        query = request.dbsession.query(UserRule)
        total_count = query.count()
        user_rule_list = query.order_by(UserRule.id.asc()).offset((page - 1) * per_page).limit(per_page).all()
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
                } for rule in user_rule_list]
        tree = Tree(options)
        tree.init(data)
        user_rule_tree_list = tree.getTreeList(tree.getTreeArray(0),field='title')
        pages = (total_count + per_page - 1) // per_page
        return {'user_rule_list': user_rule_tree_list,'current_page': page,'total_pages': pages,}

# add
@view_config(route_name='admin.user.rule.add', permission="admin", renderer='zhanor_admin:templates/admin/user/rule/add.jinja2')
def add_view(request):
    demo_instance = UserRule()
    demo_instance.initialize_special_fields()
    query = request.dbsession.query(UserRule)
    user_rules = query.order_by(UserRule.id.desc()).all()
    return {'value': demo_instance,'user_rules':user_rules}

# edit
@view_config(route_name='admin.user.rule.edit', renderer='zhanor_admin:templates/admin/user/rule/edit.jinja2')
def edit_view(request):
    user_rule_id = request.matchdict.get('id')
    result = request.dbsession.query(UserRule).filter(UserRule.id == user_rule_id).first()
    query = request.dbsession.query(UserRule)
    user_rules = query.order_by(UserRule.id.desc()).all()
    return {'value': result,'user_rules':user_rules}

@view_config(route_name='admin.user.rule.save', permission="admin", renderer='json', request_method='POST')
def add_or_edit_user_rule_view(request):
    try:
        user_rule_id = request.POST.get("id")
        user_rule = None
        if user_rule_id:
            user_rule = (
                request.dbsession.query(UserRule).filter_by(id=user_rule_id).one_or_none()
            )
            if user_rule is None:
                raise Response(
                    json.dumps({"status": 0, "message": "UserRule not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            user_rule = UserRule()
            if hasattr(UserRule, "createtime"):
                user_rule.createtime = now(request)

        for field in request.POST.keys():
            clean_field = field.replace("[]", "")
            if clean_field in UserRule.__table__.columns.keys()and field not in [
                "id",
                "createtime",
                "updatetime",
            ]:
                if field.endswith("[]"):
                    setattr(user_rule, clean_field, ','.join(map(str, request.POST.getall(field))))
                else:
                    setattr(user_rule, field, request.POST[field])

        if hasattr(UserRule, "updatetime"):
            user_rule.updatetime = now(request)

        if not user_rule_id:
            request.dbsession.add(user_rule)
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
@view_config(route_name='admin.user.rule.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_user_rule_view(request):
    data = json.loads(request.body)
    user_rule_ids = data.get('ids', [])
    if not user_rule_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for user_rule_id in user_rule_ids:
            user_rule = request.dbsession.query(UserRule).filter(UserRule.id == user_rule_id).one()
            request.dbsession.delete(user_rule)  
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
