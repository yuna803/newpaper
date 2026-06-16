import redis.asyncio as redis
import json
redis_client = redis.Redis(host="localhost", port=6379, db=0,decode_responses=True)


#读取 字符串
async def get_str(key:str):
    try:
        return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败: {e}")
        return None

#读取 列表字典
async def get_json(key:str):
    try:
        data= await redis_client.get(key)   
        if data:
            return json.loads(data)
        return None
    except Exception as e:
        print(f"获取JSON缓存失败: {e}")
        return None

#设置缓存
async def set_cache(key:str, value, expire:int=3600):
    try:
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=False)
        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        print(f"设置缓存失败: {e}")
        return False