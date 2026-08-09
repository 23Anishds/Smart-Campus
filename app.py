from flask import Flask, redirect, url_for, session, render_template
import os

from config import AppConfig
# We'll import blueprints here as we create them
# from routes.auth import auth_bp
# from routes.dashboard import dashboard_bp
# from routes.students import students_bp
# from routes.attendance import attendance_bp
# ...

def create_app() -> Flask:
    app = Flask(__name__)
    config = AppConfig.get_config()
    app.config['SECRET_KEY'] = config.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.students import students_bp
    from routes.attendance import attendance_bp
    from routes.analytics import analytics_bp
    from routes.registration import registration_bp
    from routes.timetable import timetable_bp
    from routes.admin import admin_bp
    from routes.portal import portal_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(registration_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(portal_bp)

    @app.route('/')
    def index():
        if 'user_id' in session:
            role = session.get('role', 'student')
            if role == 'admin':
                return redirect('/admin')
            elif role == 'teacher':
                return redirect('/dashboard')
            else:
                return redirect('/portal')
        return render_template('landing.html')

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
