# 分布式系统设计模式 Demo 项目

基于《Designing Distributed Systems》的实践项目，包含常见分布式系统设计模式的实现和演示。

## 项目结构

```
.
├── 01-single-node-patterns/      # 单节点模式
│   ├── sidecar/                  # 边车模式
│   ├── ambassador/               # 大使模式
│   └── adapter/                  # 适配器模式
├── 02-serving-patterns/          # 服务模式
│   ├── replicated-service/       # 副本服务
│   ├── sharded-service/          # 分片服务
│   └── load-balancer/            # 负载均衡
├── 03-batch-patterns/            # 批处理模式
│   ├── work-queue/               # 工作队列
│   ├── event-driven/             # 事件驱动
│   └── coordinated-batch/        # 协调批处理
├── 04-communication-patterns/    # 通信模式
│   ├── request-response/         # 请求-响应
│   ├── pub-sub/                  # 发布-订阅
│   └── message-queue/            # 消息队列
├── docker/                       # Docker 配置
├── k8s/                         # Kubernetes 配置
├── monitoring/                   # 监控配置
└── blog/                        # 技术博客文章
```

## 技术栈

- **容器化**: Docker & Kubernetes
- **编程语言**: Python, Go, JavaScript/Node.js
- **消息队列**: Redis, RabbitMQ
- **数据库**: MongoDB, PostgreSQL
- **监控**: Prometheus, Grafana
- **负载均衡**: Nginx, HAProxy

## 快速开始

### 环境准备
```bash
# 安装 Docker
brew install docker

# 安装 Kubernetes (minikube)
brew install minikube

# 启动本地集群
minikube start
```

### 运行示例
```bash
# 构建所有服务
make build

# 启动完整演示环境
make deploy

# 查看服务状态
make status
```

## 设计模式说明

### 单节点模式 (Single-Node Patterns)
- **边车模式 (Sidecar)**: 将辅助功能作为独立容器与主应用一起部署
- **大使模式 (Ambassador)**: 代理外部服务调用，提供统一接口
- **适配器模式 (Adapter)**: 标准化应用的监控和日志输出

### 服务模式 (Serving Patterns)
- **副本服务 (Replicated Service)**: 通过多副本提供高可用性
- **分片服务 (Sharded Service)**: 数据分片提高系统处理能力
- **负载均衡 (Load Balancer)**: 流量分发和故障转移

### 批处理模式 (Batch Patterns)
- **工作队列 (Work Queue)**: 异步任务处理
- **事件驱动 (Event-Driven)**: 基于事件的处理流程
- **协调批处理 (Coordinated Batch)**: 多阶段批处理协调

## 监控和可观察性

项目集成了完整的监控堆栈：
- Prometheus 收集指标
- Grafana 可视化监控
- Jaeger 分布式追踪
- ELK Stack 日志聚合

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
