# addon.py
import json
from pyramid.view import view_config
from pyramid.response import Response
from sqlalchemy.exc import OperationalError
from ...common.cache import Cache
import sqlalchemy

@view_config(route_name='admin.cache.clear.all', permission='admin', renderer='json', request_method='POST')
def clear_all(request):
    try:
        settings = request.registry.settings
        cache = Cache(settings)
        cache.flush_db()
        request.dbsession.expunge_all()
    except Exception as e:
        return Response(
            json.dumps({"status": 0, "message": f"Clean Error:{e}", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status = 500
        )
    return Response(
            json.dumps({'status': 1, 'message': 'Clean Success', 'data': {}}),
            content_type="application/json",
            charset="utf-8",
            status = 200
        )
@view_config(route_name='admin.cache.clear.all', permission='view', renderer='admin/cache.html')
def add_view(request):
    result = {}
    return {'value': result}