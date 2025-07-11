#!/usr/bin/env python3
"""
GitHub Star API 模块
提供GitHub用户star列表相关的原子化功能
"""

import aiohttp
import asyncio
import json
from typing import Any, List, Dict, Optional
import logging
from datetime import datetime
import base64

logger = logging.getLogger("github_star_api")

class GitHubStarAPI:
    """GitHub Star API 封装类"""
    
    def __init__(self, token: Optional[str] = None):
        """
        初始化GitHub API客户端
        
        Args:
            token: GitHub Personal Access Token (可选，但推荐用于提高API限制)
        """
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "MCP-GitHub-Star-Classifier/1.0"
        }
        
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    async def _make_request(self, session: aiohttp.ClientSession, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """发起HTTP请求"""
        try:
            async with session.request(method, url, headers=self.headers, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise ValueError(f"未找到资源: {url}")
                elif response.status == 403:
                    raise ValueError("API限制或权限不足，请检查token")
                elif response.status == 401:
                    raise ValueError("认证失败，请检查token")
                else:
                    text = await response.text()
                    raise ValueError(f"API请求失败 (状态码: {response.status}): {text}")
        except aiohttp.ClientError as e:
            raise ValueError(f"网络请求错误: {str(e)}")
    
    async def get_user_starred_repos(self, username: str, page: int = 1, per_page: int = 30, sort: str = "created") -> Dict[str, Any]:
        """
        获取用户的starred仓库列表
        
        Args:
            username: GitHub用户名
            page: 页码 (默认: 1)
            per_page: 每页数量 (默认: 30, 最大: 100)
            sort: 排序方式 (created, updated)
        
        Returns:
            包含starred仓库列表的字典
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/users/{username}/starred"
            params = {
                "page": page,
                "per_page": min(per_page, 100),
                "sort": sort
            }
            
            repos = await self._make_request(session, "GET", url, params=params)
            
            # 简化仓库信息
            simplified_repos = []
            for repo in repos:
                simplified_repos.append({
                    "id": repo["id"],
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo["description"],
                    "language": repo["language"],
                    "stars": repo["stargazers_count"],
                    "forks": repo["forks_count"],
                    "url": repo["html_url"],
                    "clone_url": repo["clone_url"],
                    "created_at": repo["created_at"],
                    "updated_at": repo["updated_at"],
                    "topics": repo.get("topics", []),
                    "license": repo["license"]["name"] if repo["license"] else None,
                    "archived": repo["archived"],
                    "fork": repo["fork"]
                })
            
            return {
                "username": username,
                "page": page,
                "per_page": per_page,
                "total_count": len(simplified_repos),
                "repositories": simplified_repos
            }
    
    async def search_starred_repos(self, username: str, query: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        在用户的starred仓库中搜索
        
        Args:
            username: GitHub用户名
            query: 搜索关键词
            language: 编程语言过滤 (可选)
        
        Returns:
            搜索结果
        """
        # 先获取所有starred仓库
        all_repos = []
        page = 1
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.base_url}/users/{username}/starred"
                params = {"page": page, "per_page": 100}
                
                repos = await self._make_request(session, "GET", url, params=params)
                if not repos:
                    break
                
                all_repos.extend(repos)
                page += 1
                
                # 防止无限循环，最多获取1000个仓库
                if len(all_repos) >= 1000:
                    break
        
        # 搜索匹配的仓库
        matched_repos = []
        query_lower = query.lower()
        
        for repo in all_repos:
            # 搜索仓库名、描述、topics
            match_fields = [
                repo["name"].lower(),
                (repo["description"] or "").lower(),
                " ".join(repo.get("topics", [])).lower()
            ]
            
            # 语言过滤
            if language and repo["language"] and repo["language"].lower() != language.lower():
                continue
            
            # 关键词匹配
            if any(query_lower in field for field in match_fields):
                matched_repos.append({
                    "id": repo["id"],
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo["description"],
                    "language": repo["language"],
                    "stars": repo["stargazers_count"],
                    "url": repo["html_url"],
                    "topics": repo.get("topics", [])
                })
        
        return {
            "username": username,
            "query": query,
            "language_filter": language,
            "total_starred": len(all_repos),
            "matched_count": len(matched_repos),
            "results": matched_repos
        }
    
    async def get_repo_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        获取仓库详细信息
        
        Args:
            owner: 仓库所有者
            repo: 仓库名
        
        Returns:
            仓库详细信息
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/repos/{owner}/{repo}"
            repo_data = await self._make_request(session, "GET", url)
            
            return {
                "id": repo_data["id"],
                "name": repo_data["name"],
                "full_name": repo_data["full_name"],
                "description": repo_data["description"],
                "language": repo_data["language"],
                "stars": repo_data["stargazers_count"],
                "forks": repo_data["forks_count"],
                "watchers": repo_data["watchers_count"],
                "open_issues": repo_data["open_issues_count"],
                "url": repo_data["html_url"],
                "clone_url": repo_data["clone_url"],
                "ssh_url": repo_data["ssh_url"],
                "created_at": repo_data["created_at"],
                "updated_at": repo_data["updated_at"],
                "pushed_at": repo_data["pushed_at"],
                "size": repo_data["size"],
                "topics": repo_data.get("topics", []),
                "license": repo_data["license"]["name"] if repo_data["license"] else None,
                "archived": repo_data["archived"],
                "disabled": repo_data["disabled"],
                "fork": repo_data["fork"],
                "default_branch": repo_data["default_branch"],
                "owner": {
                    "login": repo_data["owner"]["login"],
                    "type": repo_data["owner"]["type"],
                    "url": repo_data["owner"]["html_url"]
                }
            }
    
    async def check_if_starred(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        检查当前用户是否已starred某个仓库 (需要token)
        
        Args:
            owner: 仓库所有者
            repo: 仓库名
        
        Returns:
            starred状态信息
        """
        if not self.token:
            raise ValueError("此功能需要提供GitHub token")
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/user/starred/{owner}/{repo}"
            try:
                await self._make_request(session, "GET", url)
                starred = True
            except ValueError as e:
                if "未找到资源" in str(e):
                    starred = False
                else:
                    raise
            
            return {
                "owner": owner,
                "repo": repo,
                "starred": starred
            }
    
    async def star_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        给仓库加star (需要token)
        
        Args:
            owner: 仓库所有者
            repo: 仓库名
        
        Returns:
            操作结果
        """
        if not self.token:
            raise ValueError("此功能需要提供GitHub token")
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/user/starred/{owner}/{repo}"
            
            try:
                async with session.put(url, headers=self.headers) as response:
                    if response.status == 204:
                        return {
                            "owner": owner,
                            "repo": repo,
                            "action": "starred",
                            "success": True,
                            "message": "仓库已成功加星"
                        }
                    else:
                        text = await response.text()
                        raise ValueError(f"加星失败 (状态码: {response.status}): {text}")
            except aiohttp.ClientError as e:
                raise ValueError(f"网络请求错误: {str(e)}")
    
    async def unstar_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        取消仓库star (需要token)
        
        Args:
            owner: 仓库所有者
            repo: 仓库名
        
        Returns:
            操作结果
        """
        if not self.token:
            raise ValueError("此功能需要提供GitHub token")
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/user/starred/{owner}/{repo}"
            
            try:
                async with session.delete(url, headers=self.headers) as response:
                    if response.status == 204:
                        return {
                            "owner": owner,
                            "repo": repo,
                            "action": "unstarred",
                            "success": True,
                            "message": "仓库已成功取消加星"
                        }
                    else:
                        text = await response.text()
                        raise ValueError(f"取消加星失败 (状态码: {response.status}): {text}")
            except aiohttp.ClientError as e:
                raise ValueError(f"网络请求错误: {str(e)}")
    
    async def get_starred_stats(self, username: str) -> Dict[str, Any]:
        """
        获取用户starred仓库的统计信息
        
        Args:
            username: GitHub用户名
        
        Returns:
            统计信息
        """
        # 获取所有starred仓库
        all_repos = []
        page = 1
        
        async with aiohttp.ClientSession() as session:
            while True:
                url = f"{self.base_url}/users/{username}/starred"
                params = {"page": page, "per_page": 100}
                
                repos = await self._make_request(session, "GET", url, params=params)
                if not repos:
                    break
                
                all_repos.extend(repos)
                page += 1
                
                # 防止无限循环
                if len(all_repos) >= 1000:
                    break
        
        # 统计分析
        language_stats = {}
        total_stars = 0
        total_forks = 0
        topics_stats = {}
        license_stats = {}
        
        for repo in all_repos:
            # 语言统计
            lang = repo["language"] or "Unknown"
            language_stats[lang] = language_stats.get(lang, 0) + 1
            
            # Stars和forks统计
            total_stars += repo["stargazers_count"]
            total_forks += repo["forks_count"]
            
            # Topics统计
            for topic in repo.get("topics", []):
                topics_stats[topic] = topics_stats.get(topic, 0) + 1
            
            # License统计
            license_name = repo["license"]["name"] if repo["license"] else "No License"
            license_stats[license_name] = license_stats.get(license_name, 0) + 1
        
        # 排序统计结果
        sorted_languages = sorted(language_stats.items(), key=lambda x: x[1], reverse=True)
        sorted_topics = sorted(topics_stats.items(), key=lambda x: x[1], reverse=True)[:20]  # 前20个topic
        sorted_licenses = sorted(license_stats.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "username": username,
            "total_starred_repos": len(all_repos),
            "total_stars_received": total_stars,
            "total_forks_received": total_forks,
            "language_distribution": dict(sorted_languages),
            "top_topics": dict(sorted_topics),
            "license_distribution": dict(sorted_licenses),
            "avg_stars_per_repo": round(total_stars / len(all_repos), 2) if all_repos else 0,
            "avg_forks_per_repo": round(total_forks / len(all_repos), 2) if all_repos else 0
        }
    
    async def get_repo_languages(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        获取仓库的编程语言分布
        
        Args:
            owner: 仓库所有者
            repo: 仓库名
        
        Returns:
            语言分布信息
        """
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/repos/{owner}/{repo}/languages"
            languages = await self._make_request(session, "GET", url)
            
            total_bytes = sum(languages.values())
            language_percentages = {}
            
            for lang, bytes_count in languages.items():
                percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                language_percentages[lang] = {
                    "bytes": bytes_count,
                    "percentage": round(percentage, 2)
                }
            
            return {
                "owner": owner,
                "repo": repo,
                "total_bytes": total_bytes,
                "languages": language_percentages
            }
 