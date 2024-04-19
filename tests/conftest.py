# import alembic
# import alembic.config
# import alembic.command
# import os
# from pyramid.paster import get_appsettings
# from pyramid.scripting import prepare
# from pyramid.testing import DummyRequest, testConfig
# import pytest
# import transaction
# import webtest

# from zhanor_admin import main
# from zhanor_admin import models
# from zhanor_admin.models.meta import Base


# def pytest_addoption(parser):
#     parser.addoption('--ini', action='store', metavar='INI_FILE')

# @pytest.fixture(scope='session')
# def ini_file(request):
#     # potentially grab this path from a pytest option
#     return os.path.abspath(request.config.option.ini or 'testing.ini')

# @pytest.fixture(scope='session')
# def app_settings(ini_file):
#     return get_appsettings(ini_file)

# @pytest.fixture(scope='session')
# def dbengine(app_settings, ini_file):
#     engine = models.get_engine(app_settings)

#     alembic_cfg = alembic.config.Config(ini_file)
#     Base.metadata.drop_all(bind=engine)
#     alembic.command.stamp(alembic_cfg, None, purge=True)

#     # run migrations to initialize the database
#     # depending on how we want to initialize the database from scratch
#     # we could alternatively call:
#     # Base.metadata.create_all(bind=engine)
#     # alembic.command.stamp(alembic_cfg, "head")
#     alembic.command.upgrade(alembic_cfg, "head")

#     yield engine

#     Base.metadata.drop_all(bind=engine)
#     alembic.command.stamp(alembic_cfg, None, purge=True)

# @pytest.fixture(scope='session')
# def app(app_settings, dbengine):
#     return main({}, dbengine=dbengine, **app_settings)

# @pytest.fixture
# def tm():
#     tm = transaction.TransactionManager(explicit=True)
#     tm.begin()
#     tm.doom()

#     yield tm

#     tm.abort()

# @pytest.fixture
# def dbsession(app, tm):
#     session_factory = app.registry['dbsession_factory']
#     return models.get_tm_session(session_factory, tm)

# @pytest.fixture
# def testapp(app, tm, dbsession):
#     # override request.dbsession and request.tm with our own
#     # externally-controlled values that are shared across requests but aborted
#     # at the end
#     testapp = webtest.TestApp(app, extra_environ={
#         'HTTP_HOST': 'example.com',
#         'tm.active': True,
#         'tm.manager': tm,
#         'app.dbsession': dbsession,
#     })

#     return testapp

# @pytest.fixture
# def app_request(app, tm, dbsession):
#     """
#     A real request.

#     This request is almost identical to a real request but it has some
#     drawbacks in tests as it's harder to mock data and is heavier.

#     """
#     with prepare(registry=app.registry) as env:
#         request = env['request']
#         request.host = 'example.com'

#         # without this, request.dbsession will be joined to the same transaction
#         # manager but it will be using a different sqlalchemy.orm.Session using
#         # a separate database transaction
#         request.dbsession = dbsession
#         request.tm = tm

#         yield request

# @pytest.fixture
# def dummy_request(tm, dbsession):
#     """
#     A lightweight dummy request.

#     This request is ultra-lightweight and should be used only when the request
#     itself is not a large focus in the call-stack.  It is much easier to mock
#     and control side-effects using this object, however:

#     - It does not have request extensions applied.
#     - Threadlocals are not properly pushed.

#     """
#     request = DummyRequest()
#     request.host = 'example.com'
#     request.dbsession = dbsession
#     request.tm = tm

#     return request

# @pytest.fixture
# def dummy_config(dummy_request):
#     """
#     A dummy :class:`pyramid.config.Configurator` object.  This allows for
#     mock configuration, including configuration for ``dummy_request``, as well
#     as pushing the appropriate threadlocals.

#     """
#     with testConfig(request=dummy_request) as config:
#         yield config
import logging


data = [('gmt_create', '2024-04-19 09:37:36'), ('charset', 'utf-8'), ('gmt_payment', '2024-04-19 09:37:39'), ('notify_time', '2024-04-19 09:51:27'), ('subject', 'vip'), ('sign', 'auOxmWCXe2RvlfCbXeliLQ6BZ0NS2yL01b2C9GOJChjippZmwGTWMKVU+LMqcqY3gosgyju2n6w+DRVNyIidsVmOtCNX8UNHrhqidOEh3hOn3nwZerGzt2Gc76U0XMQ9FhFWf/PXHsNW8ZCRj5a45/ArAZI+TV/fj+cy69abUSBpLKm9kqw4cc+pn/9stkAoLoECCisD1Q089A65iDXJWppQkK8eVd3uteU6JO70FdWYY2RvCQZ01cYuB7Lxp7oebfuEJTmHVwqrF8G+np/EOcR0uvzk2jCtvhpMuNydFeN8j/01eqfPqKIktc7mzwVJQlZ/yAgnbILXa0Bqp0f/fg=='), ('buyer_id', '2088002928988794'), ('body', 'vip'), ('invoice_amount', '1.00'), ('version', '1.0'), ('notify_id', '2024041901222093739088791462317779'), ('fund_bill_list', '[{"amount":"1.00","fundChannel":"ALIPAYACCOUNT"}]'), ('notify_type', 'trade_status_sync'), ('out_trade_no', '20240419717355'), ('total_amount', '1.00'), ('trade_status', 'TRADE_SUCCESS'), ('trade_no', '2024041922001488791441534862'), ('auth_app_id', '2021003182643073'), ('receipt_amount', '1.00'), ('point_amount', '0.00'), ('buyer_pay_amount', '1.00'), ('app_id', '2021003182643073'), ('sign_type', 'RSA2'), ('seller_id', '2088021402341331')]



# 检查是否存在多值字段
has_multiple_values = any(len(item[1]) > 1 for item in data)


# 处理数据
processed_data = {}
if has_multiple_values:
    processed_data = dict(data)

else:
    processed_data = data

# 移除并获取签名
sign = processed_data.pop('sign', None)
 
# 记录原始数据
print(f"user.recharge.pay.notify====>data: {data}")

# 验证签名
try:
    sorted_params = sorted(processed_data.items())  # 按照键名排序
    message = '&'.join(f"{k}={v}" for k, v in sorted_params)  # 拼接排序后的参数
    
    print(f"user.recharge.pay.notify====>,\n\n\n {message.encode('utf-8')},\n\n\n {sign.encode('utf-8')}\n\n\n\n")
    
except Exception as e:
    print(f"Failed to verify the signature: {e}")
    is_verified = False
    
    
    
    
    
app_id=2021003182643073&auth_app_id=2021003182643073&body=vip&buyer_id=2088002928988794&buyer_pay_amount=1.00&charset=utf-8&fund_bill_list=[{"amount":"1.00","fundChannel":"ALIPAYACCOUNT"}]&gmt_create=2024-04-19 10:07:03&gmt_payment=2024-04-19 10:07:06&invoice_amount=1.00&notify_id=2024041901222100707088791464227487&notify_time=2024-04-19 10:07:07&notify_type=trade_status_sync&out_trade_no=20240419473156&point_amount=0.00&                                                receipt_amount=1.00&seller_id=2088021402341331&sign_type=RSA2&subject=vip&total_amount=1.00&trade_no=2024041922001488791440154030&trade_status=TRADE_SUCCESS&version=1.0


app_id=2016092101248425&buyer_id=2088102114562585&buyer_pay_amount=0.80&fund_bill_list=[{"amount":"0.80","fundChannel":"ALIPAYACCOUNT"},{"amount":"0.20","fundChannel":"MDISCOUNT"}]        &gmt_create=2016-10-12 21:36:12&gmt_payment=2016-10-12 21:37:19&invoice_amount=0.80&notify_id=7676a2e1e4e737cff30015c4b7b55e3kh6&notify_time=2016-10-12 21:41:23&notify_type=trade_status_sync&out_trade_no=mobile_rdm862016-10-12213600&passback_params=passback_params123&point_amount=0.00&receipt_amount=0.80&seller_id=2088201909970555&subject=PC网站支付交易&total_amount=1.00&trade_no=2016101221001004580200203978&trade_status=TRADE_SUCCESS&voucher_detail_list=[{"amount":"0.20","merchantContribute":"0.00","name":"5折券","otherContribute":"0.20","type":"ALIPAY_DISCOUNT_VOUCHER","voucherId":"2016101200073002586200003BQ4"}]
