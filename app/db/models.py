from sqlalchemy import Column, Integer, String, Float, ForeignKey, Date # type: ignore
from sqlalchemy.ext.declarative import declarative_base # type: ignore
from sqlalchemy.orm import relationship # type: ignore
from sqlalchemy_database import Base

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
    

class AcademicStaffData(Base):
    """Model for staff data by faculty and department"""
    __tablename__ = "academic_staff"
    
    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, index=True, nullable=False)  # e.g., '2023/2024'
    faculty = Column(String, index=True, nullable=False)  # e.g., 'Technology'
    department = Column(String, index=True, nullable=False) # e.g., 'Computer Science'
    gender = Column(String, nullable=True)  
    position = Column(String, nullable=True)  # e.g., 'Professor', 'Lecturer', etc.
    count = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<Academic_StaffData(Faculty={self.faculty}, department={self.department}, position={self.position})>"
    


class EnrollmentData(Base):
    """Model for enrollment data by session"""
    __tablename__ = "enrollment_data"
    
    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, index=True, nullable=False)  # e.g., '2023/2024'
    faculty = Column(String, index=True, nullable=False)  # e.g., 'Technology'
    department = Column(String, index=True, nullable=False) # e.g., 'Computer Science'
    level = Column(String, index=True, nullable=False)  # e.g., '1st Year'
    type = Column(String, nullable=True)  # e.g., 'Undergraduate', 'Graduate', etc.
    gender = Column(String, nullable=True)  
    count = Column(Integer, nullable=False)
    
    def __repr__(self):
        return f"<Enrollment_data(Session={self.session}, faculty = {self.faculty}, department={self.department}, position={self.position})>"



class IncomeData(Base):
    """Model for tracking income records"""
    __tablename__ = "income"
    
    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, index=True, nullable=False)  # e.g., '1996/1997'
    source = Column(String, nullable=False)               # e.g., 'N.U.C Grant'
    amount = Column(Float, nullable=False)                 # e.g., 405876729.0
    
    def __repr__(self):
        return f"<IncomeData(session={self.session}, source={self.source}, amount={self.amount:,.2f})>"



class ExpenditureData(Base):
    """Model for tracking expenditure records"""
    __tablename__ = "expenditure"
    
    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, index=True, nullable=False)  # e.g., '1996/1997'
    type = Column(String, nullable=False)                 # e.g., 'Salaries', 'Maintenance'
    amount = Column(Float, nullable=False)                # e.g., 12000000.0
    
    def __repr__(self):
        return f"<ExpenditureData(session={self.session}, type={self.type}, amount={self.amount:,.2f})>"
