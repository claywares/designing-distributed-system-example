from flask import Flask, jsonify, request
import logging
import json
import time
import random
from datetime import datetime

app = Flask(__name__)

# 配置日志输出到文件，供边车容器收集
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/app/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 模拟用户数据
users = [
    {"id": 1, "name": "Alice", "email": "alice@example.com"},
    {"id": 2, "name": "Bob", "email": "bob@example.com"},
    {"id": 3, "name": "Charlie", "email": "charlie@example.com"}
]

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    logger.info("Health check requested")
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/api/users', methods=['GET'])
def get_users():
    """获取所有用户"""
    # 模拟随机响应时间
    time.sleep(random.uniform(0.1, 0.5))
    
    logger.info(f"Users list requested, returning {len(users)} users")
    
    return jsonify({
        "users": users,
        "count": len(users),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """获取指定用户"""
    # 模拟随机响应时间
    time.sleep(random.uniform(0.1, 0.3))
    
    user = next((u for u in users if u["id"] == user_id), None)
    
    if user:
        logger.info(f"User {user_id} requested")
        return jsonify(user)
    else:
        logger.warning(f"User {user_id} not found")
        return jsonify({"error": "User not found"}), 404

@app.route('/api/users', methods=['POST'])
def create_user():
    """创建新用户"""
    data = request.get_json()
    
    if not data or 'name' not in data or 'email' not in data:
        logger.error("Invalid user data provided")
        return jsonify({"error": "Name and email are required"}), 400
    
    new_user = {
        "id": max([u["id"] for u in users]) + 1,
        "name": data["name"],
        "email": data["email"]
    }
    
    users.append(new_user)
    logger.info(f"New user created: {new_user}")
    
    return jsonify(new_user), 201

@app.route('/api/simulate-error', methods=['GET'])
def simulate_error():
    """模拟错误，用于测试日志收集"""
    logger.error("Simulated error occurred!")
    return jsonify({"error": "This is a simulated error"}), 500

@app.route('/api/simulate-load', methods=['GET'])
def simulate_load():
    """模拟高负载，用于测试监控"""
    # 模拟CPU密集型任务
    start_time = time.time()
    result = 0
    for i in range(1000000):
        result += i ** 2
    
    duration = time.time() - start_time
    logger.info(f"Load simulation completed in {duration:.3f}s, result: {result}")
    
    return jsonify({
        "message": "Load simulation completed",
        "duration": duration,
        "result": result
    })

if __name__ == '__main__':
    logger.info("Starting Flask application")
    app.run(host='0.0.0.0', port=5000, debug=False)
