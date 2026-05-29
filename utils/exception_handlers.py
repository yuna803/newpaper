from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from fastapi import HTTPException
from utils.exception import http_exception_handler,integrity_error_handler,general_exception_handler


"""全局异常处理"""

def register_exception_handlers(app):
    """
    注册异常处理器
    """
    #业务
    app.add_exception_handler(HTTPException, http_exception_handler)
    #数据完整性约束
    app.add_exception_handler(IntegrityError,integrity_error_handler)
    #数据库
    app.add_exception_handler(SQLAlchemyError, general_exception_handler)
    #兜底
    app.add_exception_handler(Exception, general_exception_handler)