# attachment_file.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError
from ...models.attachment_file import AttachmentFile
import transaction

# list
@view_config(route_name='admin.attachment.file', permission="admin",renderer='zhanor_admin:templates/admin/attachment/file/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(AttachmentFile)
        attachment_files = query.order_by(AttachmentFile.id.desc()).all()
        attachment_file_dicts = [attachment_file.to_dict() for attachment_file in attachment_files]
        response_data = {'status': 1, 'message': 'Success', 'data': attachment_file_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 20
        query = request.dbsession.query(AttachmentFile)
        total_count = query.count()
        attachment_file_list = query.order_by(AttachmentFile.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page
        return {'attachment_file_list': attachment_file_list,'current_page': page,'total_pages': pages,}

# add
@view_config(route_name='admin.attachment.file.add', permission="admin", renderer='zhanor_admin:templates/admin/attachment/file/add.jinja2')
def add_view(request):
    result = {}
    return {'value': result}

# edit
@view_config(route_name='admin.attachment.file.edit',permission="admin", renderer='zhanor_admin:templates/admin/attachment/file/edit.jinja2')
def edit_view(request):
    attachment_file_id = request.matchdict.get('id')
    result = request.dbsession.query(AttachmentFile).filter(AttachmentFile.id == attachment_file_id).first()
    return {'value': result}

@view_config(route_name='admin.attachment.file.save', permission="admin", renderer='json', request_method='POST')
def add_or_edit_attachment_file_view(request):
    try:
        attachment_file_id = request.POST.get("id")
        attachment_file = None
        if attachment_file_id:
            attachment_file = (
                request.dbsession.query(AttachmentFile).filter_by(id=attachment_file_id).one_or_none()
            )
            if attachment_file is None:
                raise Response(
                    json.dumps({"status": 0, "message": "AttachmentFile not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            attachment_file = AttachmentFile()
            if hasattr(AttachmentFile, "createtime"):
                attachment_file.createtime = now(request)

        for field in request.POST.keys():
            clean_field = field.replace("[]", "")
            if clean_field in AttachmentFile.__table__.columns.keys()and field not in [
                "id",
                "createtime",
                "updatetime",
            ]:
                if field.endswith("[]"):
                    setattr(attachment_file, clean_field, ','.join(map(str, request.POST.getall(field))))
                else:
                    setattr(attachment_file, field, request.POST[field])

        if hasattr(AttachmentFile, "updatetime"):
            attachment_file.updatetime = now(request)

        if not attachment_file_id:
            request.dbsession.add(attachment_file)
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
@view_config(route_name='admin.attachment.file.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_attachment_file_view(request):
    data = json.loads(request.body)
    attachment_file_ids = data.get('ids', [])
    if not attachment_file_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for attachment_file_id in attachment_file_ids:
            attachment_file = request.dbsession.query(AttachmentFile).filter(AttachmentFile.id == attachment_file_id).one()
            request.dbsession.delete(attachment_file)  
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
