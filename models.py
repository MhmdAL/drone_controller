from pydantic import BaseModel
from typing import List

class Location(BaseModel):
    lat: float
    lng: float

class Point(BaseModel):
    x: float
    y: float
    
class MissionStartRequest(BaseModel):
    id: int
    homeToSourceInstructions: List[Point]
    sourceToDestInstructions: List[Point]
    destToHomeInstructions: List[Point]
    