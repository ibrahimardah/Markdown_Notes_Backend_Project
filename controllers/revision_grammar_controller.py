import os
from datetime import datetime
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
from auth.auth import get_current_user
from models.user import User
from models.note import Note
from models.revision import Revision
from models.grammar_issue import GrammarIssue
from schemas.note_schema import NoteResponse
from schemas.revision_schema import RevisionResponse
from schemas.grammar_issue_schema import GrammarIssueResponse

router = APIRouter(prefix="/notes", tags=["Revisions and Grammar Issues"])

# List Note Revisions Endpoint
@router.get("/{note_id}/revisions", response_model=list[RevisionResponse])
def get_revisions(
    note_id: int,
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
    revisions = (db.query(Revision)
        .filter(Revision.note_id == note.id)
        .order_by(Revision.revision_number.desc()).all()
    )
    return revisions

# Get Specific Revision Endpoint
@router.get("/{note_id}/revisions/{rev_id}", response_model=RevisionResponse)
def get_revision(
    note_id: int,
    rev_id: int,
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
    revision = (db.query(Revision).filter(
        Revision.id == rev_id,
        Revision.note_id == note.id).first()
    )
    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision not found"
        )
    return revision

# Restore Revision Endpoint
@router.post(
    "/{note_id}/revisions/{rev_id}/restore",
    response_model=NoteResponse
)
def restore_revision(
    note_id: int,
    rev_id: int,
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
    revision = (db.query(Revision).filter(
        Revision.id == rev_id,
        Revision.note_id == note.id).first()
    )
    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision not found"
        )
        
    # Check if the selected revision is already the current note
    if (note.title == revision.title and 
        note.body_markdown == revision.body_markdown):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This revision is already the current version"
        )    
        
    # Restore snapshot into current note
    note.title = revision.title
    note.body_markdown = revision.body_markdown
    note.updated_at = datetime.now()
    # Find latest revision
    latest_revision = (
        db.query(Revision)
        .filter(Revision.note_id == note.id)
        .order_by(Revision.revision_number.desc()).first()
    )
    next_revision_number = latest_revision.revision_number + 1
    # Append new revision representing the restore
    restored_revision = Revision(
        note_id=note.id,
        revision_number=next_revision_number,
        title=revision.title,
        body_markdown=revision.body_markdown,
        created_by=current_user.id
    )
    db.add(restored_revision)
    db.commit()
    db.refresh(note)
    return note

LANGUAGETOOL_URL = os.getenv("LANGUAGETOOL_URL")

# Check Grammar Issue Endpoint
@router.post(
    "/{note_id}/revisions/{revision_id}/grammar-check",
    response_model=list[GrammarIssueResponse],
    status_code=status.HTTP_200_OK
)
def check_revision_grammar(
    note_id: int,
    revision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # making sure the note belongs to the current user and is found
    note = (db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id).first()
    )
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
        
    # same for revision as note above
    revision = (db.query(Revision).filter(
        Revision.id == revision_id,
        Revision.note_id == note.id).first()
    )
    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision not found"
        )
    try:
        response = httpx.post(
            LANGUAGETOOL_URL,
            data={
                "text": revision.body_markdown,
                "language": "en-US"
            },
            timeout=10.0
        )
        response.raise_for_status()
        
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LanguageTool request timed out"
        )
    except httpx.HTTPError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="LanguageTool request failed"
        )
    language_tool_result = response.json()
    # Remove issues from an earlier check of the same revision
    db.query(GrammarIssue).filter(GrammarIssue.revision_id == revision.id).delete()
    stored_issues = []
    for match in language_tool_result.get("matches", []):
        suggestions = [replacement["value"] 
                       for replacement in match.get("replacements", [])]
        rule = match.get("rule", {})
        grammar_issue = GrammarIssue(
            revision_id=revision.id,
            offset=match["offset"],
            length=match["length"],
            message=match["message"],
            rule_id=rule.get("id"),
            suggestions=suggestions
        )
        db.add(grammar_issue)
        stored_issues.append(grammar_issue)
    db.commit()
    for issue in stored_issues:
        db.refresh(issue)
    return stored_issues

# Get Grammar Issues Endpoint
@router.get(
    "/{note_id}/revisions/{revision_id}/grammar-issues",
    response_model=list[GrammarIssueResponse]
)
def get_grammar_issues(
    note_id: int,
    revision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    note = (db.query(Note).filter(
        Note.id == note_id,
        Note.owner_id == current_user.id).first()
    )
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )

    revision = (db.query(Revision).filter(
        Revision.id == revision_id,
        Revision.note_id == note.id).first()
    )
    if revision is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Revision not found"
        )
    # get all issues for a specific revision    
    issues = (db.query(GrammarIssue).filter(
        GrammarIssue.revision_id == revision.id).all()
    )
    return issues