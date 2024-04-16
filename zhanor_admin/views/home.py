from docutils.core import publish_parts
from html import escape
from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPNotFound,
    HTTPSeeOther,
)
from pyramid.view import view_config
import re

 
@view_config(route_name='home', renderer='zhanor_admin:templates/home.jinja2')
def home_page(request):
    return dict(page={}, content={}, edit_url='edit_url')
 