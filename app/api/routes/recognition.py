import base64
import numpy as np
import cv2
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db, Person, Attendance
from app.schemas.schemas import (
    PersonCreate, PersonResponse, AddPersonRequest, AddPersonResponse,
    CheckinRequest, CheckinResponse, AttendanceResponse
)
from app.core.auth import get_current_active_user, get_current_admin_user
from app.services.face_service import face_service
from app.services.cache import cache

router = APIRouter(prefix="/api/recognition", tags=["Face Recognition"])

def decode_base64_image(base64_string: str) -> np.ndarray:
    """Decode base64 string to image array"""
    try:
        # Remove data URL prefix if present
        if ',' in base64_string:
            base64_string = base64_string.split(',', 1)[1]
        
        img_bytes = base64.b64decode(base64_string)
        npimg = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
        
        if img_bgr is None:
            raise ValueError("Failed to decode image")
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        return img_rgb
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image format: {str(e)}"
        )

def load_embeddings_from_db(db: Session):
    """Load all embeddings from database or cache"""
    # Try cache first
    cached_embeddings = cache.get_embeddings()
    cached_names = cache.get_person_names()
    
    if cached_embeddings and cached_names:
        ids = list(cached_embeddings.keys())
        names = [cached_names[pid] for pid in ids]
        embeddings = [cached_embeddings[pid] for pid in ids]
        return ids, names, embeddings
    
    # Load from database
    people = db.query(Person).all()
    
    ids = []
    names = []
    embeddings = []
    
    embeddings_dict = {}
    names_dict = {}
    
    for person in people:
        if person.embedding:
            ids.append(person.id)
            names.append(person.name)
            emb = np.array(person.embedding, dtype=np.float32)
            embeddings.append(emb)
            embeddings_dict[person.id] = emb
            names_dict[person.id] = person.name
    
    # Cache the results
    if embeddings_dict:
        cache.set_embeddings(embeddings_dict)
        cache.set_person_names(names_dict)
    
    return ids, names, embeddings

@router.post("/add-person", response_model=AddPersonResponse)
async def add_person(
    request: AddPersonRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """
    Add a new person to the database with face embeddings
    Requires admin privileges
    """
    # Check if person already exists
    existing = db.query(Person).filter(Person.name == request.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Person '{request.name}' already exists"
        )
    
    # Process frames and extract embeddings
    embeddings = []
    
    for idx, frame_data in enumerate(request.frames):
        try:
            img = decode_base64_image(frame_data)
            embedding = face_service.process_image(img)
            
            if embedding is not None:
                embeddings.append(embedding)
            else:
                print(f"No face detected in frame {idx + 1}")
        except Exception as e:
            print(f"Error processing frame {idx + 1}: {e}")
            continue
    
    if len(embeddings) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No faces detected in any frame. Please ensure clear face visibility."
        )
    
    # Average the embeddings
    avg_embedding = np.mean(embeddings, axis=0).tolist()
    
    # Create new person
    new_person = Person(name=request.name, embedding=avg_embedding)
    db.add(new_person)
    db.commit()
    db.refresh(new_person)
    
    # Invalidate cache
    cache.invalidate_embeddings()
    cache.invalidate_person_names()
    
    return AddPersonResponse(
        success=True,
        message=f"Successfully added '{request.name}' with {len(embeddings)} face samples",
        person_id=new_person.id
    )

@router.post("/checkin", response_model=CheckinResponse)
async def checkin(
    request: CheckinRequest,
    db: Session = Depends(get_db)
):
    """
    Perform face recognition and check-in
    Public endpoint - no authentication required
    """
    try:
        # Decode image
        img = decode_base64_image(request.image)
        
        # Extract face embedding
        embedding = face_service.process_image(img)
        
        if embedding is None:
            return CheckinResponse(
                success=False,
                message="No face detected. Please ensure good lighting and clear face visibility."
            )
        
        # Load database embeddings
        ids, names, db_embeddings = load_embeddings_from_db(db)
        
        if not db_embeddings:
            return CheckinResponse(
                success=False,
                message="No registered faces in database. Please register first."
            )
        
        # Find best match
        best_idx, best_score = face_service.find_best_match(embedding, db_embeddings)
        
        if best_idx is None:
            return CheckinResponse(
                success=False,
                message=f"No match found (best score: {best_score:.2f}). Please register first.",
                confidence=best_score
            )
        
        # Record attendance
        person_id = ids[best_idx]
        person_name = names[best_idx]
        
        attendance = Attendance(
            person_id=person_id,
            confidence_score=best_score
        )
        db.add(attendance)
        db.commit()
        
        return CheckinResponse(
            success=True,
            message=f"✓ Checked in: {person_name}",
            person_name=person_name,
            confidence=best_score
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing error: {str(e)}"
        )

@router.get("/people", response_model=List[PersonResponse])
async def get_people(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get all registered people"""
    people = db.query(Person).all()
    return people

@router.delete("/people/{person_id}")
async def delete_person(
    person_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin_user)
):
    """Delete a person (admin only)"""
    person = db.query(Person).filter(Person.id == person_id).first()
    
    if not person:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Person not found"
        )
    
    db.delete(person)
    db.commit()
    
    # Invalidate cache
    cache.invalidate_embeddings()
    cache.invalidate_person_names()
    
    return {"message": f"Successfully deleted {person.name}"}

@router.get("/attendance", response_model=List[AttendanceResponse])
async def get_attendance(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get recent attendance records"""
    records = (
        db.query(Attendance)
        .order_by(desc(Attendance.timestamp))
        .limit(limit)
        .all()
    )
    
    return [
        AttendanceResponse(
            id=record.id,
            person_id=record.person_id,
            person_name=record.person.name,
            timestamp=record.timestamp,
            confidence_score=record.confidence_score
        )
        for record in records
    ]
