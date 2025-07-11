# 🚀 最小MCP SSE服务器实现指南

## 📋 概述

MCP SSE Server from cursor.

## 🏗️ 核心架构

MCP SSE服务器的最小架构包含以下组件：

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI助手客户端   │◄──►│   MCP服务器     │◄──►│   实际服务/API   │
│                │    │                │    │                │
│ - 发送MCP消息   │    │ - 处理协议消息   │    │ - 执行具体功能   │
│ - 接收SSE事件   │    │ - 管理工具列表   │    │ - 返回结果数据   │
│ - 调用工具      │    │ - SSE推送      │    │                │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 最小依赖

```txt
aiohttp>=3.8.0
aiohttp-cors>=0.7.0
mcp>=1.0.0
```

## 🔧 实现步骤

### 1. 基础服务器框架

```python
#!/usr/bin/env python3
"""
最小MCP SSE服务器实现
"""

import asyncio
import json
import logging
from typing import Any, Dict, List
from aiohttp import web
import aiohttp_cors
import mcp.types as types
from mcp.server import Server

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("minimal_mcp_server")

# 创建MCP服务器实例
server = Server("minimal_mcp_server")
```

### 2. 定义工具

```python
@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """定义服务器提供的工具列表"""
    return [
        types.Tool(
            name="echo",
            description="回显工具 - 将输入的文本原样返回",
            inputSchema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "要回显的文本"
                    }
                },
                "required": ["text"]
            }
        ),
        types.Tool(
            name="get_time",
            description="获取当前服务器时间",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]
```

### 3. 实现工具处理函数

```python
@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent]:
    """处理工具调用"""
    if name == "echo":
        text = arguments.get("text", "") if arguments else ""
        return [types.TextContent(type="text", text=f"回显: {text}")]
    
    elif name == "get_time":
        import datetime
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [types.TextContent(type="text", text=f"当前时间: {current_time}")]
    
    else:
        raise ValueError(f"未知工具: {name}")
```

### 4. MCP消息处理器

```python
class MCPHandler:
    """MCP协议消息处理器"""
    
    def __init__(self):
        self.initialized = False
        self.client_capabilities = None

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any] | None:
        """处理MCP消息"""
        try:
            method = message.get("method")
            params = message.get("params", {})
            msg_id = message.get("id")

            if method == "initialize":
                return await self._handle_initialize(msg_id, params)
            elif method == "initialized":
                self.initialized = True
                return None  # 不需要响应
            elif method == "tools/list":
                return await self._handle_tools_list(msg_id)
            elif method == "tools/call":
                return await self._handle_tools_call(msg_id, params)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
        except Exception as e:
            logger.error(f"处理消息错误: {e}")
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }

    async def _handle_initialize(self, msg_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        self.client_capabilities = params.get("capabilities", {})
        
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "logging": {}
                },
                "serverInfo": {
                    "name": "minimal_mcp_server",
                    "version": "1.0.0"
                }
            }
        }

    async def _handle_tools_list(self, msg_id: int) -> Dict[str, Any]:
        """处理工具列表请求"""
        try:
            tools = await handle_list_tools()
            tools_dict = []
            
            for tool in tools:
                tools_dict.append({
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                })
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "tools": tools_dict
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": f"Error listing tools: {str(e)}"
                }
            }

    async def _handle_tools_call(self, msg_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用请求"""
        try:
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            result = await handle_call_tool(name, arguments)
            
            content = []
            for item in result:
                content.append({
                    "type": "text",
                    "text": item.text
                })
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": content
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": f"Error calling tool: {str(e)}"
                }
            }

# 创建全局处理器实例
mcp_handler = MCPHandler()
```

### 5. SSE服务器实现

```python
async def handle_sse_connect(request: web.Request) -> web.StreamResponse:
    """处理SSE连接"""
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    
    await response.prepare(request)
    
    try:
        # 发送连接确认
        await response.write(b'event: connected\ndata: {"type":"connected"}\n\n')
        
        # 保持连接活跃
        while True:
            await asyncio.sleep(30)  # 30秒心跳
            await response.write(b'event: ping\ndata: {"type":"ping"}\n\n')
    except Exception as e:
        logger.error(f"SSE连接错误: {e}")
    
    return response

async def handle_post_message(request: web.Request) -> web.Response:
    """处理POST消息 - MCP协议消息"""
    try:
        data = await request.json()
        logger.info(f"收到MCP消息: {data}")
        
        # 使用MCP处理器处理消息
        result = await mcp_handler.handle_message(data)
        
        if result is None:
            return web.Response(status=204)
        
        logger.info(f"发送MCP响应: {result}")
        return web.json_response(result)
        
    except Exception as e:
        logger.error(f"处理POST消息错误: {e}")
        return web.json_response({
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": f"Parse error: {str(e)}"
            }
        }, status=400)
```

### 6. 服务器启动

```python
async def setup_routes(app: web.Application):
    """设置路由"""
    # 添加CORS支持
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # 添加路由
    sse_get_route = app.router.add_get("/sse", handle_sse_connect)
    sse_post_route = app.router.add_post("/sse", handle_post_message)
    health_route = app.router.add_get("/health", handle_health_check)
    
    # 添加CORS支持
    cors.add(sse_get_route)
    cors.add(sse_post_route)
    cors.add(health_route)

async def handle_health_check(request: web.Request) -> web.Response:
    """健康检查端点"""
    return web.json_response({
        "status": "healthy",
        "server": "minimal_mcp_server",
        "version": "1.0.0"
    })

async def main():
    """启动服务器"""
    port = 8000
    host = "localhost"
    
    app = web.Application()
    await setup_routes(app)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info(f"最小MCP SSE服务器已启动: http://{host}:{port}")
    
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("服务器停止")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
```

## 📁 完整文件结构

```
minimal_mcp_server/
├── minimal_server.py      # 上述完整代码
├── requirements.txt       # 依赖列表
└── README.md             # 使用说明
```

## 🚀 启动和测试

### 1. 安装依赖
```bash
pip install aiohttp aiohttp-cors mcp
```

### 2. 启动服务器
```bash
python minimal_server.py
```

### 3. 测试连接
```bash
# 健康检查
curl http://localhost:8000/health

# SSE连接测试
curl -N http://localhost:8000/sse

# MCP消息测试
curl -X POST http://localhost:8000/sse \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "1.0.0"}
    }
  }'
```

## 🎛️ 客户端配置

### Cursor IDE配置

要在Cursor IDE中使用这个MCP服务器，需要配置MCP设置。两个方案：
1. 创建或修改 `~/.cursor-server/mcp_servers.json`；
2. 项目目录下创建或修改`.cursor/mcp.json`

```json
{
  "mcpServers": {
    "star-classifier": {
      "command": "python",
      "args": [
        "/path/to/your/star_classifier/start_github_star_server.py"
      ],
      "env": {
        "GITHUB_TOKEN": "your_github_token_here"
      }
    }
  }
}
```

完成配置后可在 cursor settings - Tools & Integrations 中 enable 并检查服务连接状态。



### 配置注意事项

1. **路径要求**: 
   - 使用绝对路径，避免相对路径问题
   - Windows用户注意使用正确的路径分隔符

2. **环境变量**:

   - `PORT`: 可选，默认8080
   - `HOST`: 可选，默认localhost


### 配置验证

启动后可以通过以下方式验证配置：

1. **检查服务器日志**:
```bash
# 查看服务器启动日志
tail -f /tmp/mcp_server.log
```

2. **测试连接**:
```bash
# 健康检查
curl http://localhost:8080/health
```

3. **在客户端中测试**:


## 🔧 扩展指南

### 添加新工具

1. **在handle_list_tools中添加工具定义**：
```python
types.Tool(
    name="my_new_tool",
    description="我的新工具",
    inputSchema={
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "参数1"},
            "param2": {"type": "integer", "description": "参数2"}
        },
        "required": ["param1"]
    }
)
```

2. **在handle_call_tool中添加处理逻辑**：
```python
elif name == "my_new_tool":
    param1 = arguments.get("param1", "")
    param2 = arguments.get("param2", 0)
    
    # 执行具体逻辑
    result = f"处理结果: {param1}, {param2}"
    
    return [types.TextContent(type="text", text=result)]
```

### 添加外部API集成

```python
import aiohttp

async def call_external_api(url: str, params: dict) -> dict:
    """调用外部API的通用函数"""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            return await response.json()

# 在工具处理中使用
elif name == "external_api_tool":
    result = await call_external_api("https://api.example.com/data", arguments)
    return [types.TextContent(type="text", text=json.dumps(result))]
```

## 📚 核心概念

### MCP协议消息格式
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {"key": "value"}
  }
}
```

### SSE事件格式
```
event: event_name
data: {"type": "event_type", "content": "data"}

```

### 工具定义结构
- `name`: 工具唯一标识符
- `description`: 工具功能描述
- `inputSchema`: JSON Schema定义输入参数

