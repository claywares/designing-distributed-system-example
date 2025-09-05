# 消息队列模式演示

## 概述

消息队列是分布式系统中实现异步通信的重要模式。它允许应用程序通过消息进行通信，而不需要直接连接或等待响应。

## 架构图

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Producer   │───▶│   Message   │◀───│  Consumer   │
│             │    │    Queue    │    │             │
│ - 订单服务   │    │   (Redis)   │    │ - 支付服务   │
│ - 用户注册   │    │             │    │ - 邮件服务   │
│ - 日志记录   │    │             │    │ - 数据处理   │
└─────────────┘    └─────────────┘    └─────────────┘
```

## 消息队列的优势

1. **解耦**: 生产者和消费者之间松耦合
2. **异步处理**: 提高系统响应速度
3. **削峰填谷**: 平滑流量波动
4. **可靠性**: 消息持久化，防止丢失
5. **扩展性**: 可以动态增加消费者

## 使用场景

- **订单处理**: 订单创建 → 库存检查 → 支付处理 → 发货通知
- **用户注册**: 用户注册 → 发送欢迎邮件 → 创建默认配置
- **日志处理**: 应用日志 → 日志收集 → 分析处理
- **图片处理**: 图片上传 → 压缩处理 → 生成缩略图

## 本示例演示

- **生产者**: Web API接收请求并发送消息到队列
- **消费者**: 后台服务处理队列中的消息
- **监控**: 队列状态和处理指标监控

## 运行方式

```bash
# 启动所有服务
docker-compose up --build

# 发送消息
curl -X POST http://localhost:8001/api/orders \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123, "product": "laptop", "amount": 999.99}'

# 发送用户注册消息
curl -X POST http://localhost:8001/api/users \
  -H "Content-Type: application/json" \
  -d '{"username": "john", "email": "john@example.com"}'

# 查看队列状态
curl http://localhost:8001/api/queue/status

# 查看Redis队列
docker exec -it redis redis-cli LLEN order_queue
```
