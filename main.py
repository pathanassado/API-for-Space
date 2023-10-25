from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from database import Database
from models import SpellCheckResponse, TextCorrection, CorrectedText
from symspellpy import SymSpell, Verbosity
import pkg_resources


app = FastAPI()
db = Database()

# Initialize SymSpell for spell checking
sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)
dictionary_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
sym_spell.load_dictionary("D:\\combination\\frequency_dictionary_en_82_765.txt", term_index=0, count_index=1)

# Spell check and correction endpoint for a single word
@app.get("/spellcheck/", response_model=SpellCheckResponse)
def spell_check(term: str):
    suggestions = sym_spell.lookup(term, Verbosity.CLOSEST, max_edit_distance=2)
    corrected_terms = [suggestion.term for suggestion in suggestions]

    db.add_correction(term, ", ".join(corrected_terms))

    return SpellCheckResponse(input_term=term, corrections=corrected_terms)

def correct_spellings_and_add_space(input_text):
    # Initialize SymSpell
    sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=7)

    # Load a frequency dictionary for English
    dictionary_path = pkg_resources.resource_filename("symspellpy", "frequency_dictionary_en_82_765.txt")
    bigram_path = pkg_resources.resource_filename("symspellpy", "frequency_bigramdictionary_en_243_342.txt")

    # Create a dictionary using the provided frequency dictionary
    sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1)
    sym_spell.load_bigram_dictionary(bigram_path, term_index=0, count_index=2)

    # Split the input text into words
    words = input_text.split()

    # Initialize an empty corrected text
    corrected_text = []

    for word in words:
        # Find suggestions for the word
        suggestions = sym_spell.lookup(word, Verbosity.CLOSEST, max_edit_distance=2)

        if suggestions:
            # If suggestions are found, add the best suggestion to the corrected text
            corrected_text.append(suggestions[0].term)
        else:
            # If no suggestions are found, add the original word
            corrected_text.append(word)

    # Join the corrected words with spaces
    output_text = " ".join(corrected_text)

    return output_text



# Text correction endpoint for a document
@app.post("/corrections/", response_model=CorrectedText)
def create_correction(text_correction: TextCorrection):
    input_text = text_correction.text
    corrected_text = correct_spellings_and_add_space(input_text)

    with db.connection.cursor() as cursor:
        cursor.execute("INSERT INTO text_corrections (input_text, corrected_text) VALUES (%s, %s)",
                       (input_text, corrected_text))
        db.connection.commit()
        cursor.execute("SELECT LAST_INSERT_ID()")
        correction_id = cursor.fetchone()["LAST_INSERT_ID()"]

    return {"id": correction_id, "text": input_text, "corrected_text": corrected_text}

# Define the get_db() function as a FastAPI dependency
def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

# Fetch text correction by ID
@app.get("/corrections/{correction_id}", response_model=CorrectedText)
def read_correction(correction_id: int, db: Database = Depends(get_db)):
    correction = db.get_correction(correction_id)
    if correction is None:
        raise HTTPException(status_code=404, detail="Correction not found")

    return CorrectedText(id=correction_id, text=correction["input_text"], corrected_text=correction["corrected_text"])

# Shutdown event to close the database connection
@app.on_event("shutdown")
def shutdown_event():
    db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
