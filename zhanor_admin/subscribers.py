import os
import random
from pyramid.events import NewRequest, BeforeRender, ContextFound, BeforeTraversal
import logging
import json
import re
import transaction

from zhanor_admin.models.user_user import UserUser

 
from .models.admin_user import AdminUser
from .common.defs import mask_password, now
from .models import admin_log
from .common.languages import languages
from .common.cache import Cache
from .models.general_config import GeneralConfig
from pyramid.settings import aslist
from pyramid.i18n import get_localizer, get_locale_name, TranslationStringFactory
from collections import defaultdict 


_ = TranslationStringFactory("zhanor_admin")

def all_languages():
    return languages


def country2flag(country_code):
    if "-" in country_code:
        country_code = country_code.split("-")[1]
    elif "_" in country_code:
        country_code = country_code.split("_")[1]

    if country_code == "el":
        country_code = "gr"
    elif country_code == "da":
        country_code = "dk"

    return re.sub(r".", lambda x: chr(ord(x.group()) % 32 + 0x1F1E5), country_code)

def add_global_template_vars(event):
    request = event.get("request")
    settings = request.registry.settings
    cache = Cache(settings)
    if request:
        view_name = getattr(request.matched_route, "name", "index")
        event["view_name"] = "/".join(view_name.split(".")[:-1])
        event["view_name"] = view_name.replace(".", "/")
        if request.matched_route:
            current_route_name = request.matched_route.name.replace(".", "/").replace(
                "_", "/"
            )
            event["current_route"] = f"/{current_route_name}"
        else:
            event["current_route"] = ""
        event["current_path"] = request.path
        parts = request.path.rsplit("/", 2)
      
        event["current_parent_path"] = "/".join(parts[:2]).replace("/edit", "").replace("/add", "")

        event["admin_rules"] = request.registry.admin_rules

        event["user_rules"] = request.registry.user_rules

        general_configs = []
        cached_data = cache.get("general_configs")

        if cached_data:
            general_configs_data = json.loads(cached_data)
            general_configs = [
                GeneralConfig.from_dict(item) for item in general_configs_data
            ]
        else:
            query = request.dbsession.query(GeneralConfig)
            general_configs = query.all()  # Execute query and get all data

            dicts = [gc.to_dict() for gc in general_configs]
            json_data = json.dumps(dicts, default=str)  # Convert to JSON format
            cache.set("general_configs", json_data, expire=3600 * 24 * 3)
            
        configs = defaultdict(dict)
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
            configs[item.group][item.name] = value_as_dict
        event["configs"] = configs 

def add_localizer(event):
    request = event.request
    localizer = get_localizer(request)
    request.localizer = localizer 


def set_language_from_route(event):
    request = event.request
    SUPPORTED_LANGUAGES = ["en", "zh"]
    DEFAULT_LANGUAGE = "en"

    if request.matchdict and "lang" in request.matchdict:
        lang = request.matchdict.get("lang", DEFAULT_LANGUAGE)
    else:
        lang = DEFAULT_LANGUAGE

    if lang:
        if lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE
    request.locale_name = lang 


def add_renderer_globals(event):
    request = event["request"]

    # SUPPORTED_LANGUAGES = ['en', 'zh']  # 示例支持的语言代码
    # DEFAULT_LANGUAGE = 'en'  # 默认语言
    # lang = request.matchdict.get('lang', DEFAULT_LANGUAGE)
    # if lang:
    #         # 检查语言代码是否在支持的列表中
    #     if lang not in SUPPORTED_LANGUAGES:
    #         lang = DEFAULT_LANGUAGE  # 使用默认语言
    #     request.locale_name = lang 

    #
    event["settings"] = request.registry.settings
    event["all_languages"] = all_languages()
    event["languages"] = aslist(request.registry.settings["available_languages"])
    event["country2flag"] = country2flag
    event["localizer"] = request.localizer
    event["locale_name"] = get_locale_name(request)
    event["logging"] = logging.getLogger(__name__)
    
    # icons
    
    static_directory = request.registry.settings.get("static.directory", "static")
    with open(f'{static_directory}/icons.json', 'r') as file:
        icons = json.load(file)
    event["icons"] = random.sample(icons, 100)
 
    # javascript_locales
    static_directory = request.registry.settings.get("static.directory", "static")
    folder_path = os.path.join(static_directory, 'assets','js')
    js_translations = find_translations_in_js_files(folder_path)
    javascript_locales = json.dumps(js_translations, ensure_ascii=False, indent=2)
    
    event["javascript_locales"] = javascript_locales
    
def find_translations_in_js_files(directory):
    translations = {}
    
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith(".js"):
                file_path = os.path.join(root, file_name)                
                with open(file_path, 'r', encoding='utf-8') as js_file:
                    content = js_file.read()
                    matches = re.findall(r'_\(\s*["\'](.+?)["\']\s*\)', content)
                    for match in matches:
                        translations[match] = f'"{_(match)}"'                       
    return translations

def add_breadcrumbs(event):
    request = event["request"]
    route_name = request.matched_route.name if request.matched_route else ""
    event["breadcrumbs"] = process_string(route_name.replace("admin.", "", 1))
    event["title"] = request.registry.route_title.get(route_name, "")
    event["description"] = request.registry.route_descriptions.get(route_name, "")


def process_string(s):
    parts = s.split(".")
    back_to_dashboard = f'<i class="ti ti-chevron-left page-pretitle flex items-center"></i><a href="/admin/dashboard" class="page-pretitle flex items-center">{_("Back To Dashboard")}</a>'
    if s == "dashboard":
        return (
            f'<a class="page-pretitle flex items-center" href="#">{_("Dashboard")}</a>'
        )
    if len(parts) == 1:
        return f'{back_to_dashboard}<a class="page-pretitle flex items-center" href="#">/{parts[0].capitalize()}</a>'
    elif len(parts) == 2:
        title = s.rsplit(".", maxsplit=1)[0].replace("_", "/")
        return f'{back_to_dashboard}<span class="page-pretitle flex items-center">/</span><a class="page-pretitle flex items-center" href="/admin/{title}/{parts[1]}">{parts[0].capitalize().replace("_"," ")}{parts[1].capitalize()}</a>'
    elif len(parts) == 3:
        title = s.rsplit(".", maxsplit=1)[0].replace(".", "/")
        return f'{back_to_dashboard}<span class="page-pretitle flex items-center">/</span><a class="page-pretitle flex items-center" href="/admin/{title}">{parts[0].capitalize().replace("_"," ")}{parts[1].capitalize()}</a><span class="page-pretitle flex items-center">/ {parts[2].capitalize()}</span>'
    else:
        return ""

def log_request(event):
    request = event.request
    keywords_set = {"save", "delete", "login", "add", "register", "forgot_password",'profile'}
    user = getattr(request, "admin", None)
    admin_id = getattr(user, "id", 0)
    username = getattr(user, "name", 'none')
    if request.path.startswith('/admin') and request.role=='admin' and any(keyword in request.path for keyword in keywords_set):
        if request.method == "POST" or request.method == "DELETE": 
            if 'login' in request.path or 'register' in request.path or 'forgot_password' in request.path or 'profile' in request.path:
                data = request.POST.mixed()
                data = mask_password(dict(data))
            else:
                if request.method == "POST":
                    data = request.POST.mixed()
                else:
                    data = json.loads(request.body)
            admin_log_entry = admin_log.AdminLog(
                admin_id=admin_id,
                username="admin",
                url=request.path_url,
                title=request.method,
                content=str(data),
                ip=request.remote_addr,
                useragent=request.user_agent,
                createtime=now(request),
            )
            request.dbsession.add(admin_log_entry)
            transaction.commit()
            
 
          
            
def user(event):
    request = event.get("request")
    user = None
    user_id = request.authenticated_userid if(request is not None and hasattr(request,'authenticated_userid')) else None
    if user_id:
        if request.path.startswith('/admin') and request.role=='admin':
            user = request.dbsession.query(AdminUser).get(user_id)
            event["user"] = user
        else:
            user = request.dbsession.query(UserUser).get(user_id)
            event["user"] = user
 

 
def includeme(config):
    config.add_subscriber(user, BeforeRender)
    config.add_subscriber(add_global_template_vars, BeforeRender)
    config.add_subscriber(add_localizer, NewRequest)
    config.add_subscriber(set_language_from_route, ContextFound)
    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.add_subscriber(add_breadcrumbs, BeforeRender)
    config.add_subscriber(log_request, NewRequest)
    
    config.include('pyramid_tm')
