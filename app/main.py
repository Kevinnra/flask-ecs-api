from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import datetime

app = Flask(__name__)

# Database configuration — reads from environment variables
# In ECS, these will be injected as task environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "flaskdb")
DB_USER = os.getenv("DB_USER", "flaskadmin")
DB_PASS = os.getenv("DB_PASS", "")

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Simple model — a log of every request hit
class RequestLog(db.Model):
    __tablename__ = 'request_logs'
    id = db.Column(db.Integer, primary_key=True)
    endpoint = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# Health check — ALB pings this (no DB call, keeps it fast)
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

# Root endpoint — logs the hit to DB and returns count
@app.route('/')
def index():
    try:
        log = RequestLog(endpoint='/')
        db.session.add(log)
        db.session.commit()
        count = RequestLog.query.count()
        return jsonify({
            "message": "Flask API running on ECS",
            "version": "2.0",
            "environment": os.getenv("ENVIRONMENT", "local"),
            "total_requests": count
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Status endpoint
@app.route('/status')
def status():
    return jsonify({
        "app": "flask-ecs-api",
        "db_host": DB_HOST,
        "region": os.getenv("AWS_REGION", "not-configured")
    }), 200

# DB init endpoint — creates tables (call this once after deploy)
@app.route('/init-db')
def init_db():
    try:
        db.create_all()
        return jsonify({"message": "Database tables created"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)