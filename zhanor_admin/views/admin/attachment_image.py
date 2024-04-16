# attachment_image.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import now
from sqlalchemy.exc import OperationalError
from ...models.attachment_image import AttachmentImage
import transaction

# list
@view_config(route_name='admin.attachment.image', permission="admin",renderer='zhanor_admin:templates/admin/attachment/image/index.jinja2')
def index_view(request):
    if request.is_xhr:
        query = request.dbsession.query(AttachmentImage)
        attachment_images = query.order_by(AttachmentImage.id.desc()).all()
        attachment_image_dicts = [attachment_image.to_dict() for attachment_image in attachment_images]
        response_data = {'status': 1, 'message': 'Success', 'data': attachment_image_dicts}  # 假设User模型有to_dict方法将对象转换为字典
        return Response(
            json.dumps(response_data),
            content_type="application/json",
            charset="utf-8",
            status=200
        )
    else:
        page = int(request.GET.get('page', 1))
        per_page = 20
        query = request.dbsession.query(AttachmentImage)
        total_count = query.count()
        attachment_image_list = query.order_by(AttachmentImage.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total_count + per_page - 1) // per_page
        return {'attachment_image_list': attachment_image_list,'current_page': page,'total_pages': pages,}

# add
@view_config(route_name='admin.attachment.image.add', permission="admin", renderer='zhanor_admin:templates/admin/attachment/image/add.jinja2')
def add_view(request):
    result = {}
    return {'value': result}

# edit
@view_config(route_name='admin.attachment.image.edit',permission="admin", renderer='zhanor_admin:templates/admin/attachment/image/edit.jinja2')
def edit_view(request):
    attachment_image_id = request.matchdict.get('id')
    result = request.dbsession.query(AttachmentImage).filter(AttachmentImage.id == attachment_image_id).first()
    return {'value': result}

@view_config(route_name='admin.attachment.image.save', permission="admin", renderer='json', request_method='POST')
def add_or_edit_attachment_image_view(request):
    try:
        attachment_image_id = request.POST.get("id")
        attachment_image = None
        if attachment_image_id:
            attachment_image = (
                request.dbsession.query(AttachmentImage).filter_by(id=attachment_image_id).one_or_none()
            )
            if attachment_image is None:
                raise Response(
                    json.dumps({"status": 0, "message": "AttachmentImage not found.", "data": {}}),
                    content_type="application/json",
                    charset="utf-8",
                    status=500,
                )
        else:
            attachment_image = AttachmentImage()
            if hasattr(AttachmentImage, "createtime"):
                attachment_image.createtime = now(request)

        for field in request.POST.keys():
            clean_field = field.replace("[]", "")
            if clean_field in AttachmentImage.__table__.columns.keys()and field not in [
                "id",
                "createtime",
                "updatetime",
            ]:
                if field.endswith("[]"):
                    setattr(attachment_image, clean_field, ','.join(map(str, request.POST.getall(field))))
                else:
                    setattr(attachment_image, field, request.POST[field])

        if hasattr(AttachmentImage, "updatetime"):
            attachment_image.updatetime = now(request)

        if not attachment_image_id:
            request.dbsession.add(attachment_image)
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
@view_config(route_name='admin.attachment.image.delete', permission="admin", renderer='json', request_method='DELETE')
def delete_attachment_image_view(request):
    data = json.loads(request.body)
    attachment_image_ids = data.get('ids', [])
    if not attachment_image_ids:
        return Response(
            json.dumps({"status": 0, "message": "Error,Need IDs", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500
        )
    try:
        for attachment_image_id in attachment_image_ids:
            attachment_image = request.dbsession.query(AttachmentImage).filter(AttachmentImage.id == attachment_image_id).one()
            request.dbsession.delete(attachment_image)  
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
