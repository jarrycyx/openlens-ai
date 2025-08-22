import dotenv
dotenv.load_dotenv()
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional, Union
import glob
import zipfile
from datetime import datetime
from loguru import logger
import markdown

from .config import Config

# 从环境变量读取邮件配置
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.yeah.net')  # SMTP服务器地址
SMTP_PORT = int(os.getenv('SMTP_PORT', '25'))  # SMTP端口号
EMAIL_USER = os.getenv('EMAIL_USER', '')  # 发件人邮箱
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')  # 发件人邮箱密码
logger.info(f"SMTP_SERVER: {SMTP_SERVER}")
logger.info(f"SMTP_PORT: {SMTP_PORT}")
logger.info(f"EMAIL_USER: {EMAIL_USER}")
logger.info(f"EMAIL_PASSWORD: {EMAIL_PASSWORD}")

def collect_files(config: Config):
    save_path = config.save_path
    
    # 定义需要收集的文件类型
    file_patterns = ['*.py', '*.json', '*.md', '*.txt', '*.tex', '*.bib', '*.sty', '*.pdf']
    
    # 收集所有匹配的文件
    files = []
    for pattern in file_patterns:
        files.extend(glob.glob(os.path.join(save_path, '**', pattern), recursive=True))
    
    # 创建压缩文件夹路径
    compressed_dir = os.path.join(save_path, 'compressed')
    os.makedirs(compressed_dir, exist_ok=True)
    
    # 创建以时间戳命名的zip文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_filename = f"files_{timestamp}.zip"
    zip_filepath = os.path.join(compressed_dir, zip_filename)
    
    # 将文件打包成zip
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in files:
            # 将文件添加到zip中，保持相对路径结构
            arcname = os.path.relpath(file, save_path)
            zipf.write(file, arcname)
    
    # 按修改时间排序.md文件，返回最新的一个
    md_files = [f for f in files if f.endswith('.md')]
    latest_md_file = None
    latest_md = ""
    if md_files:
        md_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        latest_md_file = md_files[0]
    if latest_md_file:
        with open(latest_md_file, 'r', encoding='utf-8') as f:
            latest_md = f.read()
    
    return zip_filepath, latest_md


def send_email(subject: str, content: str, recipients: Union[str, List[str]], attachments: Optional[Union[str, List[str]]] = None):
    """
    发送邮件，支持任意主题、内容和附件
    
    Args:
        subject (str): 邮件主题
        content (str): 邮件正文内容
        attachments (List[str], optional): 附件文件路径列表
        recipients (List[str], optional): 收件人列表，默认使用环境变量中的EMAIL_TO
    """
    # 如果没有提供收件人，则使用环境变量中的默认收件人
    if recipients is None:
        recipients = [EMAIL_TO] if EMAIL_TO else []
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
        server.sendmail(EMAIL_USER, recipients, msg.as_string())
        server.quit()
        logger.info(f"邮件已发送至 {', '.join(recipients)}")
    except Exception as e:
        logger.warning(f"发送邮件时出错: {e}")