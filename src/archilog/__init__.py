from flask import Flask


def create_app():
    app = Flask(__name__)
    app.secret_key = "change_this_secret_key_in_production"

    from archilog.views.gui import web_ui
    app.register_blueprint(web_ui, url_prefix="/")

    from archilog.auth_views import auth_ui
    app.register_blueprint(auth_ui, url_prefix="/auth")

    return app

