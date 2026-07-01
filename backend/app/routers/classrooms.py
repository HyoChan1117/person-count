from fastapi import APIRouter, HTTPException, Body
from typing import List
from app.models import Classroom, ClassroomCreate, ClassroomUpdate
from app import storage

router = APIRouter()


@router.get("/", response_model=List[Classroom])
def list_classrooms():
    return storage.get_all()


@router.post("/", response_model=Classroom)
def create_classroom(body: ClassroomCreate):
    return storage.create(body)


@router.get("/{classroom_id}", response_model=Classroom)
def get_classroom(classroom_id: int):
    c = storage.get_one(classroom_id)
    if not c:
        raise HTTPException(404, "Classroom not found")
    return c


@router.put("/{classroom_id}", response_model=Classroom)
def update_classroom(classroom_id: int, body: ClassroomUpdate):
    c = storage.update(classroom_id, body)
    if not c:
        raise HTTPException(404, "Classroom not found")
    return c


@router.delete("/{classroom_id}")
def delete_classroom(classroom_id: int):
    if not storage.delete(classroom_id):
        raise HTTPException(404, "Classroom not found")
    return {"success": True}


@router.put("/{classroom_id}/map-data")
def save_map_data(classroom_id: int, body: dict = Body(...)):
    storage.save_map_data(classroom_id, body)
    return {"success": True}


@router.get("/{classroom_id}/map-data")
def get_map_data(classroom_id: int):
    data = storage.get_map_data(classroom_id)
    if not data:
        raise HTTPException(404, "Map data not found")
    return data
