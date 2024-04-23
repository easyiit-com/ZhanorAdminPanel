import json
import logging
from pyramid.authorization import Allow, Everyone, ALL_PERMISSIONS
from pyramid.httpexceptions import (
    HTTPNotFound,
    HTTPSeeOther,
)
import transaction
from sqlalchemy import inspect
from sqlalchemy.orm import scoped_session, sessionmaker
from zhanor_admin.common.cache import Cache
from zhanor_admin.models.admin_rule import AdminRule
from pyramid.events import ApplicationCreated
from pyramid.events import subscriber

from zhanor_admin.models.meta import Base
from zhanor_admin.models import *
from zhanor_admin.models.user_rule import UserRule


from . import models


def process_admin_rules(dbsession, database_rules, cache, settings):
    admin_rules_dicts = []
    json_data = ""

    for admin_rule in database_rules:
        admin_rule_dict = AdminRule.to_dict(admin_rule)
        children_query = (
            dbsession.query(AdminRule)
            .filter(AdminRule.pid == admin_rule.id, AdminRule.type == "menu")
            .order_by(AdminRule.id.asc())
        )
        admin_rule_dict["child"] = [
            AdminRule.to_dict(child) for child in children_query.all()
        ]
        url_paths = [child["url_path"] for child in admin_rule_dict["child"]]
        admin_rule_dict["url_paths"] = url_paths
        admin_rules_dicts.append(admin_rule_dict)

    json_data = json.dumps(admin_rules_dicts, default=str)
    cache.set("admin_rules", json_data, expire=3600 * 24 * 7)
    return admin_rules_dicts


def process_user_rules(dbsession, database_rules, cache, settings):
    user_rules_dicts = []
    json_data = ""

    for user_rule in database_rules:
        user_rule_dict = UserRule.to_dict(user_rule)
        children_query = (
            dbsession.query(UserRule)
            .filter(UserRule.pid == user_rule.id, UserRule.type == "menu")
            .order_by(UserRule.id.asc())
        )
        user_rule_dict["child"] = [
            UserRule.to_dict(child) for child in children_query.all()
        ]
        url_paths = [child["url_path"] for child in user_rule_dict["child"]]
        user_rule_dict["url_paths"] = url_paths
        user_rules_dicts.append(user_rule_dict)

    json_data = json.dumps(user_rules_dicts, default=str)
    cache.set("user_rules", json_data, expire=3600 * 24 * 7)
    return user_rules_dicts


def includeme(config):
    settings = config.registry.settings

    config.add_static_view("static", "static", cache_max_age=3600)
    add_localized_route(config, "home", "/")
    add_localized_route(config, "admin", "/admin")
    add_localized_route(config, "admin.auth.login", "/admin/login")
    
    add_localized_route(config, "auth.logout", "/admin/logout")
    add_localized_route(config, "upload", "/upload") 
    add_localized_route(config, "updater.check", "/updater/check") 
    add_localized_route(config, "qr", "/qr/{data:.*}")
    
    add_localized_route(config, "admin.cache.clear.all", "/admin/cache/clear/all")

    add_localized_route(config, "user.auth.login", "/user/login")
    add_localized_route(config, "user.auth.register", "/user/register")
    add_localized_route(config, "user.auth.forgot.password", "/user/forgot/password")
    add_localized_route(config, "user.auth.send.mail", "/user/send/mail")
    add_localized_route(config, "user.auth.logout", "/user/logout")
    add_localized_route(config, "user", "/user")
    
    add_localized_route(config, 'api.user.group', '/api/user/group/{page}')
    add_localized_route(config, 'api.user.group.save', '/api/user/group/save/{id}')
    add_localized_route(config, 'api.user.group.delete', '/api/user/group/delete/{id}')
    
    add_localized_route(config, 'api.auth.login', '/api/auth/login')
    add_localized_route(config, 'api.auth.register', '/api/auth/register')
    add_localized_route(config, 'api.auth.forgot.password', '/api/auth/forgot/password')
    add_localized_route(config, 'api.auth.send.mail', '/api.auth/send/mail')
    add_localized_route(config, 'api.auth.logout', '/api/auth/logout')

    # config.add_route('admin_area', '/admin/*subpath',
    #                  custom_predicates=())

    cache_open = settings.get("cache.open", False)
    cache = Cache(settings)
    # if cache_open:
    #     cached_data = cache.get("admin_rules")
    #     if cached_data:
    #         admin_rules_from = "cache"
    #         admin_rules = json.loads(cached_data)
    #     else:
    #         admin_rules_from = "database"
    #         query = (
    #             DBSession.query(AdminRule)
    #             .filter(AdminRule.pid == 0, AdminRule.ismenu == 1)å
    #             .order_by(AdminRule.id.asc())
    #         )
    #         admin_rules = process_admin_rules(query.all(), cache, settings)
    # else:
    admin_rules_from = "database"

    engine = models.get_engine(settings)
    DBSession = scoped_session(sessionmaker(bind=engine))
    
    scoped_sess = scoped_session(sessionmaker(bind=engine))
    # 获取数据库检查器来获取所有表的信息
    inspector = inspect(engine)
    # 打开一个文件用于写入dbsession.add()语句
    with open('orm_add_statements.txt', 'w') as f:
        # 遍历所有表
        for table_name in inspector.get_table_names():
            # 获取对应表的ORM类
            table_class = next((c for c in models.__dict__.values() if hasattr(c, '__tablename__') and c.__tablename__ == table_name), None)
            if table_class is not None:
                # 查询该表的所有记录
                records = scoped_sess.query(table_class).all()
                
                for record in records:
                    # 生成模拟的dbsession.add()调用语句
                    add_params = ', '.join(f"{col}='{getattr(record, col)}'" for col in record.__table__.columns.keys())
                    add_stmt = f"dbsession.add({table_class.__name__}({add_params}))"
                    # 写入文件
                    f.write(add_stmt + "\n")

    # 关闭数据库会话
    scoped_sess.remove()

    with transaction.manager:
        dbsession = DBSession()
        query = (
            dbsession.query(AdminRule)
            .filter(
                AdminRule.pid == 0,
                AdminRule.type == "menu",
                AdminRule.status == "normal",
            )
            .order_by(AdminRule.id.asc())
        )
        admin_rules = process_admin_rules(dbsession, query.all(), cache, settings)
        config.registry.admin_rules = admin_rules

        admin_rules_query_all = (
            dbsession.query(AdminRule)
            .filter(AdminRule.status == "normal")
            .order_by(AdminRule.id.asc())
        )
        admin_rules_all = admin_rules_query_all.all()
      
        config.registry.admin_rules_all = admin_rules_all
        for admin_rule in admin_rules_all:
            add_localized_route(
                config,
                admin_rule.name,
                admin_rule.url_path,
                title=admin_rule.title,
                description=admin_rule.description,
            )

        # user rules
        user_rules_query = (
            dbsession.query(UserRule)
            .filter(
                UserRule.pid == 0,
                UserRule.type == "menu",
                UserRule.status == "normal",
            )
            .order_by(UserRule.id.asc())
        )
        user_rules = process_user_rules(
            dbsession, user_rules_query.all(), cache, settings
        )
        config.registry.user_rules = user_rules
        user_rules_query_all = (
            dbsession.query(UserRule)
            .filter(UserRule.status == "normal")
            .order_by(UserRule.id.asc())
        )
        user_rules_all = user_rules_query_all.all()
        config.registry.user_rules_all = user_rules_all
        for user_rule in user_rules_all:
            add_localized_route(
                config,
                user_rule.name,
                user_rule.url_path,
                title=user_rule.title,
                description=user_rule.description,
            )


def add_localized_route(config, name, pattern, title="", description=""):
    localized_pattern = "" + pattern
    # localized_pattern = '/{lang}' + pattern
    config.add_route(name, localized_pattern, factory=page_factory)

    if not hasattr(config.registry, "route_title"):
        config.registry.route_title = {}
    config.registry.route_title[name] = (
        title if title else name.replace(".", " ").title()
    )

    if not hasattr(config.registry, "route_descriptions"):
        config.registry.route_descriptions = {}
    config.registry.route_descriptions[name] = description


def page_factory(request):
    page = "newPage"
    if page is None:
        raise HTTPNotFound
    return PageResource(page)

class PageResource:
    def __init__(self, page):
        self.page = page

    def __acl__(self):
        return [
            (Allow, Everyone, "view"),
            (Allow, "role:admin", ALL_PERMISSIONS),
            (Allow, "role:user", "user"),
            (Allow, "role:view", "view"),
            # (Allow, 'u:12', 'edit'),
        ]

from pyramid.security import Allow, Everyone

class AdminFactory(object):
    def __init__(self, request):
        self.__acl__ = [(Allow, Everyone, "view"), (Allow, "role:admin", "admin:view")]

class UserFactory(object):
    def __init__(self, request):
        self.__acl__ = [
            (Allow, Everyone, "view"),
            (Allow, "role:user", "user:view"),
            (Allow, "role:admin", "admin:view"),
        ]
