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
    Class for managing OpenLens AI processes
    """
    MAX_PROCESSES = 10

    def __init__(self):
        """Initialize process manager"""
        self.process_file = PROCESS_FILE
        self._ensure_process_file_exists()
        

    def _ensure_process_file_exists(self):
        """Ensure process file exists"""
        if not os.path.exists("outputs"):
            os.makedirs("outputs")
            
        if not os.path.exists(self.process_file):
            with open(self.process_file, 'w') as f:
                json.dump([], f)

    def load_processes(self) -> List[Dict[str, Any]]:
        """Load all process information"""
        try:
            with open(self.process_file, 'r') as f:
                processes = json.load(f)
                processes = self.cleanup_finished_processes(processes)
                return processes
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_processes(self, processes: List[Dict[str, Any]]):
        """Save process information to file"""
        with open(self.process_file, 'w') as f:
            json.dump(processes, f, indent=2, ensure_ascii=False)

    def add_process(self, pid: int, thread_id: str) -> bool:
        """Add new process, return True if successful, return False if max processes reached"""
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
        """Remove process by PID"""
        processes = self.load_processes()
        processes = [p for p in processes if p.get('pid') != pid]
        self.save_processes(processes)

    def get_process_count(self) -> int:
        """Get current process count"""
        return len(self.load_processes())

    def is_full(self) -> bool:
        """Check if process manager is full"""
        return self.get_process_count() >= self.MAX_PROCESSES

    def cleanup_finished_processes(self, processes):
        """Clean up finished processes"""
        active_processes = []
        
        for process in processes:
            try:
                # Check if process is still running
                pid = process['pid']
                os.kill(pid, 0)  # 不发送信号，只检查进程是否存在
                if psutil.Process(pid).status() != "zombie":
                    active_processes.append(process)
                else:
                    logger.info(f"Clean up abnormal process: {process.get('thread_id', 'Unknown')}")
            except Exception as e:
                # Process doesn't exist or PID is invalid, skip this process
                logger.info(f"Clean up finished process: {process.get('thread_id', 'Unknown')}")
                pass
        
        if len(active_processes) != len(processes):
            self.save_processes(active_processes)
        return active_processes

    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get current process list"""
        return self.load_processes()
    
    def interrupt_process(self, thread_id: str) -> bool:
        """Interrupt process by thread_id"""
        processes = self.load_processes()
        for process in processes:
            if process.get('thread_id') == thread_id:
                pid = process.get('pid')
                try:
                    # Use psutil to terminate process and its children
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    
                    # Terminate child processes first
                    for child in children:
                        child.terminate()
                    
                    # Wait for child processes to end
                    psutil.wait_procs(children, timeout=3)
                    
                    # Terminate parent process
                    parent.terminate()
                    
                    # Remove from process list
                    self.remove_process_by_pid(pid)
                    return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                    logger.error(f"Failed to interrupt process {pid}: {e}")
                    # Even if termination fails, remove from list
                    self.remove_process_by_pid(pid)
                    return False
        return False


# 全局进程管理器实例
process_manager = ProcessManager()