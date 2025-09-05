import time
import os
import json
import logging
import requests
from datetime import datetime
from collections import defaultdict, deque
import threading

class SidecarMonitor:
    """边车监控服务"""
    
    def __init__(self):
        self.setup_logging()
        self.metrics = defaultdict(int)
        self.response_times = deque(maxlen=100)  # 保留最近100次请求的响应时间
        self.main_app_url = "http://main-app:5000"
        self.log_file_path = "/var/log/app/app.log"
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - SIDECAR - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def collect_logs(self):
        """收集主应用的日志"""
        self.logger.info("Starting log collection service")
        
        if not os.path.exists(self.log_file_path):
            self.logger.warning(f"Log file {self.log_file_path} not found")
            return
            
        # 监控日志文件变化
        with open(self.log_file_path, 'r') as f:
            # 移动到文件末尾
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    self.process_log_line(line.strip())
                else:
                    time.sleep(1)  # 等待新的日志
                    
    def process_log_line(self, line):
        """处理单行日志"""
        try:
            # 解析日志并提取指标
            if "ERROR" in line:
                self.metrics["error_count"] += 1
                self.logger.warning(f"Error detected in main app: {line}")
            elif "WARNING" in line:
                self.metrics["warning_count"] += 1
            elif "INFO" in line:
                self.metrics["info_count"] += 1
                
            # 检测特定的业务指标
            if "Users list requested" in line:
                self.metrics["users_list_requests"] += 1
            elif "User" in line and "requested" in line:
                self.metrics["user_detail_requests"] += 1
            elif "New user created" in line:
                self.metrics["user_created"] += 1
                
            self.metrics["total_log_lines"] += 1
            
        except Exception as e:
            self.logger.error(f"Error processing log line: {e}")
            
    def health_monitor(self):
        """监控主应用健康状态"""
        self.logger.info("Starting health monitoring service")
        
        while True:
            try:
                start_time = time.time()
                response = requests.get(f"{self.main_app_url}/health", timeout=5)
                response_time = time.time() - start_time
                
                self.response_times.append(response_time)
                
                if response.status_code == 200:
                    self.metrics["health_check_success"] += 1
                    self.logger.debug(f"Health check passed in {response_time:.3f}s")
                else:
                    self.metrics["health_check_failure"] += 1
                    self.logger.warning(f"Health check failed with status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.metrics["health_check_failure"] += 1
                self.logger.error(f"Health check failed: {e}")
                
            time.sleep(30)  # 每30秒检查一次
            
    def get_metrics(self):
        """获取收集的指标"""
        avg_response_time = sum(self.response_times) / len(self.response_times) if self.response_times else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime": time.time() - self.start_time,
            "metrics": dict(self.metrics),
            "average_response_time": avg_response_time,
            "latest_response_times": list(self.response_times)[-10:],  # 最近10次响应时间
            "total_requests_monitored": len(self.response_times)
        }
        
    def start_monitoring(self):
        """启动所有监控服务"""
        self.start_time = time.time()
        self.logger.info("Sidecar monitoring services starting...")
        
        # 启动日志收集线程
        log_thread = threading.Thread(target=self.collect_logs, daemon=True)
        log_thread.start()
        
        # 启动健康监控线程
        health_thread = threading.Thread(target=self.health_monitor, daemon=True)
        health_thread.start()
        
        self.logger.info("All monitoring services started")
        
        return log_thread, health_thread

def main():
    """主函数"""
    monitor = SidecarMonitor()
    
    # 启动监控服务
    log_thread, health_thread = monitor.start_monitoring()
    
    # 简单的HTTP服务器暴露指标
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class MetricsHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/metrics':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                metrics = monitor.get_metrics()
                self.wfile.write(json.dumps(metrics, indent=2).encode())
            elif self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                health_data = {
                    "status": "healthy",
                    "service": "sidecar-monitor",
                    "timestamp": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(health_data, indent=2).encode())
            else:
                self.send_response(404)
                self.end_headers()
                
        def log_message(self, format, *args):
            # 禁用默认的访问日志
            pass
    
    # 启动指标服务器
    server = HTTPServer(('0.0.0.0', 8080), MetricsHandler)
    monitor.logger.info("Metrics server starting on port 8080")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        monitor.logger.info("Shutting down sidecar monitor")
        server.shutdown()

if __name__ == "__main__":
    main()
