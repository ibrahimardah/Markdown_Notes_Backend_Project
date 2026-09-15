from fastapi import FastAPI
from controllers.auth_controller import router as auth_router
from controllers.user_controller import router as user_router
from controllers.note_controller import router as note_router
from controllers.folder_controller import router as folder_router
from controllers.tag_controller import router as tag_router
from controllers.revision_grammar_controller import router as rev_gram_router

app = FastAPI()

app.include_router(auth_router) # Authentication Routes
app.include_router(user_router) # User Routes
app.include_router(note_router) # Notes Routes (+ attach/detach tags + render)
app.include_router(folder_router) # Folder Routes
app.include_router(tag_router) # Tag Routes
app.include_router(rev_gram_router) # Revisions and Grammar Routes

# Home Route
@app.get("/")
def root():
    return {"message": "This is Home Route!"}