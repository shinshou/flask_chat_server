from flask_chat_server import db
from flask_chat_server.models import User

db.drop_all()

db.create_all()


admin = User(
    email="admin_user@test.com",
    username="Admin User",
    password="adminuser9182",
    administrator="1",
)
db.session.add(admin)
db.session.commit()
