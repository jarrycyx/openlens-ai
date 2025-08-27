import json
import os
from typing import Dict, List, Any
from loguru import logger
import subprocess
import time
import psutil

PROCESS_FILE = os.path.join("outputs", "processes.json")


class ProcessManager:
    """
    管理OpenLens AI进程的类
    """
    MAX_PROCESSES = 5

    def __init__(self):
        """初始化进程管理器"""
        self.process_file = PROCESS_FILE
        self._ensure_process_file_exists()
        

    def _ensure_process_file_exists(self):
        """确保进程文件存在"""
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
            
        if not os.path.exists(self.process_file):
            with open(self.process_file, 'w') as f:
                json.dump([], f)

    def load_processes(self) -> List[Dict[str, Any]]:
        """加载所有进程信息"""
        try:
            with open(self.process_file, 'r') as f:
                processes = json.load(f)
                processes = self.cleanup_finished_processes(processes)
                return processes
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_processes(self, processes: List[Dict[str, Any]]):
        """保存进程信息到文件"""
        with open(self.process_file, 'w') as f:
            json.dump(processes, f, indent=2)

    def add_process(self, pid: int, thread_id: str) -> bool:
        """添加新进程，如果成功返回True，如果达到最大进程数返回False"""
        processes = self.load_processes()
        
        # 检查是否已达到最大进程数
        if len(processes) >= self.MAX_PROCESSES:
            return False
        
        # 添加新进程
        new_process = {
            'pid': pid,
            'thread_id': thread_id
        }
        processes.append(new_process)
        self.save_processes(processes)
        return True

    def remove_process_by_pid(self, pid: int):
        """根据PID移除进程"""
        processes = self.load_processes()
        processes = [p for p in processes if p.get('pid') != pid]
        self.save_processes(processes)

    def get_process_count(self) -> int:
        """获取当前进程数量"""
        return len(self.load_processes())

    def is_full(self) -> bool:
        """检查进程管理器是否已满"""
        return self.get_process_count() >= self.MAX_PROCESSES

    def cleanup_finished_processes(self, processes):
        """清理已完成的进程"""
        active_processes = []
        
        for process in processes:
            try:
                # 检查进程是否仍在运行
                pid = process['pid']
                os.kill(pid, 0)  # 不发送信号，只检查进程是否存在
                if psutil.Process(pid).status() != "zombie":
                    active_processes.append(process)
                else:
                    logger.info(f"清理异常进程: {process.get('thread_id', 'Unknown')}")
            except Exception as e:
                # 进程不存在或PID无效，跳过该进程
                logger.info(f"清理已完成的进程: {process.get('thread_id', 'Unknown')}")
                pass
        
        if len(active_processes) != len(processes):
            self.save_processes(active_processes)
        return active_processes

    def get_process_list(self) -> List[Dict[str, Any]]:
        """获取当前进程列表"""
        return self.load_processes()


# 全局进程管理器实例
process_manager = ProcessManager()