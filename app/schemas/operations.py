from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class DownloadCreate(BaseModel):
    boat: str = Field(min_length=1, max_length=200)
    owner: str = Field(min_length=1, max_length=200)

class PieceCreate(BaseModel):
    weight_kg: float = Field(ge=5, le=350)
    second_hole: bool = False
    loin: bool = False
    destination: str = Field(pattern=r"^(Caminhão|Fábrica)$")

class Prices(BaseModel):
    kg_15_24: float = Field(ge=0)
    kg_25_39: float = Field(ge=0)
    kg_40_up: float = Field(ge=0)
    second_hole: float = Field(ge=0)
    loin: float = Field(ge=0)

class ManifestRequest(BaseModel):
    prices: Prices

class DownloadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    boat: str
    owner: str
    started_at: datetime
    status: str
