# addon.py
from datetime import datetime, date 
from decimal import Decimal
from sqlalchemy import String,Numeric,Text,SmallInteger,Column,Integer,DateTime
from sqlalchemy.dialects.mysql import SET, ENUM, YEAR
from sqlalchemy.sql.expression import ClauseElement
from zhanor_admin.common.json import JSONEncodedDict
from zhanor_admin.models.meta import Base
 
class Addon(Base):
    __tablename__ = 'addon'
    id = Column(Integer, primary_key=True, nullable=False,comment='Id') 
    title = Column(String(255), nullable=False,comment='Title') 
    author = Column(String(80), nullable=False,comment='Author') 
    uuid = Column(String(120), nullable=False,comment='Uuid') 
    description = Column(String(255), nullable=False,comment='Description') 
    version = Column(String(50), nullable=False,comment='Version') 
    downloads = Column(Integer, nullable=False,comment='Downloads') 
    download_url = Column(String(255), nullable=False,comment='Download_Url') 
    md5_hash = Column(String(32), nullable=False,comment='Md5_Hash') 
    price = Column(Numeric,comment='Price') 
    paid = Column(SmallInteger, nullable=False,comment='Paid') 
    installed = Column(SmallInteger, nullable=False,comment='Installed') 
    enabled = Column(SmallInteger, nullable=False,comment='Enabled') 
    setting_menu = Column(JSONEncodedDict, nullable=True, comment='Setting_Menu')
    createtime = Column(DateTime, nullable=False,comment='Createtime') 
    updatetime = Column(DateTime, nullable=False,comment='Updatetime') 



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
    
    def initialize_special_fields(self):
        for field_name, field in self.__mapper__.columns.items():
            if isinstance(field.type, (ENUM, SET)):
                options_method = getattr(self, f"{field_name}_property".upper(), None)
                if options_method and hasattr(options_method(), 'members'):
                    setattr(self, field_name, field.type.members)
                elif isinstance(field.type, ENUM):
                    if isinstance(field.default, ClauseElement):
                        pass
                    else:
                        if field.default is not None and hasattr(field.default, 'arg'):
                            setattr(self, field_name, field.default.arg if field.default.arg != 'None' else '')
                elif isinstance(field.type, SET): 
                    setattr(self, field_name, frozenset())

            elif field.default is not None: 
                if isinstance(field.default, ClauseElement):
                    pass
                else:
                    if field.default is not None and hasattr(field.default, 'arg'):
                            setattr(self, field_name, field.default.arg if field.default.arg != 'None' else '')
            else:
                setattr(self, field_name,'')
