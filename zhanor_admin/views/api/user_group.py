# api user_group.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from pyramid.httpexceptions import HTTPInternalServerError, HTTPBadRequest
from colander import Invalid
from ...models.user_group import UserGroup
import transaction


# list
@view_config(route_name="api.user.group", permission="user", renderer="json", require_csrf=False)
def index_view(request):
    default_page = 1
    if request.method == 'GET':
        page = int(request.GET.get('page', default_page))
    elif request.method == 'POST':
        if request.content_type.startswith('application/json'):
            try:
                body = json.loads(request.body.decode('utf-8'))
                page = int(body.get('page', default_page))
            except (json.JSONDecodeError, ValueError):
                return Response(
                    json.dumps({"status": 0, "message": "Invalid JSON or 'page' value", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            page = int(request.POST.get('page', default_page))
 
    if '{page}' in request.matched_route.pattern:
        page_match = request.matchdict.get('page')
        if page_match is not None:
            page = int(page_match)
 
    if request.method not in ('GET', 'POST'):
        return Response(
                    json.dumps({"status": 0, "message": "HTTP Method Not Allowed.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
    per_page = 20
    query = request.dbsession.query(UserGroup)
    total_count = query.count()
    user_group_list = query.order_by(UserGroup.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
    pages = (total_count + per_page - 1) // per_page
    user_group_dicts = [user_group.to_dict() for user_group in user_group_list]
    datas = {'user_group_list': user_group_dicts,'current_page': page,'total_pages': pages}
    response_data = {'status': 1, 'message': 'Success', 'data': datas}  # 假设User模型有to_dict方法将对象转换为字典
    return Response(
        json.dumps(response_data),
        content_type="application/json",
        charset="utf-8",
        status=200
    )

@view_config(
    route_name="api.user.group.save",
    renderer="json",
    permission="user",
    request_method="POST",
    require_csrf=False,
)
def add_or_edit_user_group_view(request):
    user_group_id = None
    post_data = {}
    if request.content_type.startswith("application/json"):
        try:
            body = request.json_body
            user_group_id = body.get("id", None)
            post_data = body
        except (json.JSONDecodeError, ValueError):
            return HTTPBadRequest(
                json_body={
                    "status": 0,
                    "message": "Invalid JSON or 'id' value",
                    "data": {},
                },
                content_type="application/json",
                charset="utf-8",
            )
    else:
        post_data = request.POST.mixed()
        user_group_id = post_data.get("id") and int(post_data["id"])
    if user_group_id is not None:
        user_group = (
            request.dbsession.query(UserGroup).filter_by(id=user_group_id).one_or_none()
        )
        if user_group is None:
            return HTTPInternalServerError(
                json_body={"status": 0, "message": "UserGroup not found.", "data": {}}
            )
    else:
        user_group = UserGroup()
        if hasattr(UserGroup, "createtime"):
            user_group.createtime = now(request)

    for key, value in post_data.items():
        if hasattr(user_group, key):
            attr_value = value
            setattr(user_group, key, attr_value)

    if hasattr(user_group, "updatetime"):
        user_group.updatetime = now(request)
    try:
        if user_group.id is None:
            request.dbsession.add(user_group)
        request.dbsession.flush()
        transaction.commit()
    except Exception as e:
        request.dbsession.rollback()
        transaction.abort()
        return HTTPInternalServerError(
            json_body={"status": 0, "message": f"Error: {e}", "data": {}}
        )

    response_body = {"status": 1, "message": "Success", "data": {}}
    return Response(
        json_body=response_body, content_type="application/json", charset="utf-8"
    )

# delete
@view_config(
    route_name="api.user.group.delete",
    renderer="json",
    permission="user",
    request_method="DELETE",
    require_csrf=False,
)
def delete_user_group_view(request):
    user_group_id = request.matchdict["id"]
    if not user_group_id:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500,
        )
    try:
        user_group = (
            request.dbsession.query(UserGroup)
            .filter(UserGroup.id == int(user_group_id))
            .one()
        )
        request.dbsession.delete(user_group)
        transaction.commit()
    except Exception as e:
        request.dbsession.rollback()
        transaction.abort()
        return Response(
            json.dumps({"status": 0, "message": f"Error:{e}", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500,
        )
    return Response(
        json.dumps({"status": 1, "message": "Success", "data": {}}),
        content_type="application/json",
        charset="utf-8",
        status=200,
    )
