因Github API尚未支持star list相关操作，本项目写一半夭折了，

### 最初设计

本项目最初的目标是通过调用Github API并将其作为MCP工具提供，实现让LLM助手自动化分类和管理用户的Github star，从而解决star仓库分类混乱。我优先使用cursor实现了完整的MCP server框架，并成功集成了Github API的基础功能，初步证明了项目的技术可行性。然而在进一步开发过程中发现，Github API目前并未提供star list(starred repositories lists)的管理能力，这是一个始料未及的限制。因此，本项目转型为一个功能完备的MCP server参考模板。

Github相关问题详见：
- https://docs.github.com/en/rest/activity/starring?apiVersion=2022-11-28
- https://github.com/orgs/community/discussions/8293

MCP模板参考：
- https://github.com/chrisboden/mcp_template
- https://docs.cursor.com/context/mcp


### 🏗️ 项目架构

```
star_classifier/
├── src/
│   ├── server.py           # MCP SSE 服务器核心实现
│   ├── github_star_api.py  # GitHub API 封装（真实可用的API）
│   └── config.yaml         # 配置文件
├── mcp_sse_server.py       # SSE 服务器启动脚本  
├── start_github_star_server.py  # 快速启动脚本
├── requirements.txt        # 依赖列表
├── 最小MCP_SSE实现指南.md   # 最小实现教程
└── README.md              # 项目说明
```

### ✅ 实际可用的功能

经过清理，本项目现在只包含真实存在的GitHub API功能：

- 📊 **基础数据获取**: starred仓库列表、统计信息、仓库详情
- 🔍 **搜索功能**: 在starred仓库中搜索特定内容
- ⭐ **Star管理**: 给仓库加star、取消star、检查star状态
- 📈 **数据分析**: 编程语言分布、项目统计等
- 🌟 **恒星分类**: 额外的天文恒星分类功能（彩蛋）

### 🚫 已移除的功能

以下功能因GitHub API不支持而已被移除：
- ❌ 创建/管理starred lists
- ❌ 将仓库添加到lists
- ❌ 从lists中移除仓库
- ❌ 批量操作starred lists

### 🚀 快速开始

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **配置GitHub Token**
```bash
# 创建token文件（可选，但强烈建议）
echo "your_github_token_here" > starring_accessed_token
```

3. **启动服务器**
```bash
python start_github_star_server.py
```

4. **连接AI助手**
服务器将在 `http://localhost:8000` 启动，支持MCP协议连接。

