#!/usr/bin/env python3
"""
GitHub Star Classifier 服务器启动脚本
提供便捷的服务器启动和配置选项
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path



def main():
    parser = argparse.ArgumentParser(
        description="GitHub Star Classifier MCP Server v1.2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
GitHub Token 配置:
  - 在项目目录创建 github_token.txt 文件
  - 或设置环境变量 GITHUB_TOKEN
  - 服务器会自动读取 token（无需重启）

示例:
  %(prog)s                           # 使用默认设置启动
  %(prog)s --port 8080               # 指定端口启动
  %(prog)s --debug                   # 启用调试模式
"""
    )
    parser.add_argument("--port", "-p", type=int, default=38000, help="服务器端口 (默认: 38000)")
    parser.add_argument("--host", default="localhost", help="服务器主机 (默认: localhost)")
    parser.add_argument("--debug", "-d", action="store_true", help="启用调试模式")
    parser.add_argument("--version", "-v", action="version", version="GitHub Star Classifier MCP Server v1.2.0")
    
    args = parser.parse_args()
    
    # 设置工作目录
    script_dir = Path(__file__).parent
    src_dir = script_dir / "src"
    
    if not src_dir.exists():
        print("❌ 错误: 未找到 src 目录")
        sys.exit(1)
    
    # 设置环境变量
    env = os.environ.copy()
    
    if args.debug:
        env["MCP_LOG_LEVEL"] = "DEBUG"
        print("🔍 启用调试模式")
    
    # 检查依赖
    try:
        import aiohttp
        import aiohttp_cors
        import mcp
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        sys.exit(1)
    
    # 启动服务器
    cmd = [
        sys.executable,
        str(src_dir / "server.py"),
        str(args.port),
        args.host
    ]
    
    print("=" * 60)
    print(f"🚀 GitHub Star Classifier MCP Server v1.2.0")
    print(f"📍 服务地址: http://{args.host}:{args.port}")
    print(f"📋 Cursor 配置: http://{args.host}:{args.port}/sse")
    print(f"🔧 工具数量: 16 个 GitHub 管理工具")
    print(f"   ├─ 基础功能: 8个 (查询、统计、star/unstar)")
    print(f"   └─ 分类管理: 8个 (Lists创建、更新、批量操作)")
    print(f"💡 Token 配置: 在项目目录放置 github_token.txt")
    print(f"⚡ 新功能: 支持完整的GitHub Lists分类管理")
    print(f"⏹️  按 Ctrl+C 停止服务器")
    print("=" * 60)
    
    try:
        # 切换到src目录并启动服务器
        os.chdir(src_dir)
        subprocess.run(cmd, env=env)
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 