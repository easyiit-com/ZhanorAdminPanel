import logging
import time
import jwt
from pyramid.authentication import AuthTktCookieHelper
from pyramid.authorization import ACLHelper
from pyramid.security import Everyone, Authenticated 
from pyramid.request import RequestLocalCache
from zhanor_admin import models

class CustomSecurityPolicy:
    def __init__(self, admin_secret, jwt_secret):
        self.secret = admin_secret
        self.jwt_secret = jwt_secret
        self.authtkt = AuthTktCookieHelper(admin_secret)
        self.user_authtkt = AuthTktCookieHelper(jwt_secret,cookie_name = 'user_tkt')
        self.identity_cache = RequestLocalCache(self.load_identity)
        self.acl = ACLHelper() 
 
    def load_identity(self, request):
        user = None
        request.role = None
        if request.path.startswith('/admin'):
            identity = self.authtkt.identify(request)
            if identity is not None:
                userid = identity['userid']
                # tokens = identity['tokens']
                if(userid):
                    user = request.dbsession.query(models.AdminUser).get(userid)  
            if user:
                request.role = 'admin'
                request.admin = user
            return user
        else:
            identity = self.user_authtkt.identify(request)
            if identity is not None:
                userid = identity['userid']
                if(userid):
                    user = request.dbsession.query(models.UserUser).get(userid)  
            else:
                auth_header = request.headers.get('Authorization')
                if auth_header:
                    token = auth_header.split(' ')[1]
                else:
                    token = request.params.get('token')
                if token:
                    try:
                        decoded_token = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
                        expiration_time = decoded_token.get("exp")
                        now = int(time.time())
                        if expiration_time is not None and now < expiration_time:
                            userid = decoded_token.get('userid')
                            user = request.dbsession.query(models.UserUser).get(userid)
                    except jwt.PyJWTError:
                        pass
               
            if user:
                request.role = 'user'
                request.user = user
            return user
        
        
    def identity(self, request):
        return self.identity_cache.get_or_create(request)

    def authenticated_userid(self, request):
        user = self.identity(request)
        if user is not None:
            return user.id
    def remember(self, request, userid, role="user", **kw):
        if role == 'admin':
            return self.authtkt.remember(request, userid, max_age=86400,**kw)
        else:
            return self.user_authtkt.remember(request, userid, max_age=86400,**kw) 

    def forget(self, request, role="user", **kw):
        if role == 'user':
           return self.user_authtkt.forget(request, **kw)
        else:
           return self.authtkt.forget(request, **kw)

    def permits(self, request, context, permission):
        principals = self.effective_principals(request)
        return self.acl.permits(context, principals, permission)

    def effective_principals(self, request):
        principals = [Everyone]
        principals.append('role:view')
        user = self.identity(request)
        if user is not None:
            principals.append(Authenticated)
            if request.path.startswith('/admin') and request.role=='admin':
                principals.append('role:admin')
            else:
                principals.append('role:user')
        return principals