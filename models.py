from pydantic import BaseModel

class FreqPair(BaseModel):
    min_freq: int | None = None
    max_freq: int | None = None

class GPUFreqs(BaseModel):
    CoreFreq: FreqPair | None = None
    MemFreq: FreqPair | None = None