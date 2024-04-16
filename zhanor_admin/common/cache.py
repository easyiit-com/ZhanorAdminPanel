import redis,os
import logging 
from beaker.cache import CacheManager
from beaker.util import parse_cache_config_options
from .logger import setup_logger

logger = setup_logger(__name__)
class Cache:
    def __init__(self, settings):
        cache_type = settings.get("cache.type", "file")
        # logger.info(f'Cache->__init__ cache_type={cache_type}')   
        if cache_type == "redis":
            host = settings.get("redis.host", "localhost")
            port = int(settings.get("redis.port", 6379))
            db = int(settings.get("redis.db", 0))
            socket_timeout = float(settings.get("redis.socket_timeout", 2))
            password = settings.get("redis.password")
            redis_params = {
                "host": host,
                "port": port,
                "db": db,
                "socket_timeout": socket_timeout,
            }

            # 如果存在密码，则添加到连接参数中
            if password is not None:
                redis_params["password"] = password

            try:
                self.r = redis.StrictRedis(**redis_params)
            except redis.ConnectionError as e:
                raise RuntimeError(f"Failed to connect to Redis: {e}") from e
        elif cache_type == "file":
            # 获取当前文件所在目录
            current_dir = os.path.dirname(os.path.abspath(__file__))

            # 计算父目录以及/cache/directory的完整路径
            cache_directory = os.path.join(os.path.dirname(current_dir), 'cache', 'directory')
            cache_data_dir = str(settings.get(
                "cache.data_dir", cache_directory
            ))
            # logger.info(f'cache_data_dir={cache_data_dir}')
            cache_opts = {
                "cache.type": "file",
                "cache.data_dir": cache_data_dir
            }
            self.cache_manager = CacheManager(**parse_cache_config_options(cache_opts))
            self.region = self.cache_manager.get_cache("default")  # 或者自定义区域名称
        else:
            raise ValueError(f"Unsupported cache type: {cache_type}")

    def get(self, key):
        # logger.info(f'Cache->get()==>get {key}')   
        if hasattr(self, "r"):
            try:
                return self.r.get(key)
            except redis.RedisError as e:
                logging.error(f"Redis error during GET: {e}")
                return None
        elif hasattr(self, "region"):
            try:
                value = self.region.get(key)
            except KeyError:
                value = None
            return value
         

    def set(self, key, value, expire=None):
        if hasattr(self, "r"):
            try:
                if expire is not None:
                    self.r.set(key, value, ex=expire)
                else:
                    self.r.set(key, value)
            except redis.RedisError as e:
                logging.error(f"Redis error during SET: {e}")
        elif hasattr(self, "region"):
            # Beaker不支持直接设置过期时间，需要通过配置文件或在创建区域时指定ttl
            self.region.put(key, value)
        # logger.info(f'Cache->set()==>set {key}')

    def delete(self, key):
        # logger.info(f'Cache->delete()==>delete {key}')
        if hasattr(self, "r"):
            return self.r.delete(key)
        elif hasattr(self, "region"):
            return self.region.remove(key)
        

    def flush_db(self):
        if hasattr(self, "r"):
            return self.r.flushdb()
        elif hasattr(self, "region"):
            # Beaker没有直接清空整个缓存的方法，只能逐个删除或者重新初始化缓存管理器
            self.region.clear()
        # logger.info(f'Cache->flush_db()==>delete cache all')


# # 在 Pyramid 应用启动时创建并使用缓存实例
# def main(global_config, **settings):
#     config = Configurator(settings=settings)

#     cache = Cache(config)

#     # ... 其他配置 ...

#     return config.make_wsgi_app()
