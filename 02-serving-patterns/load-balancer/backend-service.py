from flask import Flask, jsonify, request
import os
import time
import random
import socket
from datetime import datetime

app = Flask(__name__)

# 获取服务器标识信息
SERVER_ID = os.environ.get('SERVER_ID', socket.gethostname())
PORT = int(os.environ.get('PORT', 8000))

# 模拟服务器负载
server_load = random.uniform(0.1, 0.9)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    # 模拟偶发的健康问题
    if random.random() < 0.05:  # 5%的概率返回不健康状态
        return jsonify({
            "status": "unhealthy",
            "server_id": SERVER_ID,
            "timestamp": datetime.now().isoformat()
        }), 503
    
    return jsonify({
        "status": "healthy",
        "server_id": SERVER_ID,
        "port": PORT,
        "load": server_load,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/info', methods=['GET'])
def get_info():
    """返回服务器信息"""
    # 模拟不同的响应时间
    processing_time = random.uniform(0.1, 0.5)
    time.sleep(processing_time)
    
    return jsonify({
        "server_id": SERVER_ID,
        "port": PORT,
        "hostname": socket.gethostname(),
        "processing_time": processing_time,
        "current_load": server_load,
        "timestamp": datetime.now().isoformat(),
        "client_ip": request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    })

@app.route('/api/data', methods=['GET'])
def get_data():
    """返回模拟数据"""
    # 模拟数据处理时间
    processing_time = random.uniform(0.2, 1.0)
    time.sleep(processing_time)
    
    data = [
        {"id": i, "value": random.randint(1, 100), "server": SERVER_ID}
        for i in range(1, 11)
    ]
    
    return jsonify({
        "data": data,
        "server_info": {
            "id": SERVER_ID,
            "port": PORT,
            "processing_time": processing_time
        },
        "metadata": {
            "count": len(data),
            "generated_at": datetime.now().isoformat()
        }
    })

@app.route('/api/session', methods=['GET', 'POST'])
def handle_session():
    """处理会话数据（用于测试会话保持）"""
    if request.method == 'POST':
        session_data = request.get_json() or {}
        response = {
            "message": "Session data received",
            "server_id": SERVER_ID,
            "received_data": session_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # 设置会话cookie
        resp = jsonify(response)
        resp.set_cookie('server_affinity', SERVER_ID)
        return resp
    
    else:
        # GET请求，返回会话信息
        affinity_cookie = request.cookies.get('server_affinity')
        return jsonify({
            "server_id": SERVER_ID,
            "session_cookie": affinity_cookie,
            "is_sticky_session": affinity_cookie == SERVER_ID,
            "timestamp": datetime.now().isoformat()
        })

@app.route('/api/load-test', methods=['GET'])
def load_test():
    """负载测试端点"""
    # 模拟CPU密集型任务
    iterations = int(request.args.get('iterations', 10000))
    start_time = time.time()
    
    result = 0
    for i in range(iterations):
        result += i ** 2
    
    processing_time = time.time() - start_time
    
    return jsonify({
        "server_id": SERVER_ID,
        "iterations": iterations,
        "result": result,
        "processing_time": processing_time,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus格式的指标"""
    return f"""# HELP requests_total Total number of requests
# TYPE requests_total counter
requests_total{{server_id="{SERVER_ID}"}} {random.randint(100, 1000)}

# HELP current_load Current server load
# TYPE current_load gauge
current_load{{server_id="{SERVER_ID}"}} {server_load}

# HELP response_time_seconds Response time in seconds
# TYPE response_time_seconds histogram
response_time_seconds_sum{{server_id="{SERVER_ID}"}} {random.uniform(10, 100)}
response_time_seconds_count{{server_id="{SERVER_ID}"}} {random.randint(50, 200)}
""", 200, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    print(f"Starting backend server {SERVER_ID} on port {PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
