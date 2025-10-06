#!/usr/bin/env python3
"""
ArXiv论文源码搜索和下载工具

该工具可以：
1. 根据关键词搜索arXiv上的论文
2. 下载论文的PDF文件
3. 下载论文的LaTeX源码文件
"""

import os
import re
import requests
import tarfile
import zipfile
from typing import List, Optional
from datetime import datetime
import feedparser
from pathlib import Path

class ArxivSourceDownloader:
    """Arxiv论文源码下载器"""
    
    ARXIV_API_URL = "http://export.arxiv.org/api/query"
    ARXIV_PDF_URL = "https://arxiv.org/pdf/"
    ARXIV_SOURCE_URL = "https://arxiv.org/e-print/"
    
    def __init__(self, save_path: str = "./data/arxiv_data/"):
        """
        初始化下载器
        
        Args:
            save_path: 文件保存路径
        """
        self.save_path = Path(save_path)
        self.save_path.mkdir(parents=True, exist_ok=True)
        
    def search_papers(self, keywords: List[str], max_results: int = 10) -> List[dict]:
        """
        根据关键词搜索论文
        
        Args:
            keywords: 搜索关键词列表
            max_results: 最大返回结果数
            
        Returns:
            论文信息列表
        """
        # 构建搜索查询
        search_query = " OR ".join([f"all:{keyword}" for keyword in keywords])
        
        params = {
            'search_query': search_query,
            'max_results': max_results,
            'sortBy': 'relevance',
            'sortOrder': 'descending'
        }
        
        response = requests.get(self.ARXIV_API_URL, params=params)
        feed = feedparser.parse(response.content)
        
        papers = []
        for entry in feed.entries:
            try:
                # 提取论文信息
                paper_id = entry.id.split('/')[-1]
                authors = [author.name for author in entry.authors]
                
                paper_info = {
                    'id': paper_id,
                    'title': entry.title,
                    'authors': authors,
                    'summary': entry.summary,
                    'published': entry.published,
                    'updated': entry.updated,
                    'pdf_url': f"{self.ARXIV_PDF_URL}{paper_id}",
                    'source_url': f"{self.ARXIV_SOURCE_URL}{paper_id}"
                }
                
                papers.append(paper_info)
            except Exception as e:
                print(f"解析论文信息时出错: {e}")
                continue
                
        return papers
    
    def download_pdf(self, paper_id: str, save_path: Optional[str] = None) -> str:
        """
        下载论文PDF文件
        
        Args:
            paper_id: 论文ID
            save_path: 保存路径
            
        Returns:
            PDF文件保存路径
        """
        if save_path is None:
            save_path = str(self.save_path)
            
        pdf_url = f"{self.ARXIV_PDF_URL}{paper_id}"
        
        print(f"正在下载PDF: {pdf_url}")
        response = requests.get(pdf_url)
        
        if response.status_code != 200:
            raise Exception(f"下载PDF失败，状态码: {response.status_code}")
            
        # 保存PDF文件
        pdf_filename = f"{paper_id}.pdf"
        pdf_path = os.path.join(save_path, pdf_filename)
        
        with open(pdf_path, 'wb') as f:
            f.write(response.content)
            
        print(f"PDF已保存至: {pdf_path}")
        return pdf_path
    
    def download_source(self, paper_id: str, save_path: Optional[str] = None) -> str:
        """
        下载论文源码文件
        
        Args:
            paper_id: 论文ID
            save_path: 保存路径
            
        Returns:
            源码文件保存路径
        """
        if save_path is None:
            save_path = str(self.save_path)
            
        source_url = f"{self.ARXIV_SOURCE_URL}{paper_id}"
        
        print(f"正在下载源码: {source_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(source_url, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"下载源码失败，状态码: {response.status_code}")
            
        # 保存源码文件
        content_type = response.headers.get('content-type', '')
        if 'tar' in content_type or 'gzip' in content_type:
            source_filename = f"{paper_id}.tar.gz"
        elif 'zip' in content_type:
            source_filename = f"{paper_id}.zip"
        else:
            # 默认使用tar.gz格式
            source_filename = f"{paper_id}.tar.gz"
            
        source_path = os.path.join(save_path, source_filename)
        
        with open(source_path, 'wb') as f:
            f.write(response.content)
            
        print(f"源码已保存至: {source_path}")
        return source_path
    
    def extract_source(self, source_path: str, extract_path: Optional[str] = None) -> str:
        """
        解压源码文件
        
        Args:
            source_path: 源码文件路径
            extract_path: 解压路径
            
        Returns:
            解压后的目录路径
        """
        if extract_path is None:
            extract_path = os.path.dirname(source_path)
            
        # 创建解压目录
        paper_id = os.path.basename(source_path).replace('.tar.gz', '').replace('.zip', '')
        extract_dir = os.path.join(extract_path, f"{paper_id}_source")
        os.makedirs(extract_dir, exist_ok=True)
        
        print(f"正在解压源码: {source_path}")
        
        try:
            # 尝试解压tar.gz文件
            if source_path.endswith('.tar.gz'):
                with tarfile.open(source_path, 'r:gz') as tar:
                    tar.extractall(path=extract_dir)
            # 尝试解压zip文件
            elif source_path.endswith('.zip'):
                with zipfile.ZipFile(source_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
            else:
                # 尝试作为tar.gz处理
                with tarfile.open(source_path, 'r:gz') as tar:
                    tar.extractall(path=extract_dir)
                    
            print(f"源码已解压至: {extract_dir}")
            return extract_dir
            
        except Exception as e:
            print(f"解压源码时出错: {e}")
            # 尝试重命名为.zip后再解压
            try:
                zip_path = source_path + '.zip'
                os.rename(source_path, zip_path)
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                print(f"源码已解压至: {extract_dir}")
                return extract_dir
            except Exception as e2:
                print(f"重试解压也失败: {e2}")
                # raise Exception(f"无法解压源码文件: {e}")
    
    def download_paper_with_source(self, paper_id: str) -> dict:
        """
        下载论文PDF和源码
        
        Args:
            paper_id: 论文ID
            
        Returns:
            下载信息字典
        """
        result = {
            'paper_id': paper_id,
            'pdf_path': None,
            'source_path': None,
            'extract_path': None,
            'success': False
        }
        
        try:
            # 下载PDF
            result['pdf_path'] = self.download_pdf(paper_id)
            
            # 下载源码
            result['source_path'] = self.download_source(paper_id)
            
            # 解压源码
            result['extract_path'] = self.extract_source(result['source_path'])
            
            result['success'] = True
            print(f"论文 {paper_id} 下载完成")
            
        except Exception as e:
            print(f"下载论文 {paper_id} 时出错: {e}")
            
        return result

def main():
    """主函数 - 示例用法"""
    # 搜索关键词
    # keywords = ["medical", "health", "MIMIC", "eICU"]
    keywords = ["MIMIC", "eICU"]
    
    for keyword in keywords:
        # 创建下载器
        downloader = ArxivSourceDownloader("./data/arxiv_data/")
        
        print("正在搜索论文...")
        papers = downloader.search_papers([keyword], max_results=1000)
        
        if not papers:
            print("未找到相关论文")
            return
            
        print(f"找到 {len(papers)} 篇论文:")
        for i, paper in enumerate(papers):
            print(f"{i+1}/{len(papers)}: {paper['title']}")
            print(f"   ID: {paper['id']}")
            print(f"   作者: {', '.join(paper['authors'])}")
        
            # 下载第一篇论文的PDF和源码
            paper_id = paper['id']
            print(f"正在下载论文 {paper_id} 的PDF和源码...")
            result = downloader.download_paper_with_source(paper_id)
        
        if result['success']:
            print("下载成功:")
            print(f"  PDF路径: {result['pdf_path']}")
            print(f"  源码路径: {result['source_path']}")
            print(f"  解压路径: {result['extract_path']}")
        else:
            print("下载失败")

if __name__ == "__main__":
    main()