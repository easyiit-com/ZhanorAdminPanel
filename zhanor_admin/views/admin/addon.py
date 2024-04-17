# addon.py
from datetime import datetime
import json
import os
import shutil
import uuid
import zipfile

from pyramid.view import view_config
from pyramid.response import Response
from zhanor_admin.common.defs import download_file, unzip_file, zipdir
from zhanor_admin.models import get_engine
from ...models.addon import Addon
import logging
import requests
from sqlalchemy import text, MetaData


# list
@view_config(
    route_name="admin.addon",
    permission="admin",
    renderer="zhanor_admin:templates/admin/addon/index.jinja2",
)
def index_view(request):
    settings = request.registry.settings
    page = int(request.GET.get("page", 1))
    per_page = 20
    pages = 1
    api_url = request.registry.settings["api.url"]
    data = {"username": "user", "password": "pass"}
    headers = {"Content-Type": "application/json"}
    network_addon_list = []
    
    try:
        response = requests.post(f'{api_url}?page={page}', data=data, headers=headers, timeout=3600)
        if response.status_code == 200:
            data = response.json()
            for plugin in data["data"]["plugins_list"]:
                addon = Addon(**plugin) 
                addon.installed = (
                    "1" if is_plugin_installed(request, addon.uuid) else "0"
                )
                addon.enabled = "1" if is_plugin_enabled(request, addon.uuid) else "0"
                addon.setting_menu = json.loads(addon.setting_menu)
                network_addon_list.append(addon)
            pages = data["data"]["total_pages"]
    except Exception as e:
        logging.error(f"Error: {e}")

    local_addon_list = []

    plugins_directory = settings.get("plugins.directory", "plugins")
    for root, dirs, files in os.walk(plugins_directory):
        local_dirs = [d for d in dirs if d.endswith("_local")]
        id = 1
        for local_dir in local_dirs:
            plugin_json_path = os.path.join(root, local_dir, "plugin.json")
            addon_info = None
            if os.path.isfile(plugin_json_path):
                with open(plugin_json_path, "r") as f:
                    plugin_data = json.load(f)
                    addon_info = plugin_data['info']
            if addon_info:
                # try:
                #     addon_info["setting_menu"] = json.loads(addon_info["setting_menu"])  # 转换为字典
                # except json.JSONDecodeError:
                #     addon_info["setting_menu"] = {}
                data_for_addon = {
                    "id":id,
                    "title": addon_info.get("title"),  # 假设'名称'映射到'title'
                    "author": addon_info["author"],
                    "uuid": addon_info.get("uuid", ""),  # 如果JSON中无uuid则生成新的
                    "description": addon_info["description"],
                    "version": addon_info["version"],
                    "downloads": 0,
                    "download_url": addon_info.get("download_url", ""),
                    "md5_hash": addon_info.get("md5_hash", ""),
                    "price": addon_info.get("price", "0.00"),
                    "paid": addon_info.get("paid", "0"),
                    "installed": addon_info.get("installed", "0"),
                    "enabled": "1" if is_plugin_enabled(request, addon_info.get("uuid", "none")) else "0",
                    "setting_menu":addon_info.get("setting_menu", []),
                    "createtime": datetime.strptime(
                        addon_info["updatetime"], "%Y-%m-%d"
                    ),
                    "updatetime": datetime.strptime(
                        addon_info["updatetime"], "%Y-%m-%d"
                    ),
                }

                # 将字典转换为Addon实例
                new_addon = Addon(**data_for_addon)
                local_addon_list.append(new_addon)
                id += id

    return {
        "network_addon_list": network_addon_list,
        "local_addon_list": local_addon_list,
        "current_page": page,
        "total_pages": pages,
    }


@view_config(
    route_name="admin.addon.download",
    permission="admin",
    renderer="json",
    request_method="POST",
)
def download_view(request):
    url = ""
    dest_path = ""
    resp = requests.get(url)
    if resp.status_code == 200:
        with open(dest_path, "wb") as f:
            f.write(resp.content)
        return True
    return False


@view_config(
    route_name="admin.addon.install",
    permission="admin",
    renderer="json",
    request_method="POST",
)
def install_view(request):
    # try:
    addon_id = request.POST.get("addon_id")
    api_url = request.registry.settings["api.url"]
    data = {"username": "user", "addon_id": addon_id}
    headers = {"Content-Type": "application/json"}
    # headers = {"Content-Type": "application/x-www-form-urlencoded"}
    url = f'{api_url}/details'
    response = requests.post(url, data=json.dumps(data), headers=headers)
    logging.info(f"install_view url:{url}")
    logging.info(f"install_view response:{response.status_code}==={response}")
    if response.status_code == 200:
        data = response.json()['data']
        logging.info(f"response={data}")
        uuid = data["uuid"]
        logging.info(f"response={uuid}")
        settings = request.registry.settings
        plugins_directory = settings.get("plugins.directory", "plugins")
        static_directory = settings.get("static.directory", "static")
        download_url = data["download_url"]
        plugin_download_file = download_file(download_url, plugins_directory)
        plugin_static_folder = os.path.join(plugins_directory, f"{uuid}/static")
        if plugin_download_file:
            logging.info(f"plugin {uuid} download successful")
            unzip_file(plugin_download_file, plugins_directory)
            update_pligin_status(request, uuid, "enabled")
            staitcfiles = f"{static_directory}/addon/{uuid}"
            if os.path.exists(staitcfiles):
                shutil.rmtree(staitcfiles)
            shutil.copytree(
                plugin_static_folder, staitcfiles
            )
            os.remove(plugin_download_file)
        else:
            return Response(
                json.dumps(
                    {"status": 0, "message": "Json file no exits", "data": data}
                ),
                content_type="application/json",
                charset="utf-8",
                status=200,
            )
    # except Exception as e:
    #     return Response(
    #         json.dumps(
    #             {"status": 0, "message": f"An error has occurred :{e}", "data": {}}
    #         ),
    #         content_type="application/json",
    #         charset="utf-8",
    #         status=500,
    #     )
    return Response(
        json.dumps({"status": 1, "message": "Success", "data": {}}),
        content_type="application/json",
        charset="utf-8",
        status=200,
    )


@view_config(
    route_name="admin.addon.uninstall",
    permission="admin",
    renderer="json",
    request_method="POST",
)
def uninstall_view(request):
    # try:
    addon_id = request.POST.get("addon_id")
    api_url = request.registry.settings["api.url"]
    data = {"username": "user", "id": addon_id}
    # headers = {"Content-Type": "application/json"}
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(f'{api_url}/details/{addon_id}', data=data, headers=headers)

    if response.status_code == 200:
        data = response.json()
        uuid = data["uuid"]
        settings = request.registry.settings
        plugins_directory = settings.get("plugins.directory", "plugins")
        static_directory = settings.get("static.directory", "static")
        plugin_static_directory = os.path.join(static_directory, f"addon/{uuid}")
        plugin_folder = os.path.join(plugins_directory, uuid)
        manifest_path = os.path.join(plugin_folder, "plugin.json")
        plugins_status_file = os.path.join(plugins_directory, "plugins_status.json")
        with open(plugins_status_file, "r") as f:
            plugins_status_data = json.load(f)
            if uuid in plugins_status_data:
                del plugins_status_data[uuid]
                with open(plugins_status_file, "w") as f:
                    json.dump(plugins_status_data, f, indent=4)
            else:
                logging.error(f"uuid is no exist")

        if os.path.exists(manifest_path):
            with open(manifest_path, "r") as f:
                manifest = json.load(f)
                tables = manifest.get("tables", [])
                logging.info(f"manifest.get.tables====>{tables}")

                remove_data_tables(request, tables)
                remove_plugin_directory(
                    plugins_directory, plugin_folder, plugin_static_directory
                )
        else:
            return Response(
                json.dumps(
                    {"status": 0, "message": "Json file no exits", "data": data}
                ),
                content_type="application/json",
                charset="utf-8",
                status=200,
            )
    # db_engine = engine_from_config(db_settings, 'sqlalchemy.')
    # with db_engine.connect() as conn:
    #     conn.execute(text("DROP TABLE IF EXISTS your_table;")) # 替换成实际的表名

    # # 删除static目录中的JS
    # os.remove(os.path.join(static_dest, 'your_plugin.js'))
    # except Exception as e:
    #     return Response(
    #         json.dumps({"status": 0, "message": f"An error has occurred:{e}", "data": {}}),
    #         content_type="application/json",
    #         charset="utf-8",
    #         status=500,
    #     )
    return Response(
        json.dumps({"status": 1, "message": "Success", "data": {}}),
        content_type="application/json",
        charset="utf-8",
        status=200,
    )


@view_config(
    route_name="admin.addon.update.status",
    permission="admin",
    renderer="json",
    request_method="POST",
)
def update_status(request):
    plugin_name = request.POST.get("plugin_name")
    status = request.POST.get("status")
    try:
        update_pligin_status(request, plugin_name, status)
    except Exception as e:
        return Response(
            json.dumps({"status": 0, "message": "Error:{e}", "data": {}}),
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


def is_plugin_installed(request, plugin_uuid):
    settings = request.registry.settings
    plugins_directory = settings.get("plugins.directory", "plugins")
    plugins_folder = os.path.join(plugins_directory, plugin_uuid)
    return os.path.isdir(plugins_folder)


def is_plugin_enabled(request, plugin_uuid):
    settings = request.registry.settings
    plugins_directory = settings.get("plugins.directory", "plugins")
    plugins_status_file = os.path.join(plugins_directory, "plugins_status.json")
    with open(plugins_status_file) as f:
        plugins_status = json.load(f)

    return plugins_status.get(plugin_uuid) == "enabled"


# def is_plugin_installed(plugin_name):
#     try:
#         with open('plugins_status.json') as f:
#             plugins_status = json.load(f)
#         return plugin_name in plugins_status and plugins_status[plugin_name] == 'installed'
#     except FileNotFoundError:
#         return False


def install_plugin(request, plugin_name, enable=True):
    # 定义插件状态文件路径
    status_file = "plugins_status.json"

    # 检查文件是否存在，如果不存在则创建一个空的字典
    if not os.path.exists(status_file):
        plugins_status = {}
    else:
        # 读取现有的插件状态
        with open(status_file, "r") as f:
            plugins_status = json.load(f)

    # 更新或添加插件状态
    status = "enabled" if enable else "disabled"
    plugins_status[plugin_name] = status

    # 写回文件
    with open(status_file, "w") as f:
        json.dump(plugins_status, f, indent=4)

    logging.info(
        f"Plugin '{plugin_name}' has been installed and {'enabled' if enable else 'disabled'}."
    )


def update_pligin_status(request, plugin_uuid, status):
    settings = request.registry.settings
    plugins_directory = settings.get("plugins.directory", "plugins")
    with open(plugins_directory + "/plugins_status.json") as f:
        plugins_status = json.load(f)
    plugins_status[plugin_uuid] = status
    try:
        with open(plugins_directory + "/plugins_status.json", "w") as f:
            json.dump(plugins_status, f, indent=4)
    except Exception as e:
        raise


def remove_plugin_directory(source_dir, plugin_dir, plugin_static_directory):
    random_code = str(uuid.uuid4()).replace("-", "")[:8]
    output_zip_file = f"{os.path.basename(plugin_dir)}_{random_code}.zip"
    with zipfile.ZipFile(output_zip_file, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipdir(source_dir, zipf)
    if os.path.isdir(plugin_dir):
        shutil.rmtree(plugin_dir)
        logging.info(f"Plugin directory {plugin_dir} has been removed")
    else:
        logging.info(
            f"Plugin directory {plugin_dir} does not exist or has already been removed"
        )
    if os.path.isdir(plugin_static_directory):
        shutil.rmtree(plugin_static_directory)
        logging.info(f"Plugin directory {plugin_static_directory} has been removed")
    else:
        logging.info(
            f"Plugin directory {plugin_static_directory} does not exist or has already been removed"
        )


def remove_data_tables(request, tables):
    settings = request.registry.settings
    engine = get_engine(settings)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    for table_name in tables:
        table_to_drop = metadata.tables.get(table_name)
        if table_to_drop is not None:
            table_to_drop.drop(engine)


def remove_static_files(static_files, plugin_dir):

    for file_path in static_files:
        full_path = os.path.join(plugin_dir, file_path)
        if os.path.exists(full_path):
            os.remove(full_path)
        # 检查是否为空目录，如果是，则删除它
        dir_path = os.path.dirname(full_path)
        if len(os.listdir(dir_path)) == 0:
            shutil.rmtree(dir_path)


def remove_menu_items(menu_items):
    # 删除菜单项的逻辑，根据实际情况编写
    pass
