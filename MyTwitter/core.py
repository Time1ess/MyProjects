import redis
import config 


conn = redis.Redis(config.REDIS_HOST, config.REDIS_PORT,
                   decode_responses=config.DECODE_RESPONSE)
