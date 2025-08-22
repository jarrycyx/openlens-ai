from pydantic import BaseModel
from typing import Optional


class Config(BaseModel):
    """
    Configuration model for OpenLens AI application.
    This model represents the configuration structure used throughout the application.
    """
    save_path: str
    thread_id: str
    question: str
    dataset_path: str
    email: str