import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))

requires = [
    'plaster_pastedeploy',
    'pyramid',
    'pyramid_jinja2',
    'pyramid_debugtoolbar',
    'waitress',
    'alembic',
    'pyramid_retry',
    'pyramid_tm',
    'SQLAlchemy',
    'transaction',
    'zope.sqlalchemy',
    'docutils',
    'mysqlclient',
    'redis',
    'beaker',
    'requests',
    'passlib',
    'Pillow',
    'colander',
    'pytz',
    'bcrypt',
    'pyramid_jwt',
    'PyJWT',
    'wechatpayv3',
    'cryptography',
    'qrcode[pil]',
    'alipay-sdk-python',
    'pyramid_openapi3',
    'ruamel.yaml'
]

tests_require = [
    'WebTest',
    'pytest',
    'pytest-cov',
]

setup(
    name='zhanor_admin',
    version='0.0',
    description='zhanor_admin',
    long_description='',
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Pyramid',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    author='zhanor',
    author_email='zhanfish@foxmail.com',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    extras_require={
        'testing': tests_require,
    },
    install_requires=requires,
    entry_points={
        'paste.app_factory': [
            'main = zhanor_admin:main',
        ],
        'console_scripts': [
            'initialize_zhanor_admin_db=zhanor_admin.scripts.initialize_db:main',
        ],
    },
)
