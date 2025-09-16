# VisioFirm 训练模块 API 文档

## 概述

本文档描述了 VisioFirm 训练模块提供的 REST API 接口，包括训练任务管理、系统资源监控、性能优化等功能。

## 基础信息

- **基础URL**: `/training`
- **认证方式**: Flask-Login 会话认证
- **数据格式**: JSON
- **编码**: UTF-8

## API 接口列表

### 1. 训练管理接口

#### 1.1 获取训练仪表板页面
```http
GET /training/<project_name>
```

**描述**: 渲染训练仪表板页面，显示训练任务列表、配置和系统状态。

**参数**:
- `project_name` (string): 项目名称

**响应**: HTML 页面

---

#### 1.2 创建训练任务
```http
POST /training/create_task
```

**描述**: 创建新的训练任务。

**请求体**:
```json
{
    "project_name": "string",
    "task_name": "string", 
    "model_type": "string",
    "train_ratio": 0.7,
    "val_ratio": 0.2,
    "test_ratio": 0.1,
    "epochs": 100,
    "batch_size": 16,
    "learning_rate": 0.01,
    "image_size": 640,
    "device": "auto",
    "optimizer": "auto"
}
```

**响应**:
```json
{
    "success": true,
    "task_id": 123
}
```

---

#### 1.3 启动训练任务
```http
POST /training/start_task
```

**描述**: 启动指定的训练任务。

**请求体**:
```json
{
    "project_name": "string",
    "task_id": 123
}
```

**响应**:
```json
{
    "success": true,
    "message": "训练任务已启动"
}
```

---

#### 1.4 停止训练任务
```http
POST /training/stop_task
```

**描述**: 停止正在运行的训练任务。

**请求体**:
```json
{
    "project_name": "string", 
    "task_id": 123
}
```

**响应**:
```json
{
    "success": true,
    "message": "训练任务已停止"
}
```

---

#### 1.5 获取任务状态
```http
GET /training/task_status/<project_name>/<task_id>
```

**描述**: 获取指定训练任务的详细状态和进度信息。

**参数**:
- `project_name` (string): 项目名称
- `task_id` (integer): 任务ID

**响应**:
```json
{
    "success": true,
    "task": {
        "id": 123,
        "task_name": "string",
        "model_type": "yolov8s",
        "status": "running",
        "progress": 75,
        "created_at": "2024-09-15T10:00:00",
        "started_at": "2024-09-15T10:05:00",
        "error_message": null,
        "model_path": "/path/to/model.pt",
        "metrics": {
            "mAP50": 0.856,
            "precision": 0.891,
            "recall": 0.823
        },
        "logs": [
            {
                "epoch": 75,
                "loss": 0.245,
                "timestamp": "2024-09-15T10:30:00"
            }
        ]
    }
}
```

---

#### 1.6 获取任务列表
```http
GET /training/tasks/<project_name>
```

**描述**: 获取项目的所有训练任务列表。

**响应**:
```json
{
    "success": true,
    "tasks": [
        {
            "id": 123,
            "task_name": "string",
            "model_type": "yolov8s",
            "status": "completed",
            "progress": 100,
            "created_at": "2024-09-15T10:00:00"
        }
    ]
}
```

---

#### 1.7 删除训练任务
```http
POST /training/delete_task
```

**描述**: 删除指定的训练任务（不能删除正在运行的任务）。

**请求体**:
```json
{
    "project_name": "string",
    "task_id": 123
}
```

**响应**:
```json
{
    "success": true,
    "message": "训练任务已删除"
}
```

---

### 2. 配置管理接口

#### 2.1 保存训练配置
```http
POST /training/save_config
```

**描述**: 保存训练配置模板供以后使用。

**请求体**:
```json
{
    "project_name": "string",
    "config_name": "string",
    "model_type": "yolov8s",
    "epochs": 100,
    "batch_size": 16,
    "learning_rate": 0.01,
    "image_size": 640,
    "device": "auto",
    "optimizer": "auto",
    "augmentation": {},
    "other_params": {}
}
```

**响应**:
```json
{
    "success": true,
    "config_id": 456
}
```

---

#### 2.2 获取配置列表
```http
GET /training/configs/<project_name>
```

**描述**: 获取项目的所有保存的训练配置。

**响应**:
```json
{
    "success": true,
    "configs": [
        {
            "id": 456,
            "config_name": "高精度配置",
            "model_type": "yolov8l",
            "epochs": 200,
            "batch_size": 8,
            "learning_rate": 0.005,
            "created_at": "2024-09-15T09:00:00"
        }
    ]
}
```

---

### 3. 模型导出接口

#### 3.1 导出模型
```http
POST /training/export_model/<project_name>/<task_id>
```

**描述**: 将训练好的模型导出为指定格式。

**请求体**:
```json
{
    "format": "onnx",
    "half": false,
    "int8": false,
    "dynamic": false,
    "simplify": true,
    "opset": 12,
    "batch": 1
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "export_path": "/path/to/exported/model.onnx",
        "format": "onnx",
        "file_size_mb": 25.6,
        "description": "ONNX - 跨平台推理格式"
    }
}
```

---

#### 3.2 验证模型
```http
POST /training/validate_model/<project_name>/<task_id>
```

**描述**: 使用测试数据集验证训练好的模型性能。

**请求体**:
```json
{
    "imgsz": 640,
    "batch": 16,
    "conf": 0.001,
    "iou": 0.6,
    "device": "auto",
    "save_json": true,
    "plots": true
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "metrics": {
            "mAP50": 0.856,
            "mAP50-95": 0.647,
            "precision": 0.891,
            "recall": 0.823,
            "f1_score": 0.856,
            "class_metrics": {
                "car": {"AP50": 0.92},
                "person": {"AP50": 0.79}
            }
        },
        "results_path": "/path/to/validation/results"
    }
}
```

---

### 4. 系统资源监控接口

#### 4.1 获取系统资源状态
```http
GET /training/system_resources/<project_name>
```

**描述**: 获取实时的系统资源使用情况。

**响应**:
```json
{
    "success": true,
    "data": {
        "cpu_percent": 45.2,
        "memory_percent": 67.8,
        "memory_available_gb": 8.4,
        "gpu_info": [
            {
                "device": "cuda:0",
                "name": "NVIDIA GeForce RTX 3080",
                "memory_used_gb": 4.2,
                "memory_total_gb": 10.0,
                "memory_percent": 42.0
            }
        ],
        "active_tasks": 1,
        "max_concurrent_tasks": 2
    }
}
```

---

### 5. 性能优化接口

#### 5.1 获取性能优化建议
```http
POST /training/performance_suggestions/<project_name>
```

**描述**: 基于当前系统状态和配置获取性能优化建议。

**请求体**:
```json
{
    "model_type": "yolov8s",
    "config": {
        "batch_size": 16,
        "epochs": 100,
        "device": "auto"
    }
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "suggestions": [
            {
                "type": "memory",
                "issue": "内存使用率过高",
                "suggestion": "建议减少批量大小或关闭图像缓存",
                "config_changes": {
                    "batch_size": 8,
                    "cache": false
                }
            }
        ],
        "resource_usage": {
            "cpu_percent": 45.2,
            "memory_percent": 87.3
        }
    }
}
```

---

#### 5.2 获取最优配置
```http
POST /training/optimal_config/<project_name>
```

**描述**: 获取针对当前硬件环境优化的训练配置。

**请求体**:
```json
{
    "model_type": "yolov8s",
    "epochs": 100,
    "device": "auto"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "epochs": 100,
        "batch": 12,
        "lr0": 0.01,
        "device": "auto",
        "amp": true,
        "cache": false,
        "workers": 4,
        "save_period": 20,
        "patience": 30,
        "optimizer": "AdamW"
    }
}
```

---

### 6. 辅助接口

#### 6.1 获取可用模型
```http
GET /training/available_models
```

**描述**: 获取所有支持的YOLO模型列表。

**响应**:
```json
{
    "success": true,
    "models": [
        {
            "name": "yolov8n",
            "description": "YOLOv8 Nano - 最快，精度较低"
        },
        {
            "name": "yolov8s", 
            "description": "YOLOv8 Small - 平衡速度和精度"
        }
    ],
    "devices": [
        {
            "name": "auto",
            "description": "自动选择最佳设备"
        },
        {
            "name": "cuda:0",
            "description": "GPU 0: NVIDIA GeForce RTX 3080"
        }
    ]
}
```

---

#### 6.2 获取导出格式
```http
GET /training/export_formats
```

**描述**: 获取所有支持的模型导出格式。

**响应**:
```json
{
    "success": true,
    "formats": {
        "onnx": {
            "name": "ONNX",
            "description": "跨平台推理格式，广泛支持",
            "extension": ".onnx",
            "recommended": true
        },
        "torchscript": {
            "name": "TorchScript",
            "description": "PyTorch优化格式，高性能",
            "extension": ".torchscript",
            "recommended": false
        }
    }
}
```

---

## 错误处理

### 通用错误格式
```json
{
    "success": false,
    "error": "错误描述信息"
}
```

### 常见HTTP状态码

| 状态码 | 含义 | 示例场景 |
|--------|------|----------|
| 200 | 成功 | 请求处理成功 |
| 400 | 请求错误 | 参数缺失或格式错误 |
| 401 | 未授权 | 用户未登录 |
| 404 | 资源不存在 | 项目或任务不存在 |
| 409 | 资源冲突 | 任务已在运行 |
| 500 | 服务器错误 | 内部处理错误 |

### 错误处理最佳实践

1. **检查响应状态**: 始终检查 `success` 字段
2. **错误重试**: 对于临时性错误，实现重试机制
3. **用户友好**: 将技术错误转换为用户可理解的信息
4. **日志记录**: 记录错误信息用于调试

## 使用示例

### JavaScript 客户端示例

```javascript
// 创建训练任务
async function createTrainingTask() {
    try {
        const response = await fetch('/training/create_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                project_name: 'my_project',
                task_name: '第一个训练任务',
                model_type: 'yolov8s',
                epochs: 100,
                batch_size: 16,
                learning_rate: 0.01
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            console.log('任务创建成功，ID:', result.task_id);
            return result.task_id;
        } else {
            console.error('创建失败:', result.error);
        }
    } catch (error) {
        console.error('请求错误:', error);
    }
}

// 监控训练进度
async function monitorTrainingProgress(projectName, taskId) {
    try {
        const response = await fetch(`/training/task_status/${projectName}/${taskId}`);
        const result = await response.json();
        
        if (result.success) {
            const task = result.task;
            console.log(`进度: ${task.progress}%, 状态: ${task.status}`);
            
            if (task.status === 'running') {
                // 继续监控
                setTimeout(() => {
                    monitorTrainingProgress(projectName, taskId);
                }, 5000);
            }
        }
    } catch (error) {
        console.error('获取进度失败:', error);
    }
}

// 获取性能建议
async function getPerformanceSuggestions(projectName) {
    try {
        const response = await fetch(`/training/performance_suggestions/${projectName}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model_type: 'yolov8s',
                config: {
                    batch_size: 16,
                    epochs: 100
                }
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            result.data.suggestions.forEach(suggestion => {
                console.log('建议:', suggestion.suggestion);
            });
        }
    } catch (error) {
        console.error('获取建议失败:', error);
    }
}
```

---

## 更新历史

- **v1.0.0** (2024-09-15): 初始版本，包含基础训练功能
- **v1.1.0** (2024-09-15): 新增性能监控和优化接口
- **v1.2.0** (2024-09-15): 新增模型导出和验证功能

---

*注意: 本API文档基于VisioFirm训练模块设计文档编写，实际使用时请以最新代码为准。*