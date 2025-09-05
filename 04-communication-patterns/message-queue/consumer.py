import redis
import json
import time
import logging
from datetime import datetime
import signal
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - CONSUMER - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MessageConsumer:
    """消息消费者"""
    
    def __init__(self, redis_host='redis', redis_port=6379):
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        self.running = True
        self.processors = {
            'order_queue': self.process_order,
            'user_queue': self.process_user_registration,
            'email_queue': self.process_email,
            'notification_queue': self.process_notification
        }
        
        # 注册信号处理器以优雅关闭
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """处理关闭信号"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def consume_messages(self, queue_names, block_timeout=1):
        """从多个队列消费消息"""
        logger.info(f"Starting message consumer for queues: {queue_names}")
        
        while self.running:
            try:
                # 使用BLPOP从多个队列中阻塞式获取消息
                result = self.redis.blpop(queue_names, timeout=block_timeout)
                
                if result:
                    queue_name, message_json = result
                    self.process_message(queue_name, message_json)
                else:
                    # 超时，继续循环检查running状态
                    continue
                    
            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {e}")
                time.sleep(5)  # 等待重连
            except Exception as e:
                logger.error(f"Unexpected error in consumer loop: {e}")
                time.sleep(1)
        
        logger.info("Consumer shutting down")
    
    def process_message(self, queue_name, message_json):
        """处理单个消息"""
        try:
            message = json.loads(message_json)
            message_id = message.get('id', 'unknown')
            
            logger.info(f"Processing message {message_id} from queue {queue_name}")
            
            # 根据队列类型处理消息
            if queue_name in self.processors:
                success = self.processors[queue_name](message)
                
                if success:
                    # 增加处理计数
                    self.redis.incr(f"{queue_name}:processed_count")
                    logger.info(f"Successfully processed message {message_id}")
                else:
                    # 处理失败，重新入队或进入死信队列
                    self.handle_processing_failure(queue_name, message)
            else:
                logger.warning(f"No processor found for queue {queue_name}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def handle_processing_failure(self, queue_name, message):
        """处理消息处理失败的情况"""
        retry_count = message.get('retry_count', 0)
        max_retries = 3
        
        if retry_count < max_retries:
            # 增加重试计数并重新入队
            message['retry_count'] = retry_count + 1
            message['last_retry'] = datetime.now().isoformat()
            
            # 延迟重试（简单的指数退避）
            delay = 2 ** retry_count
            time.sleep(delay)
            
            self.redis.rpush(queue_name, json.dumps(message))
            logger.info(f"Message {message.get('id')} requeued for retry {retry_count + 1}")
        else:
            # 超过最大重试次数，放入死信队列
            dead_letter_queue = f"{queue_name}:dead_letter"
            message['failed_at'] = datetime.now().isoformat()
            message['failure_reason'] = 'max_retries_exceeded'
            
            self.redis.rpush(dead_letter_queue, json.dumps(message))
            logger.error(f"Message {message.get('id')} moved to dead letter queue after {max_retries} retries")
    
    def process_order(self, message):
        """处理订单消息"""
        try:
            order_data = message['data']
            order_id = order_data['order_id']
            
            logger.info(f"Processing order {order_id}")
            
            # 模拟订单处理步骤
            steps = [
                "Validating order data",
                "Checking inventory",
                "Processing payment",
                "Updating order status",
                "Sending confirmation"
            ]
            
            for step in steps:
                logger.info(f"Order {order_id}: {step}")
                time.sleep(0.5)  # 模拟处理时间
            
            # 模拟5%的失败率
            import random
            if random.random() < 0.05:
                raise Exception("Payment processing failed")
            
            logger.info(f"Order {order_id} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process order: {e}")
            return False
    
    def process_user_registration(self, message):
        """处理用户注册消息"""
        try:
            user_data = message['data']
            user_id = user_data['user_id']
            
            logger.info(f"Processing user registration {user_id}")
            
            # 模拟用户注册处理步骤
            steps = [
                "Validating user data",
                "Creating user account",
                "Setting up default preferences",
                "Creating user profile",
                "Initializing user data"
            ]
            
            for step in steps:
                logger.info(f"User {user_id}: {step}")
                time.sleep(0.3)  # 模拟处理时间
            
            logger.info(f"User {user_id} registration processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process user registration: {e}")
            return False
    
    def process_email(self, message):
        """处理邮件发送消息"""
        try:
            email_data = message['data']
            recipient = email_data['to']
            template = email_data.get('template', 'default')
            
            logger.info(f"Sending email to {recipient} using template {template}")
            
            # 模拟邮件发送处理
            time.sleep(1)  # 模拟邮件发送时间
            
            # 模拟2%的失败率
            import random
            if random.random() < 0.02:
                raise Exception("SMTP server unavailable")
            
            logger.info(f"Email sent successfully to {recipient}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False
    
    def process_notification(self, message):
        """处理通知消息"""
        try:
            notification_data = message['data']
            notification_type = notification_data.get('type', 'generic')
            
            logger.info(f"Processing {notification_type} notification")
            
            # 模拟通知处理（推送、短信等）
            time.sleep(0.5)
            
            logger.info(f"Notification {notification_type} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process notification: {e}")
            return False

def main():
    """主函数"""
    logger.info("Starting Message Consumer")
    
    # 创建消费者实例
    consumer = MessageConsumer()
    
    # 定义要消费的队列
    queues = ['order_queue', 'user_queue', 'email_queue', 'notification_queue']
    
    # 开始消费消息
    try:
        consumer.consume_messages(queues)
    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    except Exception as e:
        logger.error(f"Consumer error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
