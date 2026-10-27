from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from auth.auth import get_current_user
from db.database import get_db
from schemas.folder_schema import FolderCreate, FolderUpdate, FolderResponse
from models import Folder, Note, User

# Folders Router
router = APIRouter(prefix="/folders", tags=["Folders"])

# Create Folder Endpoint
@router.post("",response_model=FolderResponse,status_code=status.HTTP_201_CREATED)
def create_folder(
    folder_data: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # If parent_id is given, parent folder must belong to current user
    if folder_data.parent_id is not None:
        parent_folder = (db.query(Folder).filter(
            Folder.id == folder_data.parent_id,
            Folder.owner_id == current_user.id).first()
        )
        if parent_folder is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found"
            )
    new_folder = Folder(
        owner_id=current_user.id,
        name=folder_data.name,
        parent_id=folder_data.parent_id
    )
    db.add(new_folder)
    db.commit()
    db.refresh(new_folder)
    return new_folder

# Get Folders Endpoint
@router.get("", response_model=list[FolderResponse])
def get_folders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure that folders returned are owned by this user    
    folders=(db.query(Folder).filter(Folder.owner_id==current_user.id).all())
    return folders

# Get Folder Endpoint
@router.get("/{folder_id}", response_model=FolderResponse)
def get_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User=Depends(get_current_user)
):
    folder = (db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id).first()
    )
    # folder is not found (not created or not accessible by this user)
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    return folder     

# Update Folder Endpoint
@router.patch("/{folder_id}", response_model=FolderResponse)
def update_folder(
    folder_id: int,
    folder_data: FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = (db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id).first()
    )
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    # Update name only if user sent it
    if folder_data.name is not None:
        folder.name = folder_data.name
    # Update parent id only if user sent it   
    # If folder chosen doesn't belong to this user, it will raise exception
    # If it belongs, exception will be not execute. id will be accepted
    if "parent_id" in folder_data.model_fields_set:
        # If folder id is sent but not null
        if folder_data.parent_id is not None:
            # Prevent folder from being its own parent
            if folder_data.parent_id == folder.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Folder cannot be its own parent"
                )
            parent_folder = (db.query(Folder).filter(
                Folder.id == folder_data.parent_id, 
                Folder.owner_id == current_user.id).first()
            )
            if parent_folder is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent folder not found"
                )  
        folder.parent_id = folder_data.parent_id
    db.commit()
    db.refresh(folder)
    return folder

# Delete Folder Endpoint
@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    folder = (db.query(Folder).filter(
        Folder.id == folder_id,
        Folder.owner_id == current_user.id).first()
    )
    if folder is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    # rejecting deletion of a non-empty folder (my choice)
    note = (db.query(Note).filter(
        Note.folder_id == folder.id,
        Note.owner_id == current_user.id).first()
    )
    if note is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Folder contains notes"
        )
    # A child folder also references this folder
    child_folder=(db.query(Folder).filter(Folder.parent_id==folder.id).first())
    if child_folder is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Folder contains child folders"
        )
    db.delete(folder)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)