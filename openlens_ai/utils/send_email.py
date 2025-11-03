

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional, Union
from datetime import datetime
from loguru import logger
import markdown


from .config import Config

# 多语言邮件模板
EMAIL_TEMPLATES = {
    "chs": {
        "job_start": "OpenLens 任务已启动 | {thread_id}",
        "job_progress": "OpenLens 任务进度 | {thread_id}",
        "job_paused": "OpenLens 任务已暂停 | {thread_id}",
        "job_update": "OpenLens 任务更新 | {thread_id}",
        "job_failed": "OpenLens 任务失败 | {thread_id}",
        "job_successful": "OpenLens 任务成功 | {thread_id}",
        "job_still_running": "任务仍在运行中。当前进度：\n\n{latest_md}",
        "subgraph_paused": "子图 {state_name} 已暂停。点击[这里]({url})查看并恢复。\n\n{latest_md}",
        "subgraph_complete": "子图 {state_name} 已完成。\n\n{latest_md}",
        "failed_to_run": "运行失败：{error}\n{error_info}\n\n{latest_md}",
        "all_subgraphs_completed": "所有子图已成功完成。",
        "job_complete": "任务已成功完成。\n\n{latest_md}",
        "failed_to_build": "构建失败：{error}\n{error_info}"
    },
    "eng": {
        "job_start": "OpenLens Job Started | {thread_id}",
        "job_progress": "OpenLens Job Progress | {thread_id}",
        "job_paused": "OpenLens Job Paused | {thread_id}",
        "job_update": "OpenLens Job Update | {thread_id}",
        "job_failed": "OpenLens Job Failed | {thread_id}",
        "job_successful": "OpenLens Job Successful | {thread_id}",
        "job_still_running": "Job is still running. Current progress:\n\n{latest_md}",
        "subgraph_paused": "Subgraph {state_name} paused. Click [here]({url}) to review and resume.\n\n{latest_md}",
        "subgraph_complete": "Subgraph {state_name} complete.\n\n{latest_md}",
        "failed_to_run": "Failed to run graph: {error}\n{error_info}\n\n{latest_md}",
        "all_subgraphs_completed": "All subgraphs completed successfully.",
        "job_complete": "Job completed successfully.\n\n{latest_md}",
        "failed_to_build": "Failed to run build: {error}\n{error_info}"
    }
}

def get_email_content(template_key: str, language: str, **kwargs) -> str:
    """根据语言和模板键获取邮件内容"""
    if language not in EMAIL_TEMPLATES:
        language = "chs"  # 默认使用中文
    
    template = EMAIL_TEMPLATES[language].get(template_key, "")
    return template.format(**kwargs)

def send_localized_email(config: Config, template_key: str, recipients: Union[str, List[str]], 
                        attachments: Optional[Union[str, List[str]]] = None, **kwargs):
    try:
        """发送本地化邮件"""
        language = config.llm.language
        
        # 根据模板键确定邮件主题
        subject_key = template_key
        if template_key == "job_still_running":
            subject_key = "job_progress"
        elif template_key == "subgraph_complete":
            subject_key = "job_update"
        elif template_key == "failed_to_run":
            subject_key = "job_failed"
        elif template_key == "all_subgraphs_completed" or template_key == "job_complete":
            subject_key = "job_successful"
        elif template_key == "failed_to_build":
            subject_key = "job_failed"
        
        # 获取本地化的主题和内容
        subject = get_email_content(subject_key, language, thread_id=config.thread_id)
        content = get_email_content(template_key, language, 
                                thread_id=config.thread_id,
                                url="https://app.openlens.icu/",
                                **kwargs)
        
        # 发送邮件
        send_email(config, subject, content, recipients, attachments)
    except Exception as e:
        logger.error(f"Failed to send localized email: {e}")
        logger.error(traceback.format_exc())
        

def send_email(config: Config, subject: str, content: str, recipients: Union[str, List[str]], attachments: Optional[Union[str, List[str]]] = None):
    """
    发送邮件，支持任意主题、内容和附件
    
    Args:
        subject (str): 邮件主题
        content (str): 邮件正文内容
        attachments (List[str], optional): 附件文件路径列表
        recipients (List[str], optional): 收件人列表，默认使用环境变量中的EMAIL_TO
    """
    
    SMTP_SERVER = config.email_server.smtp_server  # SMTP服务器地址
    SMTP_PORT = config.email_server.smtp_port  # SMTP端口号
    EMAIL_USER = config.email_server.email_user  # 发件人邮箱
    EMAIL_PASSWORD = config.email_server.email_password  # 发件人邮箱密码
    logger.debug(f"SMTP_SERVER: {SMTP_SERVER}")
    logger.debug(f"SMTP_PORT: {SMTP_PORT}")
    logger.debug(f"EMAIL_USER: {EMAIL_USER}")
    logger.debug(f"EMAIL_PASSWORD: {EMAIL_PASSWORD}")
    
    
    if not SMTP_SERVER:
        logger.warning("SMTP server not configured, please check environment variables SMTP_SERVER and SMTP_PORT")
        return
    
    # 如果没有提供收件人，则使用环境变量中的默认收件人
    if not recipients:
        logger.warning("Email recipients not configured, please check environment variable EMAIL_TO or pass argument --email")
        return
        
    if isinstance(recipients, str):
        recipients = [recipients]
    if isinstance(attachments, str):
        attachments = [attachments]
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject

    # 添加邮件正文
    html_content = markdown.markdown(content)
    msg.attach(MIMEText(html_content, "html"))
    # print(html_content)

    # 添加附件
    if attachments:
        for file_path in attachments:
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition', 
                        f'attachment; filename={os.path.basename(file_path)}'
                    )
                    msg.attach(part)
            else:
                logger.info(f"警告: 附件 {file_path} 不存在，已跳过")

    # 连接SMTP服务器并发送邮件
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        result = server.sendmail(EMAIL_USER, recipients, msg.as_string())
        logger.debug(f"邮件发送结果: {result}")
        server.quit()
        logger.info(f"邮件已发送至 {', '.join(recipients)}")
    except Exception as e:
        logger.warning(f"发送邮件时出错: {e}")
        

if __name__ == "__main__":
    # 测试邮件发送功能
    subject = "测试邮件"
    content = "这是一封测试邮件，请忽略。"
    recipients = ["dzdzzd@126.com"]
    attachments = ["openlens_ai/utils/send_email.py"]
    config = Config.from_toml("config.toml")
    # send_email(config, subject, content, recipients, attachments)
    send_localized_email(config, "job_complete", recipients, attachments, latest_md="")
