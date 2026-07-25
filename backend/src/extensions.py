"""
Extensions Layer.
Ref: backend master prompt, "Step 2: Extensions".

Instantiates Flask extensions WITHOUT binding them to an app instance.
Binding happens in the application factory (src/__init__.py) via each
extension's init_app(app) call. This is what lets create_app() be called
more than once (the real app, plus a fresh instance per test run) without
extension state leaking between instances -- a module-level
`app = Flask(__name__)` singleton could not do this safely.
"""
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
ma = Marshmallow()
