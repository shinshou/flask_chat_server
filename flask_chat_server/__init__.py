import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)

# csrf対策
app.config["SECRET_KEY"] = "mysecretkey"

# IPアドレスごとのリクエスト制限
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379",
)

CORS(
    app,
    resources={
        r"/chat_session": {
            "origins": [
                "http://localhost:8080",
            ],
            "methods": ["GET"],
        },
        r"/save_chat": {
            "origins": [
                "http://localhost:8080",
            ],
            "methods": ["POST"],
        },
        r"/chat_sse": {
            "origins": [
                "http://localhost:8080",
            ],
            "methods": ["GET"],
        },
    },
    supports_credentials=True,
)

basedir = os.path.abspath(os.path.dirname(__file__))
# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
#     basedir, "data.sqlite"
# )
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "mysql+pymysql://dbuser:Ssenj_20230815@localhost/flaskserver"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "users.login"


def localize_callback(*argds, **kwargs):
    return "このページにアクセスするには、ログインが必要です。"


login_manager.localize_callback = localize_callback

from sqlalchemy.engine import Engine
from sqlalchemy import event


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# from flask_chat_server.users.views import users
from flask_chat_server.error_pages.handlers import error_pages
from flask_chat_server.main.views import main

# app.register_blueprint(users)
app.register_blueprint(error_pages)
app.register_blueprint(main)
