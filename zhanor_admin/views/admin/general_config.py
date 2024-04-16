# general_config.py
import json,datetime
import re
from collections import defaultdict
from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPNoContent, HTTPNotFound
import sqlalchemy
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from ...models.general_config import GeneralConfig
import transaction
import logging
from ...common.cache import Cache


# list
@view_config(
    route_name="admin.general.config", permission='admin', renderer="zhanor_admin:templates/admin/general/config/index.jinja2"
)
def index_view(request):
    settings = request.registry.settings
    config_groups = settings.get("config.groups", "base,dictionary,email").split(",")
    cache = Cache(settings)
    # cache.delete('general_configs')
    general_configs = []
    cached_data = cache.get("general_configs")

    if cached_data:

        general_configs_data = json.loads(cached_data)
        # Convert each dictionary to GeneralConfig instance
        general_configs = [
            GeneralConfig.from_dict(item) for item in general_configs_data
        ]
    else:
        general_configs = update_cache(request)

    configs = defaultdict(list)
    for item in general_configs:
        value_as_dict = (
            list(enumerate(json.loads(item.value).items()))
            if item.type == "array"
            else item.value
        )
        content_as_dict = (
            list(enumerate(json.loads(item.content)))
            if item.type == "select"
            else item.content
        )

        configs[item.group].append(
            {
                "id": item.id,
                "name": item.name,
                "group": item.group,
                "title": item.title,
                "tip": item.tip,
                "type": item.type,
                "visible": item.visible,
                "value": value_as_dict,
                "content": content_as_dict,
                "rule": item.rule,
                "extend": item.extend,
                "setting": item.setting,
            }
        )
    return {"config_groups": config_groups, "general_configs_list": configs}


# add
@view_config(
    route_name="admin.general.config.add", permission='admin', renderer="zhanor_admin:templates/admin/general/config/add.jinja2"
)
def add_view(request):
    if request.method == 'POST':
        
        general_config = GeneralConfig()
        if hasattr(GeneralConfig, 'createtime'):
            general_config.createtime = datetime.utcnow()
        for field in GeneralConfig.__table__.columns.keys():
            if field in request.POST and field != 'id':
                setattr(general_config, field, request.POST[field])
        if hasattr(GeneralConfig, 'updatetime'):
            general_config.updatetime = datetime.utcnow()
 
        try: 
            request.dbsession.add(general_config)   
            transaction.commit()
        except (ValueError, OperationalError, sqlalchemy.exc.IntegrityError, sqlalchemy.exc.IntegrityError) as e:
            logging.error(f"Other error occurred: {e}")
            request.dbsession.rollback()
            return Response(
                json.dumps({"status": 0, "message": "An error has occurred", "data": {}}),
                content_type="application/json",
                charset="utf-8",
                status = 500
            )
        update_cache(request)
        return Response(
                json.dumps({'status': 1, 'message': 'Add Success', 'data': {}}),
                content_type="application/json",
                charset="utf-8",
                status = 200
            )
    else:
        settings = request.registry.settings
        config_groups = settings.get('config.groups', 'base,dictionary,email').split(',')
        return {"config_groups": config_groups,"value": {}}

@view_config(route_name="admin.general.config.save", permission='admin', renderer="json", request_method="POST")
def process_form_view(request):
    try:
        # 解析表单数据
        form_data = request.POST.items()
        data_to_json = {}
        pattern = re.compile(r"\[([^\[\]]+)\]")
        for key, value in form_data:
            match = pattern.findall(key)
            if match:
                name = match[0]
                if len(match) > 1:
                    if name not in data_to_json:
                        data_to_json[name] = {}
                    sub_dict = data_to_json[name]
                    for subkey in match[1:-1]:
                        if subkey not in sub_dict or not isinstance(
                            sub_dict[subkey], dict
                        ):
                            sub_dict[subkey] = {}
                        sub_dict = sub_dict[subkey]
                    sub_dict[match[-1]] = value
                save_or_update(request,name, value)
        for name, values in data_to_json.items():
            json_value = json.dumps(
                {
                    nested_dict["key"]: nested_dict["value"]
                    for _, nested_dict in values.items()
                }
            )
            save_or_update(request,name, json_value)
        update_cache(request)
    except Exception as e:
        return Response(
            json.dumps({"status": 0, "message": "An error has occurred", "data": {}}),
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
@view_config(
    route_name="admin.general.config.table.list",renderer="json", request_method="POST"
)
def table_list_view(request):
    engine = request.dbsession.bind
    inspector = sqlalchemy.Inspector.from_engine(engine)
    tables_list = inspector.get_table_names()
    return Response(
        json.dumps({"status": 1, "message": "Success", "data": tables_list}),
        content_type="application/json",
        charset="utf-8",
        status=200,
    )

def save_or_update(request,name, value):

    try:
        config = (
            request.dbsession.query(GeneralConfig).filter(GeneralConfig.name == name).first()
        )
        if config:
            config.value = value
        else:
            config = GeneralConfig(name=name, value=value)
            request.dbsession.add(config)
        transaction.commit()
    except Exception:
        # 发生错误时，由于已注册了全局异常处理器，此处无需手动回滚
        raise
# Upate Cache
def update_cache(request):
    query = request.dbsession.query(GeneralConfig)
    settings = request.registry.settings
    cache = Cache(settings)
    general_configs = query.all()  # Execute query and get all data

    dicts = [gc.to_dict() for gc in general_configs]
    json_data = json.dumps(dicts, default=str)  # Convert to JSON format
    cache.set("general_configs", json_data, expire=3600 * 24 * 3)
    return general_configs
# delete
@view_config(
    route_name="admin.general.config.delete", permission='admin', renderer="json", request_method="DELETE"
)
def delete_general_config_view(request):
    data = json.loads(request.body)
    general_config_id = data.get("id", None)
    if not general_config_id:
        return Response(
            json.dumps({"status": 0, "message": _("Error,Need User ID"), "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500,
        )
    try:
        general_config = (
            request.dbsession.query(GeneralConfig)
            .filter(GeneralConfig.id == general_config_id)
            .one()
        )
        request.dbsession.delete(general_config)
        transaction.commit()
    except Exception as e:
        request.dbsession.rollback()
        return Response(
            json.dumps({"status": 0, "message": "An error has occurred", "data": {}}),
            content_type="application/json",
            charset="utf-8",
            status=500,
        )
    update_cache(request)
    return Response(
        json.dumps({"status": 1, "message": "Success", "data": {}}),
        content_type="application/json",
        charset="utf-8",
        status=200,
    )
