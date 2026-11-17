import os
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app import create_app

app = create_app()
CORS(app)

app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "change-this-in-production")
jwt = JWTManager(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
