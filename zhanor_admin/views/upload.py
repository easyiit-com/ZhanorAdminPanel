from datetime import datetime
import mimetypes
import os
import uuid
from zhanor_admin.common.defs import now
from pyramid.view import view_config
from pyramid.response import Response

from zhanor_admin.common.defs import get_image_info, is_image
from ..models.attachment_file import AttachmentFile
from ..models.attachment_image import AttachmentImage
import transaction

import logging
logger = logging.getLogger(__name__)

@view_config(route_name='upload', permission="view", renderer='json')
def upload_view(request):
    user_id = 0
    admin_id = 0
    settings = request.registry.settings
    upload_directory = settings.get('upload.directory', 'static/uploads') 
    allowed_image_extensions = settings.get('upload.image.extensions', '.jpg,.jpeg,.png,.gif').split(',')
    allowed_file_extensions = settings.get('upload.file.extensions', '.pdf,.zip').split(',')
    allowed_extensions = allowed_image_extensions + allowed_file_extensions
    max_size = int(settings.get('upload.max_size', 5242880))
    max_count = int(settings.get('upload.max_count', 3)) 
    
    upload_files = request.POST.getall('files[]')
    save = request.POST.get('save','true')

    if isinstance(upload_files, (list, tuple)): 
        if len(upload_files) > max_count:
            return Response(json_body={'error': 'Exceeded max file count'}, status=400)
    
    urls = []
    for upload_file in upload_files:
        filename = upload_file.filename
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed_extensions:
            return Response(
                json_body={"status": 0, "message": "File type not allowed"},
                content_type="application/json",
                charset="utf-8",
                status=400
            )

        if upload_file.length > max_size:
            return Response(
                json_body={"status": 0, "message": "File size is too large"},
                content_type="application/json",
                charset="utf-8",
                status=400
            )
            
        base_path = os.path.join(upload_directory, datetime.now().strftime('%Y%m%d'))
        os.makedirs(base_path, exist_ok=True)  
        
        unique_filename = str(uuid.uuid4()) + ext
        file_path = os.path.join(base_path, unique_filename)
        
        with open(file_path, 'wb') as output_file:
            output_file.write(upload_file.file.read())
        relative_path = os.path.join('/static/uploads', datetime.now().strftime('%Y%m%d'), unique_filename)
        full_url = request.static_url('zhanor_admin:static/' + relative_path)
        if save=='true':
            user = getattr(request, 'user', None)
            if user:
                user_id = getattr(user, 'id', 0)
            admin = getattr(request, 'admin', None)
            if admin:
                admin_id = getattr(admin, 'id', 0)
            
            
            admin_id = getattr(admin, 'id', 0)
            if is_image(file_path):
                img_info = get_image_info(file_path)
                attachment_image = AttachmentImage()
                attachment_image.category = 'upload'
                attachment_image.admin_id = admin_id
                attachment_image.user_id = user_id
                attachment_image.path_image = relative_path
                attachment_image.image_width = img_info.width
                attachment_image.image_height = img_info.height
                attachment_image.image_type = img_info.format.lower() 
                attachment_image.name = filename
                attachment_image.file_size = os.path.getsize(file_path)
                format = img_info.format.lower()
                if ".webp" not in mimetypes.types_map:
                    mimetypes.add_type("image/webp", ".webp")
                mime_type = mimetypes.types_map[f".{format}"]
                attachment_image.mimetype = mime_type
                attachment_image.createtime = now(request)
                attachment_image.updatetime = now(request)
                request.dbsession.add(attachment_image)
            else:
                attachment_file = AttachmentFile()
                attachment_file.category = 'upload'
                attachment_file.admin_id = admin_id
                attachment_file.user_id = user_id
                attachment_file.path_file = relative_path
                attachment_file.file_name = filename
                attachment_file.file_size = os.path.getsize(file_path)
                attachment_file.mimetype = ''
                attachment_file.createtime = now(request)
                attachment_file.updatetime = now(request)
                attachment_file.storage = ''
                request.dbsession.add(attachment_file)
            transaction.commit()
        urls.append({'full_url': full_url, 'relative_url': relative_path})
    
    return Response(
                json_body={"status": 1, "message": "Files uploaded successfully", "data": urls},  # 更新成功状态消息和数据
                content_type="application/json",
                charset="utf-8",
                status=200
            )
 