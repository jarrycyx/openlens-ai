import os
import requests
import yaml
from github import Github
from concurrent.futures import ThreadPoolExecutor
from time import sleep
import tqdm
import dotenv

dotenv.load_dotenv()

# pip install PyGithub requests pyyaml

# ================== 配置部分 ==================
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # 从环境变量读取Token
# SEARCH_KEYWORDS = ["mimic medical", "eicu medical", "medical", "health"]  # 搜索关键词列表
# KEYWORDS_REPO_NUM = [2000, 2000, 500, 500]
SEARCH_KEYWORDS = ["eicu medical", "medical", "health"]  # 搜索关键词列表
KEYWORDS_REPO_NUM = [2000, 500, 500]
OUTPUT_DIR = "data/downloaded_py_md_sh_sql"  # 输出目录
FILE_EXT = ["py", "sh", "md", "sql"]
# FILE_EXT = ["sql"]
MAX_WORKERS = 5  # 并发线程数
# ==============================================

# 全局变量用于统计文件数和字符数
total_file_cnt = 0
total_char_cnt = 0


def initialize_github():
    """初始化GitHub连接[6,8](@ref)"""
    try:
        return Github(login_or_token=GITHUB_TOKEN, per_page=30)
    except Exception as e:
        print(f"GitHub连接失败: {str(e)}")
        exit(1)

def search_repos_with_keywords(g, keyword, max_repos=100):
    """执行高级GitHub搜索包含特定关键词的仓库[7](@ref)"""
    search_res = []
    print(f"🔍 正在搜索包含 '{keyword}' 的仓库，最大{max_repos}")
    try:
        # 使用PyGithub搜索仓库
        results = g.search_repositories(
            query=keyword,
        )
        res = [{
            "repo": item.full_name,
            "description": item.description,
            "stars": item.stargazers_count,
        } for item in tqdm.tqdm(results[:max_repos])]  # 取前30个结果避免超限
        print(f"找到 {len(res)} 个包含 '{keyword}' 的仓库")
        res = [r for r in res if r["stars"] >= 5]
        print(f"大于5 stars的仓库有 {len(res)} 个")
        search_res.extend(res)
    except Exception as e:
        print(f"搜索包含 '{keyword}' 的仓库失败: {str(e)}")
        return search_res
    
    return search_res

def get_repo_contents(g, repo_full_name):
    """获取仓库中的所有文件[2,5](@ref)"""
    try:
        repo = g.get_repo(repo_full_name)
        contents = repo.get_contents("")
        files = []
        
        while contents:
            file_content = contents.pop(0)
            if file_content.type == "dir":
                # 如果是目录，获取目录下的内容
                try:
                    contents.extend(repo.get_contents(file_content.path))
                except:
                    continue
            else:
                # 如果是文件，添加到列表中
                files.append({
                    "repo": repo_full_name,
                    "path": file_content.path,
                    "download_url": file_content.download_url
                })
        return files
    except Exception as e:
        print(f"获取仓库 {repo_full_name} 内容失败: {str(e)}")
        return []

def download_single_file(item):
    """多线程下载单个文件[2,5](@ref)"""
    global total_file_cnt, total_char_cnt
    try:
        # 获取文件下载URL
        raw_url = item['download_url']
        if not raw_url:
            # 如果没有直接的下载链接，构造原始文件URL
            raw_url = f"https://raw.githubusercontent.com/{item['repo']}/main/{item['path']}"
        
        # if raw_url.split('.')[-1] not in ['py', 'sh', 'md']:
        if raw_url.split('.')[-1] not in FILE_EXT:
            print(f"跳过非文本文件: {item['path']}")
            return
        
        # 发起带重试机制的请求
        for _ in range(3):
            response = requests.get(raw_url, timeout=10)
            if response.status_code == 200:
                break
            sleep(1)
        else:
            print(f"下载失败: {raw_url}")
            return

        # 处理文件路径和名称
        # 使用仓库名作为子文件夹（去除其中的"/"字符）
        repo_name = item['repo'].replace("/", "_")
        repo_dir = os.path.join(OUTPUT_DIR, repo_name)
        file_path = os.path.join(repo_dir, item['path'])
        
        # 创建目录
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # 更新全局统计变量
        total_file_cnt += 1
        total_char_cnt += len(response.text)
        
        print(f"✅ 下载完成: {repo_name}/{item['path']}，总文件: {total_file_cnt}，字符: {total_char_cnt}")

    except Exception as e:
        print(f"处理 {item.get('path', 'unknown')} 异常: {str(e)}")

def main():
    global total_file_cnt, total_char_cnt
    # 初始化目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # GitHub连接
    g = initialize_github()
    
    # 针对每个关键词搜索仓库
    for keyword, kw_repo_num in zip(SEARCH_KEYWORDS, KEYWORDS_REPO_NUM):
        # 执行搜索
        repos = search_repos_with_keywords(g, keyword, kw_repo_num)
        print(f"找到 {len(repos)} 个包含 '{keyword}' 的仓库")
        
        # 获取每个仓库中的文件并立即下载
        for repo in repos:
            print(f"正在获取仓库 {repo['repo']} 的文件列表...")
            files = get_repo_contents(g, repo['repo'])
            print(f"从 {repo['repo']} 找到 {len(files)} 个文件")
            
            # 立即下载当前仓库的所有文件
            if files:
                print(f"开始下载仓库 {repo['repo']} 的文件...")
                with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                    list(tqdm.tqdm(executor.map(download_single_file, files), total=len(files)))
                print(f"仓库 {repo['repo']} 的文件下载完成")
    
    # 显示最终统计结果
    print(f"✅ 所有任务完成，总共下载了 {total_file_cnt} 个文件，字符总数: {total_char_cnt}")

if __name__ == "__main__":
    main()