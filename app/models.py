from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from database.db import Base # type: ignore

class StudentData(Base):
    """Model for student data by Level, faculty and department"""
    __tablename__ = "student"
    
    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, index=True, nullable=False)  # e.g., '2023/2024'
    faculty = Column(String, index=True, nullable=False)  # e.g., 'Technology'
    department = Column(String, index=True, nullable=False) # e.g., 'Computer Science'
    level = Column(String, index=True, nullable=False)  # e.g., '1st Year'
    type = Column(String, nullable=True)  # e.g., 'Undergraduate', 'Graduate', etc.
    gender = Column(String, nullable=True)  # e.g,  M-male, F-female.
    count = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<StudentData(year={self.level}, department={self.department}, count={self.count})>"
    

class Academic_StaffData(Base):
    """Model for staff data by faculty and department"""
    __tablename__ = "Academic_staff"
    
    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, index=True, nullable=False)  # e.g., '2023/2024'
    faculty = Column(String, index=True, nullable=False)  # e.g., 'Technology'
    department = Column(String, index=True, nullable=False) # e.g., 'Computer Science'
    gender = Column(String, nullable=True)  
    position = Column(String, nullable=True)  # e.g., 'Professor', 'Lecturer', etc.
    count = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<Academic_StaffData(Faculty={self.faculty}, department={self.department}, position={self.position})>"
    
