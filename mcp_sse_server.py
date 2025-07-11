#!/usr/bin/env python3
"""
完整的MCP SSE服务器实现
基于chrisboden/mcp_template的标准
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional
from aiohttp import web, web_request, web_response
import aiohttp_cors

# MCP相关导入
from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_sse_server")

# 创建服务器实例
server = Server("star_classifier_demo")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """返回可用工具列表"""
    return [
        types.Tool(
            name="get_star_info",
            description="获取恒星分类信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "star_name": {
                        "type": "string",
                        "description": "恒星名称或类型"
                    }
                },
                "required": ["star_name"]
            }
        ),
        types.Tool(
            name="classify_star", 
            description="根据温度和光度分类恒星",
            inputSchema={
                "type": "object",
                "properties": {
                    "temperature": {
                        "type": "number",
                        "description": "恒星表面温度(K)"
                    },
                    "luminosity": {
                        "type": "number",
                        "description": "恒星光度(太阳光度倍数)"
                    }
                },
                "required": ["temperature", "luminosity"]
            }
        ),
        types.Tool(
            name="get_mood",
            description="获取当前心情状态",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "询问心情的对象名称"
                    }
                },
                "required": []
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """处理工具调用"""
    if name == "get_star_info":
        star_name = arguments.get("star_name", "") if arguments else ""
        return await get_star_info(star_name)
    
    elif name == "classify_star":
        if not arguments:
            return [types.TextContent(type="text", text="错误：缺少温度和光度参数")]
        
        temperature = arguments.get("temperature")
        luminosity = arguments.get("luminosity")
        
        if temperature is None or luminosity is None:
            return [types.TextContent(type="text", text="错误：需要提供温度和光度参数")]
        
        return await classify_star(temperature, luminosity)
    
    elif name == "get_mood":
        name_param = arguments.get("name", "世界") if arguments else "世界"
        return await get_mood(name_param)
    
    else:
        raise ValueError(f"未知的工具: {name}")

async def get_star_info(star_name: str) -> list[types.TextContent]:
    """获取恒星信息"""
    star_database = {
        "太阳": {
            "类型": "G型主序星",
            "温度": "5778K", 
            "光度": "1倍太阳光度",
            "描述": "我们太阳系的中心恒星，是一颗典型的黄矮星"
        },
        "天狼星": {
            "类型": "A型主序星",
            "温度": "9940K",
            "光度": "25倍太阳光度", 
            "描述": "夜空中最亮的恒星，是一个双星系统"
        },
        "参宿四": {
            "类型": "M型超巨星",
            "温度": "3500K",
            "光度": "100000倍太阳光度",
            "描述": "猎户座的红超巨星，是已知最大的恒星之一"
        },
        "织女星": {
            "类型": "A型主序星",
            "温度": "9602K",
            "光度": "40倍太阳光度",
            "描述": "天琴座的最亮星，曾是北极星"
        }
    }
    
    if star_name in star_database:
        star = star_database[star_name]
        result = f"恒星: {star_name}\n"
        result += f"类型: {star['类型']}\n"
        result += f"温度: {star['温度']}\n"
        result += f"光度: {star['光度']}\n"
        result += f"描述: {star['描述']}"
    else:
        result = f"抱歉，数据库中没有找到关于 '{star_name}' 的信息。\n"
        result += "可用的恒星: 太阳, 天狼星, 参宿四, 织女星"
    
    return [types.TextContent(type="text", text=result)]

async def classify_star(temperature: float, luminosity: float) -> list[types.TextContent]:
    """根据温度和光度分类恒星"""
    # 基于温度的光谱分类
    if temperature >= 30000:
        spectral_class = "O型"
        color = "蓝色"
    elif temperature >= 10000:
        spectral_class = "B型"
        color = "蓝白色"
    elif temperature >= 7500:
        spectral_class = "A型"
        color = "白色"
    elif temperature >= 6000:
        spectral_class = "F型"
        color = "黄白色"
    elif temperature >= 5200:
        spectral_class = "G型"
        color = "黄色"
    elif temperature >= 3700:
        spectral_class = "K型"
        color = "橙色"
    else:
        spectral_class = "M型"
        color = "红色"
    
    # 基于光度的类型分类
    if luminosity >= 10000:
        luminosity_class = "超巨星"
    elif luminosity >= 1000:
        luminosity_class = "亮巨星"
    elif luminosity >= 100:
        luminosity_class = "巨星"
    elif luminosity >= 0.1:
        luminosity_class = "主序星"
    else:
        luminosity_class = "白矮星"
    
    result = f"恒星分类结果:\n"
    result += f"温度: {temperature}K\n"
    result += f"光度: {luminosity}倍太阳光度\n"
    result += f"光谱分类: {spectral_class}\n"
    result += f"颜色: {color}\n"
    result += f"类型: {luminosity_class}\n"
    
    # 添加一些有趣的比较
    if temperature > 5778:
        result += f"\n比太阳更热 ({temperature/5778:.1f}倍)"
    else:
        result += f"\n比太阳更冷 ({5778/temperature:.1f}倍)"
    
    if luminosity > 1:
        result += f"\n比太阳更亮 ({luminosity:.1f}倍)"
    else:
        result += f"\n比太阳更暗 ({1/luminosity:.1f}倍)"
    
    return [types.TextContent(type="text", text=result)]

async def get_mood(name: str) -> list[types.TextContent]:
    """获取心情"""
    import random
    
    moods = [
        f"{name}今天心情很好! 😊",
        f"{name}今天感觉有点累... 😴", 
        f"{name}今天充满活力! ⚡",
        f"{name}今天很平静 😌",
        f"{name}今天有点兴奋! 🎉",
        f"{name}今天在思考人生... 🤔"
    ]
    
    selected_mood = random.choice(moods)
    return [types.TextContent(type="text", text=selected_mood)]

# MCP 消息处理器
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
                    "name": "star_classifier_demo",
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

async def main():
    """启动MCP SSE服务器"""
    port = 8000
    host = "localhost"
    
    # 从命令行参数获取端口
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"无效的端口号: {sys.argv[1]}")
            sys.exit(1)
    
    print(f"🚀 启动 MCP SSE 服务器...")
    print(f"📍 SSE 地址: http://{host}:{port}/sse")
    print(f"📍 POST 地址: http://{host}:{port}/sse")
    print(f"📋 在 Cursor 中使用 http://{host}:{port}/sse 配置")
    print(f"🔧 工具数量: 3 (get_star_info, classify_star, get_mood)")
    print(f"⏹️  按 Ctrl+C 停止服务器")
    
    # 创建web应用
    app = web.Application()
    
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
    
    # 添加CORS支持到路由
    cors.add(sse_get_route)
    cors.add(sse_post_route)
    
    # 启动HTTP服务器
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    
    print(f"✅ MCP SSE服务器已启动在 {host}:{port}")
    print(f"🌐 SSE 连接: GET http://{host}:{port}/sse")
    print(f"📨 MCP 消息: POST http://{host}:{port}/sse")
    
    try:
        # 保持服务器运行
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 正在停止服务器...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 错误: {e}")
        sys.exit(1) 