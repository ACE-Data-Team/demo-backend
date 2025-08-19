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
    

class Academic_StaffData(Base):
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
    


class Enrollment_Data(Base):
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
        return f"<Enrollmeant_data(Session={self.session}, faculty = {self.faculty}, department={self.department}, position={self.position})>"


class Head_Count_Student_Data(Base):
    """Model for head count data by session"""
    __tablename__ = "head_count_student_data"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(String, index=True, nullable=False)  # e.g., '2023/2024'
    faculty = Column(String, index=True, nullable=False)  # e.g., 'Technology
    attribute  = Column(String, index=True, nullable=False)  # e.g., 'Total Students', 'Total Staff'
    count = Column(Integer, nullable=False) # change the value colum to count

    def __repr__(self):
        return f"<Head_Count_data(year={self.year}, faculty={self.faculty}, attribute={self.attribute}, count={self.count})>"
    

class Income_Data(Base):
    """Model for income data by session"""
    __tablename__ = "income_data"
    
    id = Column(Integer, primary_key=True, index=True)
    session = Column(String, index=True, nullable=False)  # e.g., '2023/2024'
    source = Column(String, index=True, nullable=False)  # e.g., 'Tuition Fees', 'Grants'
    amount = Column(Float, nullable=False)  # e.g., 100000.0
    def __repr__(self):
        return f"<Income_data(session={self.session}, source={self.source}, amount={self.amount})>"
    
class New_Entrants_Data(Base):
    """Model for new entrants data by state, faculty and gender"""
    __tablename__ = "new_entrants_data"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(String, index=True, nullable=False)  # e.g., '2023/2024'
    faculty = Column(String, index=True, nullable=False)  # e.g., 'Technology'
    state = Column(String, index=True, nullable=False)  # e.g., ' Lagos'
    gender = Column(String, nullable=True)

    def __repr__(self):
        return f"<New_Entrants_data(year={self.year}, faculty={self.faculty}, state={self.state})>"

class New_Entrants_Postgraduate_Data(Base):
    """Model for new entrants data by state, faculty and gender"""
    __tablename__ = "new_entrants_postgraduate_data"
    
    id = Column(Integer, primary_key=True, index=True)
    year = Column(String, index=True, nullable=False)  # e.g., '2023/2024'
    faculty = Column(String, index=True, nullable=False)  # e.g., 'Technology'
    state = Column(String, index=True, nullable=False)  # e.g., ' Lagos'
    gender = Column(String, nullable=True)

    def __repr__(self):
        return f"<New_Entrants_data(year={self.year}, faculty={self.faculty}, state={self.state})>"
 