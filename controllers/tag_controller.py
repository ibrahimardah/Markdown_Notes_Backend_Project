from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from auth.auth import get_current_user
from db.database import get_db
from schemas.tag_schema import TagCreate, TagUpdate, TagResponse
from models import Tag, Note, User, NoteTag

# Tags Router
router = APIRouter(prefix="/tags", tags=["Tags"])

# Create Tag Endpoint
@router.post("",response_model=TagResponse,status_code=status.HTTP_201_CREATED)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Tag name must be unique for this user
    existing_tag = (db.query(Tag).filter(
        Tag.owner_id == current_user.id,
        Tag.name == tag_data.name).first()
    )
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag already exists"
        )
    # Creating the new tag    
    new_tag = Tag(owner_id=current_user.id, name=tag_data.name)
    db.add(new_tag)
    db.commit()
    db.refresh(new_tag)
    return new_tag

# Get Tags Endpoint
@router.get("", response_model=list[TagResponse])
def get_tags(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # get all tags owned by this user
    tags = (db.query(Tag).filter(Tag.owner_id == current_user.id).all())
    return tags

# Get specific Tag Endpoint
@router.get("/{tag_id}", response_model=TagResponse)
def get_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tag = (db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.owner_id == current_user.id).first()
    )
    # If there is no tag or not owned by this user
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    return tag

# Update Tag Endpoint
@router.patch("/{tag_id}", response_model=TagResponse)
def update_tag(
    tag_id: int,
    tag_data: TagUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tag = (db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.owner_id == current_user.id).first()
    )
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )

    # Make sure this user doesn't already have another tag with this name
    existing_tag = (db.query(Tag).filter(
        Tag.owner_id == current_user.id,
        Tag.name == tag_data.name,
        Tag.id != tag.id).first()
    )
    # if it has, raise an error (unique tag per user)
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag already exists"
        )
    tag.name = tag_data.name
    db.commit()
    db.refresh(tag)
    return tag

# Delete Tag Endpoint
@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    tag = (db.query(Tag).filter(
        Tag.id == tag_id,
        Tag.owner_id == current_user.id).first()
    )
    if tag is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found"
        )
    # Remove note-tag connections first
    db.query(NoteTag).filter(NoteTag.tag_id == tag.id).delete()
    # delete tag
    db.delete(tag)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)