from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.organization import Department
from app.schemas.organization import DepartmentResponse, DepartmentCreate, DepartmentUpdate

router = APIRouter()

@router.get("/", response_model=List[DepartmentResponse])
@router.get("/departments", response_model=List[DepartmentResponse])
def get_departments(db: Session = Depends(get_db)):
    """Retrieves all configurable active departments stored in PostgreSQL."""
    return db.query(Department).filter(Department.is_active == True).all()

@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department_by_id(department_id: int, db: Session = Depends(get_db)):
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept

@router.post("/", response_model=DepartmentResponse)
@router.post("/departments", response_model=DepartmentResponse)
def create_department(dept_in: DepartmentCreate, db: Session = Depends(get_db)):
    """Creates a new configurable department stored in PostgreSQL."""
    existing = db.query(Department).filter(Department.name == dept_in.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Department already exists")
    dept = Department(**dept_in.dict())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    return dept

@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(department_id: int, dept_in: DepartmentUpdate, db: Session = Depends(get_db)):
    """Updates dynamic configuration (keywords, SLA hours, lead name) for a department."""
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    update_data = dept_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(dept, field, value)

    db.commit()
    db.refresh(dept)
    return dept

@router.delete("/{department_id}")
def deactivate_department(department_id: int, db: Session = Depends(get_db)):
    """Soft-deletes or deactivates a department from active routing."""
    dept = db.query(Department).filter(Department.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    dept.is_active = False
    db.commit()
    return {"message": f"Department {dept.name} deactivated successfully."}
