from pydantic import BaseModel

# Pydantic model for spell checking
class InputTerm(BaseModel):
    term: str

class SpellCheckResponse(BaseModel):
    input_term: str
    corrections: list[str]

# Pydantic model for text correction
class TextCorrection(BaseModel):
    text: str

class CorrectedText(BaseModel):
    id: int
    text: str
    corrected_text: str
