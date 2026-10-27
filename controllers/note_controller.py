from fastapi import APIRouter, Depends, status, HTTPException, Response, Query, Header
from fastapi.responses import  HTMLResponse, PlainTextResponse, JSONResponse
from typing import Annotated
from sqlalchemy.orm import Session
from db.database import get_db
from schemas.note_schema import NoteCreate, NoteResponse, NoteFilterParams, NoteUpdate
from auth.auth import get_current_user
from datetime import datetime
from models import Note, User, Revision, Folder, Tag, NoteTag
import hashlib
import nh3
import markdown

# Notes Router
router = APIRouter(prefix="/notes", tags=["Notes"])

# Create Note Endpoint
@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    note_data: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensuring that the folder chosen belongs to this user
    if note_data.folder_id is not None:
        folder = (db.query(Folder).filter(
            Folder.id == note_data.folder_id,
            Folder.owner_id == current_user.id).first()
        )
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
    # Creating the note
    new_note = Note(
        owner_id=current_user.id,
        title=note_data.title,
        body_markdown=note_data.body_markdown,
        folder_id=note_data.folder_id
    )
    db.add(new_note)
    db.flush() # flush to get the id
    # Creating the first revision for this note
    first_revision = Revision(
        note_id=new_note.id,
        revision_number=1,
        title=new_note.title,
        body_markdown=new_note.body_markdown,
        created_by=current_user.id
    )
    db.add(first_revision)
    db.commit()
    db.refresh(new_note)
    return new_note

# List Notes Endpoint
@router.get("", response_model=list[NoteResponse])
def get_notes(
    filters: Annotated[NoteFilterParams, Query()],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Note).filter(
        Note.owner_id == current_user.id,
        Note.deleted_at.is_(None)
    )
    if filters.folder_id is not None:
        query = query.filter(Note.folder_id == filters.folder_id)

    if filters.tag:
        query = (query.join(NoteTag, NoteTag.note_id == Note.id)
            .join(Tag, Tag.id == NoteTag.tag_id)
            .filter(Tag.owner_id == current_user.id, Tag.name == filters.tag)
        )

    if filters.q and filters.q.strip():
        search_term = f"%{filters.q.strip()}%"
        query = query.filter(
            Note.title.ilike(search_term)|Note.body_markdown.ilike(search_term)
        )
    notes = query.offset(filters.offset).limit(filters.limit).all()
    return notes

# List Trash Endpoint
# Same Logic with get notes/
@router.get("/trash", response_model=list[NoteResponse])
def get_trash(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Only retreive deleted notes
    notes = (db.query(Note).filter(
        Note.owner_id == current_user.id,
        Note.deleted_at.is_not(None)).all()
    )
    return notes

# Get Note Endpoint
@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Same logic with list notes endpoint but for a specific note
    note = (db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id,
        Note.deleted_at.is_(None)).first()
    )
    # intentionally hide existence requirement (retreiving note)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    return note

# Soft Delete Endpoint
@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = (db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id).first()
    )
    # intentionally hide existence requirement (deleting note)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    if note.deleted_at is None:
        note.deleted_at = datetime.now()
        db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Restore Note Endpint
@router.post("/{note_id}/restore", response_model=NoteResponse)
def restore_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = (db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id).first()
    )
    # intentionally hide existence requirement (restoring note)
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    if note.deleted_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Note is not deleted"
        )
    # Restore note from trash    
    note.deleted_at = None
    note.updated_at = datetime.now()
    db.commit()
    db.refresh(note)
    return note

# Update Note Endpoint
@router.patch("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note_data: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # fetch non-deleted note with id {note_id} 
    note = (db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id,
        Note.deleted_at.is_(None)).first()
    )
    # note not found exception
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    title_body_changed = False # title or body changed flag
    if note_data.title is not None and note_data.title != note.title:
        note.title = note_data.title
        title_body_changed = True # title changed
    if (note_data.body_markdown is not None 
        and note_data.body_markdown != note.body_markdown):
        note.body_markdown = note_data.body_markdown
        title_body_changed = True # body_markdown changed

    # if folder_id changed
    if "folder_id" in note_data.model_fields_set:
        # Ensuring that the folder chosen belongs to this user
        if note_data.folder_id is not None:
            folder = (db.query(Folder).filter(
                Folder.id == note_data.folder_id,
                Folder.owner_id == current_user.id).first()
            )
            if not folder:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Folder not found"
                )
        note.folder_id = note_data.folder_id
    note.updated_at = datetime.now() # change updated time to now
    # if title or body changed, Create a new revision
    if title_body_changed: 
        latest_revision = (db.query(Revision)
            .filter(Revision.note_id == note.id)
            .order_by(Revision.revision_number.desc()).first()
            )
        next_revision_number = latest_revision.revision_number + 1
        new_revision = Revision(
            note_id=note.id,
            revision_number=next_revision_number,
            title=note.title,
            body_markdown=note.body_markdown,
            created_by=current_user.id
        )
        db.add(new_revision)
    db.commit()
    db.refresh(note)
    return note

# Attach Tag Endpoint
@router.post(
    "/{note_id}/tags/{tag_id}",
    status_code=status.HTTP_201_CREATED
)
def attach_tag(
    note_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Note must belong to current user
    note = (db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id,
        Note.deleted_at.is_(None)).first()
    )
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
        
    # Tag must also belong to current user
    tag = (db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.owner_id == current_user.id).first()
    )
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    existing_connection = (db.query(NoteTag).filter(
        NoteTag.note_id == note_id,
        NoteTag.tag_id == tag_id).first()
    )
    if existing_connection:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag already attached to note"
        )
    note_tag = NoteTag(note_id=note_id,tag_id=tag_id)
    db.add(note_tag)
    db.commit()
    return {"message": "Tag attached successfully"}
    
# Detach Tag Endpoint
@router.delete(
    "/{note_id}/tags/{tag_id}",
    status_code=status.HTTP_204_NO_CONTENT
)
def detach_tag(
    note_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # same as attach endpoint
    note = (db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id,
        Note.deleted_at.is_(None)).first()
    )
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    # same as attach endpoint
    tag = (db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.owner_id == current_user.id).first()
    )
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    note_tag = (db.query(NoteTag).filter(
        NoteTag.note_id == note_id,
        NoteTag.tag_id == tag_id).first()
    )
    # If there are not attach
    if note_tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag is not attached to this note"
        )
    db.delete(note_tag)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

# Render Note Endpoint
@router.get("/{note_id}/render")
def render_note(
    note_id: int,
    if_none_match: Annotated[str | None, Header()] = None,
    accept: Annotated[str | None, Header()] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = (db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id,
        Note.deleted_at.is_(None)).first()
    )
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
        
    # Convert Markdown to HTML
    raw_html = markdown.markdown(note.body_markdown)
    # sanitizing generated HTML
    sanitized_html = nh3.clean(raw_html)
    
    # Generate ETag
    if note.updated_at is not None:
        updated_value = note.updated_at.isoformat()
    else:
        updated_value = ""
    # etag derived from title, body_markdown and updated_at
    # then converted to bytes to be hashed by hashlib
    etag_source = note.title + note.body_markdown + updated_value
    etag_hash = hashlib.sha256(etag_source.encode("utf-8")).hexdigest()
    etag = f'"{etag_hash}"'
    headers = {
            "ETag": etag,
            "Cache-Control": "private, must-revalidate"
        }
    
    # checking If-None-Match
    if if_none_match == etag:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers=headers
        )
    # Default
    # Accept missing or */*
    # santized html rendering
    if (accept is None or accept == "*/*" or "text/html" in accept):
        return HTMLResponse(
            content=sanitized_html,
            status_code=status.HTTP_200_OK,
            headers=headers
        )

    # data remains the same
    # raw markdown
    if "text/markdown" in accept:
        return PlainTextResponse(
            content=note.body_markdown,
            media_type="text/markdown",
            status_code=status.HTTP_200_OK,
            headers=headers
        )

    # json representation
    if "application/json" in accept:
        return JSONResponse(
            content={
                "note_id": note.id,
                "html": sanitized_html,
                "markdown": note.body_markdown,
                "etag": etag
            },
            status_code=status.HTTP_200_OK,
            headers=headers
        )
        
    raise HTTPException(
        status_code=status.HTTP_406_NOT_ACCEPTABLE,
        detail="Unsupported Accept type"
    )