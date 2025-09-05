from flask import Flask, request, jsonify
import redis
import json
import uuid
from datetime import datetime
import logging

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 连接Redis
redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

# 队列名称定义
QUEUES = {
    'orders': 'order_queue',
    'users': 'user_queue', 
    'emails': 'email_queue',
    'notifications': 'notification_queue'
}

class MessageProducer:
    """消息生产者"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def send_message(self, queue_name, message_data, priority=0):
        """发送消息到队列"""
        message = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'data': message_data,
            'priority': priority,
            'retry_count': 0
        }
        
        message_json = json.dumps(message)
        
        # 使用Redis列表作为队列
        if priority > 0:
            # 高优先级消息放到队列前面
            self.redis.lpush(queue_name, message_json)
        else:
            # 普通消息放到队列后面
            self.redis.rpush(queue_name, message_json)
            
        # 记录消息发送指标
        self.redis.incr(f"{queue_name}:sent_count")
        
        logger.info(f"Message sent to {queue_name}: {message['id']}")
        return message['id']
    
    def get_queue_status(self, queue_name):
        """获取队列状态"""
        length = self.redis.llen(queue_name)
        sent_count = self.redis.get(f"{queue_name}:sent_count") or 0
        processed_count = self.redis.get(f"{queue_name}:processed_count") or 0
        
        return {
            'queue_name': queue_name,
            'length': length,
            'sent_count': int(sent_count),
            'processed_count': int(processed_count),
            'pending_count': length
        }

# 初始化消息生产者
producer = MessageProducer(redis_client)

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        redis_client.ping()
        return jsonify({
            'status': 'healthy',
            'service': 'message-producer',
            'redis_connection': 'ok',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 503

@app.route('/api/orders', methods=['POST'])
def create_order():
    """创建订单并发送到队列"""
    try:
        order_data = request.get_json()
        
        if not order_data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        # 验证必需字段
        required_fields = ['user_id', 'product', 'amount']
        if not all(field in order_data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # 添加订单ID和时间戳
        order_data['order_id'] = str(uuid.uuid4())
        order_data['created_at'] = datetime.now().isoformat()
        
        # 发送到订单处理队列
        message_id = producer.send_message(QUEUES['orders'], order_data)
        
        # 如果金额大于1000，设为高优先级
        if order_data['amount'] > 1000:
            # 发送高优先级通知
            notification_data = {
                'type': 'high_value_order',
                'order_id': order_data['order_id'],
                'amount': order_data['amount']
            }
            producer.send_message(QUEUES['notifications'], notification_data, priority=1)
        
        return jsonify({
            'message': 'Order created successfully',
            'order_id': order_data['order_id'],
            'message_id': message_id,
            'status': 'queued'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/users', methods=['POST'])
def register_user():
    """用户注册并发送欢迎消息"""
    try:
        user_data = request.get_json()
        
        if not user_data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        # 验证必需字段
        required_fields = ['username', 'email']
        if not all(field in user_data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # 添加用户ID和注册时间
        user_data['user_id'] = str(uuid.uuid4())
        user_data['registered_at'] = datetime.now().isoformat()
        
        # 发送到用户处理队列
        message_id = producer.send_message(QUEUES['users'], user_data)
        
        # 发送欢迎邮件消息
        email_data = {
            'to': user_data['email'],
            'template': 'welcome',
            'user_id': user_data['user_id'],
            'username': user_data['username']
        }
        email_message_id = producer.send_message(QUEUES['emails'], email_data)
        
        return jsonify({
            'message': 'User registered successfully',
            'user_id': user_data['user_id'],
            'message_id': message_id,
            'email_message_id': email_message_id,
            'status': 'queued'
        }), 201
        
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/messages', methods=['POST'])
def send_custom_message():
    """发送自定义消息"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        queue_name = data.get('queue')
        message_data = data.get('data')
        priority = data.get('priority', 0)
        
        if not queue_name or not message_data:
            return jsonify({'error': 'Queue name and data are required'}), 400
        
        if queue_name not in QUEUES.values():
            return jsonify({'error': f'Invalid queue name. Valid queues: {list(QUEUES.values())}'}), 400
        
        message_id = producer.send_message(queue_name, message_data, priority)
        
        return jsonify({
            'message': 'Message sent successfully',
            'message_id': message_id,
            'queue': queue_name,
            'priority': priority
        }), 201
        
    except Exception as e:
        logger.error(f"Error sending custom message: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/queue/status', methods=['GET'])
def get_all_queue_status():
    """获取所有队列状态"""
    try:
        status = {}
        for name, queue_name in QUEUES.items():
            status[name] = producer.get_queue_status(queue_name)
        
        return jsonify({
            'queues': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/queue/<queue_type>/status', methods=['GET'])
def get_queue_status(queue_type):
    """获取指定队列状态"""
    try:
        if queue_type not in QUEUES:
            return jsonify({'error': f'Invalid queue type. Valid types: {list(QUEUES.keys())}'}), 400
        
        queue_name = QUEUES[queue_type]
        status = producer.get_queue_status(queue_name)
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus格式的指标"""
    try:
        metrics_data = []
        
        for name, queue_name in QUEUES.items():
            status = producer.get_queue_status(queue_name)
            metrics_data.append(f'queue_length{{queue="{name}"}} {status["length"]}')
            metrics_data.append(f'queue_sent_total{{queue="{name}"}} {status["sent_count"]}')
            metrics_data.append(f'queue_processed_total{{queue="{name}"}} {status["processed_count"]}')
        
        return '\n'.join(metrics_data), 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return "# Error getting metrics\n", 500, {'Content-Type': 'text/plain'}

if __name__ == '__main__':
    logger.info("Starting Message Producer API")
    app.run(host='0.0.0.0', port=8001, debug=False)
