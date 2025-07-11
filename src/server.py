#!/usr/bin/env python3
"""
MCP SSE 服务器基础框架模板
用于快速构建基于Server-Sent Events的MCP服务器
集成GitHub Star API功能
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
import logging
import os
from aiohttp import web, web_request, web_response
import aiohttp_cors

# MCP相关导入
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server

# GitHub API模块导入
from .github_star_api import GitHubStarAPI

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_sse_server")

# 创建服务器实例
server = Server("github_star_classifier")

def get_github_token() -> Optional[str]:
    """
    获取 GitHub Token
    优先级：starring_accessed_token 文件 > github_token.txt 文件 > 环境变量
    """
    # 首先尝试读取 starring_accessed_token 文件
    try:
        if os.path.exists("starring_accessed_token"):
            with open("starring_accessed_token", 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line and line.startswith('github_pat_'):
                        return line
    except Exception:
        pass
    
    # 然后尝试读取 github_token.txt 文件
    try:
        if os.path.exists("github_token.txt"):
            with open("github_token.txt", 'r', encoding='utf-8') as f:
                token = f.read().strip()
                if token and not token.startswith('#'):
                    return token
    except Exception:
        pass
    
    # 使用环境变量作为最后的备用
    return os.getenv("GITHUB_TOKEN")

# ================== MCP 工具定义区域 ==================

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """返回GitHub Star相关的工具列表"""
    return [
        types.Tool(
            name="get_user_starred_repos",
            description="获取用户的starred仓库列表。注意：如果遇到API限制错误，请务必传递token参数！",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "GitHub用户名"
                    },
                    "page": {
                        "type": "integer",
                        "description": "页码，默认为1"
                    },
                    "per_page": {
                        "type": "integer",
                        "description": "每页数量，默认30，最大100"
                    },
                    "sort": {
                        "type": "string",
                        "description": "排序方式：created或updated",
                        "enum": ["created", "updated"]
                    },
                    "token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token（强烈建议传递以避免API限制！如果不传递可能会遇到权限错误）"
                    }
                },
                "required": ["username"]
            }
        ),
        types.Tool(
            name="search_starred_repos",
            description="在用户的starred仓库中搜索。注意：如果遇到API限制错误，请务必传递token参数！",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "GitHub用户名"
                    },
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    },
                    "language": {
                        "type": "string",
                        "description": "编程语言过滤（可选）"
                    },
                    "token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token（强烈建议传递以避免API限制！如果不传递可能会遇到权限错误）"
                    }
                },
                "required": ["username", "query"]
            }
        ),
        types.Tool(
            name="get_repo_info",
            description="获取仓库的详细信息。注意：如果遇到API限制错误，请务必传递token参数！",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "仓库所有者"
                    },
                    "repo": {
                        "type": "string",
                        "description": "仓库名称"
                    },
                    "token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token（强烈建议传递以避免API限制！如果不传递可能会遇到权限错误）"
                    }
                },
                "required": ["owner", "repo"]
            }
        ),
        types.Tool(
            name="check_if_starred",
            description="检查当前用户是否已starred某个仓库。此操作必须提供token才能访问！",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "仓库所有者"
                    },
                    "repo": {
                        "type": "string",
                        "description": "仓库名称"
                    },
                    "token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token（必需！此操作需要认证）"
                    }
                },
                "required": ["owner", "repo", "token"]
            }
        ),
        types.Tool(
            name="star_repo",
            description="给仓库加star。此操作必须提供token才能执行！",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "仓库所有者"
                    },
                    "repo": {
                        "type": "string",
                        "description": "仓库名称"
                    },
                    "token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token（必需！此操作需要写入权限）"
                    }
                },
                "required": ["owner", "repo", "token"]
            }
        ),
        types.Tool(
            name="unstar_repo",
            description="取消仓库star。此操作必须提供token才能执行！",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "仓库所有者"
                    },
                    "repo": {
                        "type": "string",
                        "description": "仓库名称"
                    },
                    "token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token（必需！此操作需要写入权限）"
                    }
                },
                "required": ["owner", "repo", "token"]
            }
        ),
        types.Tool(
            name="get_starred_stats",
            description="获取用户starred仓库的统计信息。注意：如果遇到API限制错误，请务必传递token参数！",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {
                        "type": "string",
                        "description": "GitHub用户名"
                    },
                    "token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token（强烈建议传递以避免API限制！如果不传递可能会遇到权限错误）"
                    }
                },
                "required": ["username"]
            }
        ),
        types.Tool(
            name="get_repo_languages",
            description="获取仓库的编程语言分布。注意：如果遇到API限制错误，请务必传递token参数！",
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {
                        "type": "string",
                        "description": "仓库所有者"
                    },
                    "repo": {
                        "type": "string",
                        "description": "仓库名称"
                    },
                    "token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token（强烈建议传递以避免API限制！如果不传递可能会遇到权限错误）"
                    }
                },
                "required": ["owner", "repo"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """处理GitHub Star工具调用"""
    
    try:
        if name == "get_user_starred_repos":
            return await handle_get_user_starred_repos(arguments or {})
        elif name == "search_starred_repos":
            return await handle_search_starred_repos(arguments or {})
        elif name == "get_repo_info":
            return await handle_get_repo_info(arguments or {})
        elif name == "check_if_starred":
            return await handle_check_if_starred(arguments or {})
        elif name == "star_repo":
            return await handle_star_repo(arguments or {})
        elif name == "unstar_repo":
            return await handle_unstar_repo(arguments or {})
        elif name == "get_starred_stats":
            return await handle_get_starred_stats(arguments or {})
        elif name == "get_repo_languages":
            return await handle_get_repo_languages(arguments or {})

        else:
            raise ValueError(f"未知的工具: {name}")
    except Exception as e:
        logger.error(f"工具调用错误 {name}: {e}")
        return [types.TextContent(type="text", text=f"错误: {str(e)}")]

# ================== 工具实现区域 ==================

def create_github_api(token: Optional[str] = None) -> GitHubStarAPI:
    """创建 GitHubStarAPI 实例，支持动态传入 token"""
    if token:
        return GitHubStarAPI(token=token)
    else:
        # 如果没有传入token，使用原来的逻辑
        default_token = get_github_token()
        return GitHubStarAPI(token=default_token)

async def handle_get_user_starred_repos(arguments: dict) -> list[types.TextContent]:
    """处理获取用户starred仓库列表"""
    username = arguments.get("username")
    page = arguments.get("page", 1)
    per_page = arguments.get("per_page", 30)
    sort = arguments.get("sort", "created")
    token = arguments.get("token")
    
    if not username:
        return [types.TextContent(type="text", text="错误: 缺少必需参数 'username'")]
    
    github_api = create_github_api(token)
    result = await github_api.get_user_starred_repos(username, page, per_page, sort)
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def handle_search_starred_repos(arguments: dict) -> list[types.TextContent]:
    """处理搜索starred仓库"""
    username = arguments.get("username")
    query = arguments.get("query")
    language = arguments.get("language")
    token = arguments.get("token")
    
    if not username or not query:
        return [types.TextContent(type="text", text="错误: 缺少必需参数 'username' 或 'query'")]
    
    github_api = create_github_api(token)
    result = await github_api.search_starred_repos(username, query, language)
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def handle_get_repo_info(arguments: dict) -> list[types.TextContent]:
    """处理获取仓库信息"""
    owner = arguments.get("owner")
    repo = arguments.get("repo")
    token = arguments.get("token")
    
    if not owner or not repo:
        return [types.TextContent(type="text", text="错误: 缺少必需参数 'owner' 或 'repo'")]
    
    github_api = create_github_api(token)
    result = await github_api.get_repo_info(owner, repo)
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def handle_check_if_starred(arguments: dict) -> list[types.TextContent]:
    """处理检查是否已starred"""
    owner = arguments.get("owner")
    repo = arguments.get("repo")
    token = arguments.get("token")
    
    if not owner or not repo:
        return [types.TextContent(type="text", text="错误: 缺少必需参数 'owner' 或 'repo'")]
    
    github_api = create_github_api(token)
    result = await github_api.check_if_starred(owner, repo)
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def handle_star_repo(arguments: dict) -> list[types.TextContent]:
    """处理给仓库加star"""
    owner = arguments.get("owner")
    repo = arguments.get("repo")
    token = arguments.get("token")
    
    if not owner or not repo:
        return [types.TextContent(type="text", text="错误: 缺少必需参数 'owner' 或 'repo'")]
    
    github_api = create_github_api(token)
    result = await github_api.star_repo(owner, repo)
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def handle_unstar_repo(arguments: dict) -> list[types.TextContent]:
    """处理取消仓库star"""
    owner = arguments.get("owner")
    repo = arguments.get("repo")
    token = arguments.get("token")
    
    if not owner or not repo:
        return [types.TextContent(type="text", text="错误: 缺少必需参数 'owner' 或 'repo'")]
    
    github_api = create_github_api(token)
    result = await github_api.unstar_repo(owner, repo)
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def handle_get_starred_stats(arguments: dict) -> list[types.TextContent]:
    """处理获取starred统计信息"""
    username = arguments.get("username")
    token = arguments.get("token")
    
    if not username:
        return [types.TextContent(type="text", text="错误: 缺少必需参数 'username'")]
    
    github_api = create_github_api(token)
    result = await github_api.get_starred_stats(username)
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

async def handle_get_repo_languages(arguments: dict) -> list[types.TextContent]:
    """处理获取仓库语言分布"""
    owner = arguments.get("owner")
    repo = arguments.get("repo")
    token = arguments.get("token")
    
    if not owner or not repo:
        return [types.TextContent(type="text", text="错误: 缺少必需参数 'owner' 或 'repo'")]
    
    github_api = create_github_api(token)
    result = await github_api.get_repo_languages(owner, repo)
    return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]

# ================== MCP 消息处理器 ==================

class MCPHandler:
    def __init__(self):
        self.initialized = False
        self.client_capabilities = None

    async def handle_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理 MCP 消息"""
        try:
            method = message.get("method")
            params = message.get("params", {})
            msg_id = message.get("id")

            logger.info(f"处理 MCP 消息: {method}")

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
            logger.error(f"处理消息时出错: {e}")
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
                    "name": "github_star_classifier",
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
            logger.error(f"获取工具列表时出错: {e}")
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
                if hasattr(item, 'text'):
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
            logger.error(f"调用工具时出错: {e}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": f"Error calling tool: {str(e)}"
                }
            }

# 全局 MCP 处理器
mcp_handler = MCPHandler()

# ================== SSE 服务器区域 ==================

# 全局变量存储连接
connections = set()

async def handle_sse_connect(request: web_request.Request) -> web_response.Response:
    """处理SSE连接"""
    response = web_response.StreamResponse()
    response.headers['Content-Type'] = 'text/event-stream'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = '*'
    response.headers['Access-Control-Allow-Methods'] = '*'
    
    await response.prepare(request)
    
    try:
        # 发送连接确认
        await response.write(b'event: connected\ndata: {"type":"connected"}\n\n')
        
        # 保持连接活跃
        while True:
            await asyncio.sleep(30)  # 30秒心跳
            try:
                await response.write(b'event: ping\ndata: {"type":"ping"}\n\n')
            except:
                break
                
    except Exception as e:
        logger.error(f"SSE连接错误: {e}")
        
    return response

async def handle_post_message(request: web_request.Request) -> web_response.Response:
    """处理POST消息 - MCP协议消息"""
    try:
        data = await request.json()
        logger.info(f"收到MCP消息: {json.dumps(data, ensure_ascii=False)}")
        
        # 使用MCP处理器处理消息
        result = await mcp_handler.handle_message(data)
        
        if result is None:
            # 对于不需要响应的消息（如initialized）
            return web.Response(status=204)
        
        logger.info(f"发送MCP响应: {json.dumps(result, ensure_ascii=False)}")
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

async def broadcast_message(message: dict):
    """向所有连接广播消息"""
    if not connections:
        return
    
    data = f"data: {json.dumps(message)}\n\n".encode()
    disconnected = set()
    
    for connection in connections:
        try:
            await connection.write(data)
        except:
            disconnected.add(connection)
    
    # 清理断开的连接
    connections.difference_update(disconnected)

# ================== 服务器启动区域 ==================

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
    
    # 添加路由 - SSE 端点同时处理 GET 和 POST
    sse_get_route = app.router.add_get("/sse", handle_sse_connect)
    sse_post_route = app.router.add_post("/sse", handle_post_message)
    
    # 可选：添加健康检查端点
    health_route = app.router.add_get("/health", handle_health_check)
    
    # 添加CORS支持到路由
    cors.add(sse_get_route)
    cors.add(sse_post_route)
    cors.add(health_route)

async def handle_health_check(request: web_request.Request) -> web_response.Response:
    """健康检查端点"""
    return web.json_response({
        "status": "healthy",
        "server": "github_star_classifier",
        "version": "1.1.0"
    })

async def main():
    """启动MCP SSE服务器"""
    port = 38000
    host = "localhost"
    
    # 从命令行参数获取端口
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            logger.error(f"无效的端口号: {sys.argv[1]}")
            sys.exit(1)
    
    # 创建web应用
    app = web.Application()
    
    # 设置路由
    await setup_routes(app)
    
    # 启动HTTP服务器
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    logger.info(f"MCP SSE服务器已启动在 {host}:{port}")
    
    try:
        # 保持服务器运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("正在停止服务器...")
    finally:
        await runner.cleanup()

# ================== 程序入口 ==================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"启动错误: {e}")
        sys.exit(1)

