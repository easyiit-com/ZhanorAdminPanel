from zhanor_admin import models
from zhanor_admin.views.qr import qr_view


def test_qr_view_failure(app_request):
    info = qr_view(app_request)
    assert info.status_int == 500

def test_qy_view_success(app_request, dbsession):
    model = models.User(name='test')
    dbsession.add(model)
    dbsession.flush()

    info = qr_view(app_request)
    assert app_request.response.status_int == 200
    assert info['one'].name == 'one'
    assert info['project'] == 'zhanor_admin'
