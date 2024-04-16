# category.py
from datetime import datetime, date 
from decimal import Decimal
from sqlalchemy import Integer,Column,DateTime,String
from sqlalchemy.dialects.mysql import SET, ENUM, YEAR
from .meta import Base
 
class GeneralCategory(Base):
    __tablename__ = 'general_category'
    id = Column(Integer, primary_key=True, nullable=False,comment='ID') 
    pid = Column(Integer, nullable=False,comment='Parent ID') 
    type = Column(String(30), nullable=False,comment='GeneralCategory Type') 
    name = Column(String(30), nullable=False,comment='Name') 
    image = Column(String(100),comment='Image') 
    keywords = Column(String(255),comment='Keywords') 
    description = Column(String(255),comment='Description') 
    createtime = Column(DateTime,comment='Creation Time') 
    updatetime = Column(DateTime,comment='Update Time') 
    weigh = Column(Integer, nullable=False,comment='Weight') 
    status = Column(ENUM('normal', 'hidden'), nullable=False,comment='Status') 



    @classmethod
    def from_dict(cls, data):
        """
        Creates an instance of GeneralConfig from a dictionary.
        This method explicitly filters out keys that do not correspond to the model's columns.
        """
        
        # List all column names of the model
        valid_keys = {column.name for column in cls.__table__.columns}
        # Filter the dictionary to include only keys that correspond to column names
        filtered_data = {key: value for key, value in data.items() if key in valid_keys}
        return cls(**filtered_data)
    def to_dict(self, fields=None):
        """
        Convert this User instance into a dictionary.

        Args:
        - fields: Optional list of fields to include in the dictionary. If None, includes all fields.

        Returns:
        - A dictionary representation of this User instance.
        """
        # If no specific fields are requested, include all fields.
        if fields is None:
            fields = [column.name for column in self.__table__.columns]
        
        result_dict = {}
        for field in fields:
            value = getattr(self, field, None)
            
            # Convert datetime and date objects to string for JSON compatibility.
            if isinstance(value, (datetime, date)):
                value = value.isoformat()
            # Convert Decimal to string to prevent precision loss during serialization.
            elif isinstance(value, Decimal):
                value = str(value)
            
            result_dict[field] = value
        
        return result_dict
