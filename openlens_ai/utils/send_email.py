import dotenv
dotenv.load_dotenv()
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
import json

# 从环境变量读取邮件配置
SMTP_SERVER = os.getenv('SMTP_SERVER', '')  # SMTP服务器地址
SMTP_PORT = int(os.getenv('SMTP_PORT', ''))  # SMTP端口号
EMAIL_USER = os.getenv('EMAIL_USER', '')  # 发件人邮箱
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')  # 发件人邮箱密码
EMAIL_TO = os.getenv('EMAIL_TO', '')
logger.info(f"SMTP_SERVER: {SMTP_SERVER}")
logger.info(f"SMTP_PORT: {SMTP_PORT}")
logger.info(f"EMAIL_USER: {EMAIL_USER}")
logger.info(f"EMAIL_PASSWORD: {EMAIL_PASSWORD}")


def send_email(subject: str, content: str, recipients: Union[str, List[str]], attachments: Optional[Union[str, List[str]]] = None):
    """
    发送邮件，支持任意主题、内容和附件
    
    Args:
        subject (str): 邮件主题
        content (str): 邮件正文内容
        attachments (List[str], optional): 附件文件路径列表
        recipients (List[str], optional): 收件人列表，默认使用环境变量中的EMAIL_TO
    """
    if not SMTP_SERVER:
        logger.warning("SMTP server not configured, please check environment variables SMTP_SERVER and SMTP_PORT")
        return
    
    # 如果没有提供收件人，则使用环境变量中的默认收件人
    if recipients is None:
        recipients = [EMAIL_TO] if EMAIL_TO else []
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
        logger.info(f"邮件发送结果: {result}")
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
    send_email(subject, content, recipients, attachments)