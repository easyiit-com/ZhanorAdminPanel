import json
import logging
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from pyramid.csrf import CookieCSRFStoragePolicy
from zhanor_admin.security import CustomSecurityPolicy


def main(global_config, **settings):
    my_session_factory = SignedCookieSessionFactory(secret="itsaseekreet")
    with Configurator(settings=settings) as config:

        admin_auth_secret = settings.get("admin.auth.secret ", "zhanor_niu")
        jwt_auth_secret = settings.get("jwt.secret", "zhanor_jin")
        config.set_security_policy(
            CustomSecurityPolicy(admin_auth_secret, jwt_auth_secret)
        )
        # jinja2
        config.include("pyramid_jinja2")
        # models
        config.include(".models")
        # routes
        config.include(".routes")
        # subscribers
        config.include(".subscribers")

        # csrf
        config.set_csrf_storage_policy(CookieCSRFStoragePolicy())
        config.set_default_csrf_options(require_csrf=True)

        # Set session factory
        config.set_session_factory(my_session_factory)
        # Internationalization support
        config.add_translation_dirs("zhanor_admin:locales")

        # Include enabled plugins
        plugins_directory = settings.get("plugins.directory", "plugins")
      
        try:
            with open(plugins_directory + "/plugins_status.json", 'r') as f:
                plugins_status = json.load(f)
        except FileNotFoundError:
            plugins_status = {}
        except json.JSONDecodeError: 
            with open(plugins_directory + "/plugins_status.json", 'w') as f:
                f.truncate(0)
            plugins_status = {}

        for key, value in plugins_status.items():
            if value == "enabled":
                plugin_name = key
                config.include(f".plugins.{plugin_name.strip()}")
        config.registry.settings["plugins_status"] = plugins_status

        # upload
        # Store upload configurations in the registry
        config.registry.settings["upload_to"] = settings["upload.directory"]
        config.registry.settings["allowed_image_extensions"] = settings[
            "upload.image.extensions"
        ]
        config.registry.settings["allowed_file_extensions"] = settings[
            "upload.file.extensions"
        ]
        config.registry.settings["max_size"] = int(settings["upload.max_size"])
        config.registry.settings["max_count"] = int(settings["upload.max_count"])
        config.scan()
    return config.make_wsgi_app()
