

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

# Multilingual email templates
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
    """Get the email content based on the template key and language"""
    if language not in EMAIL_TEMPLATES:
        language = "chs"  # Default to Chinese if language not found
    
    template = EMAIL_TEMPLATES[language].get(template_key, "")
    return template.format(**kwargs)

def send_localized_email(config: Config, template_key: str, recipients: Union[str, List[str]], 
                        attachments: Optional[Union[str, List[str]]] = None, **kwargs):
    try:
        """Send a localized email"""
        language = config.llm.language
        
        # Determine email subject based on template key
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
        
        # Get localized subject and content
        subject = get_email_content(subject_key, language, thread_id=config.thread_id)
        content = get_email_content(template_key, language, 
                                thread_id=config.thread_id,
                                url="https://app.openlens.icu/",
                                **kwargs)
        
        # Send email
        send_email(config, subject, content, recipients, attachments)
    except Exception as e:
        logger.error(f"Failed to send localized email: {e}")
        logger.error(traceback.format_exc())
        

def send_email(config: Config, subject: str, content: str, recipients: Union[str, List[str]], attachments: Optional[Union[str, List[str]]] = None):
    """
    Send email with support for arbitrary subject, content and attachments
    
    Args:
        subject (str): Email subject
        content (str): Email body content
        attachments (List[str], optional): List of attachment file paths
        recipients (List[str], optional): List of recipients, defaults to EMAIL_TO from environment variables
    """
    
    SMTP_SERVER = config.email_server.smtp_server  # SMTP server address
    SMTP_PORT = config.email_server.smtp_port  # SMTP port number
    EMAIL_USER = config.email_server.email_user  # Sender email
    EMAIL_PASSWORD = config.email_server.email_password  # Sender email password
    logger.debug(f"SMTP_SERVER: {SMTP_SERVER}")
    logger.debug(f"SMTP_PORT: {SMTP_PORT}")
    logger.debug(f"EMAIL_USER: {EMAIL_USER}")
    logger.debug(f"EMAIL_PASSWORD: {EMAIL_PASSWORD}")
    
    
    if not SMTP_SERVER:
        logger.warning("SMTP server not configured, please check environment variables SMTP_SERVER and SMTP_PORT")
        return
    
    # If no recipients are provided, use the default recipients from environment variables
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

    # Add email body
    html_content = markdown.markdown(content)
    msg.attach(MIMEText(html_content, "html"))
    # print(html_content)

    # Add attachments
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
                logger.info(f"Warning: Attachment {file_path} does not exist, skipped")

    # Connect to SMTP server and send email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        result = server.sendmail(EMAIL_USER, recipients, msg.as_string())
        logger.debug(f"Email sending result: {result}")
        server.quit()
        logger.info(f"Email sent to {', '.join(recipients)}")
    except Exception as e:
        logger.warning(f"Error sending email: {e}")
        

if __name__ == "__main__":
    # Test email sending functionality
    subject = "Test Email"
    content = "This is a test email, please ignore."
    recipients = ["dzdzzd@126.com"]
    attachments = ["openlens_ai/utils/send_email.py"]
    config = Config.from_toml("config.toml")
    # send_email(config, subject, content, recipients, attachments)
    send_localized_email(config, "job_complete", recipients, attachments, latest_md="")