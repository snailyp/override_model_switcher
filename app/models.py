from pydantic import BaseModel

class ChannelInfo(BaseModel):
    channel_name: str
    base_url: str
    api_key: str

class OverrideModelRequest(BaseModel):
    model: str

class ExportChannelInfo(BaseModel):
    channel_name: str
    base_url: str
    api_key: str
