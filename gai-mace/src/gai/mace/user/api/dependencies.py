from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Dict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix='GAIMACE_')    
    API_HOST: str = "http://localhost:12033"
    MODE: str = "user"
    NATS: str = "nats://nats01:4222"
    TTT: str = "http://gai-ttt-svr:12031"
    TTS: str = "http://gai-tts-svr:12032"
    STT: str = "http://gai-stt-svr:12033"
    TTI: str = "http://gai-itt-svr:12034"
    ITT: str = "http://gai-tti-svr:12035"
    RAG: str = "http://gai-rag-svr:12036"
    PERSONA: Optional[str|None] = None
    REACT_URL: str = "http://localhost:5123"
    
def get_settings():
    return Settings()
    

class ImageCache:
    Image128: Dict[str, bytes] = {}
    Image64: Dict[str, bytes] = {}
    
    def __init__(self):
        pass
    
def get_imagecache():
    return ImageCache()