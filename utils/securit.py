from passlib.context import CryptContext

#创建密码上下问
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#加密
def get_hash_password(password: str):
    return pwd_context.hash(password)
#验证
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)