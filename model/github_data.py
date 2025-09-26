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
SEARCH_KEYWORD = "filename:.yaml"  # 搜索关键词
OUTPUT_DIR = "data/downloaded_yamls"  # 输出目录
MAX_WORKERS = 5  # 并发线程数
# ==============================================




def initialize_github():
    """初始化GitHub连接[6,8](@ref)"""
    try:
        return Github(login_or_token=GITHUB_TOKEN, per_page=30)
    except Exception as e:
        print(f"GitHub连接失败: {str(e)}")
        exit(1)

def search_yaml_files(g, page=0):
    """执行高级GitHub搜索[7](@ref)"""
    search_res = []
    print(f"🔍 正在搜索第 {page} 页...")
    try:
        # 使用PyGithub搜索代码（限制：只能获取前1000个结果）
        results = g.search_code(
            query=SEARCH_KEYWORD + f" p:{page}",
            sort="indexed",
            order="desc",
        )
        res = [{
            "repo": item.repository.full_name,
            "path": item.path,
            "sha": item.sha
        } for item in results[:30]]  # 取前50个结果避免超限
        search_res.extend(res)
    except Exception as e:
        print(f"搜索失败: {str(e)}")
        return search_res
    
    return search_res

def download_single_file(item):
    """多线程下载单个文件[2,5](@ref)"""
    try:
        # 构造原始文件URL
        raw_url = f"https://raw.githubusercontent.com/{item['repo']}/main/{item['path']}"
        
        # 发起带重试机制的请求
        for _ in range(3):
            response = requests.get(raw_url)
            if response.status_code == 200:
                break
            sleep(1)
        else:
            print(f"下载失败: {raw_url}")
            return

        # 处理文件名
        safe_filename = str(abs(hash(item['path']))) + ".yaml"
        output_path = os.path.join(OUTPUT_DIR, safe_filename)
        
        # 保存文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # 验证YAML有效性[1,3](@ref)
        try:
            with open(output_path, 'r') as f:
                yaml.safe_load(f)
            print(f"✅ 验证通过: {safe_filename}")
        except yaml.YAMLError as e:
            print(f"❌ 无效YAML: {safe_filename} - {str(e)}")
            os.remove(output_path)  # 删除无效文件

    except Exception as e:
        print(f"处理异常: {str(e)}")

def main():
    # 初始化目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # GitHub连接
    g = initialize_github()
    
    for page in range(100):
        # 执行搜索
        items = search_yaml_files(g, page=page+1)
        print(f"找到 {len(items)} 个文件")
        
        # 并发下载
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            executor.map(download_single_file, items)
    
    print("✅ 所有任务完成")

if __name__ == "__main__":
    main()