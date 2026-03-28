from flask import Flask, jsonify
import os
import datetime

app = Flask(__name__)

# Health check endpoint — ALB will ping this to verify the container is alive
@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200

# Main endpoint
@app.route('/')
def index():
    return jsonify({
        "message": "Flask API running on ECS",
        "version": "1.0",
        "environment": os.getenv("ENVIRONMENT", "local")
    }), 200

# Status endpoint — demonstrates reading environment variables (used heavily in ECS)
@app.route('/status')
def status():
    return jsonify({
        "app": "flask-ecs-api",
        "db_host": os.getenv("DB_HOST", "not-configured"),
        "region": os.getenv("AWS_REGION", "not-configured")
    }), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)