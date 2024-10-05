from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import relationship
from base_model import Basemodel
from api import db

class MedicalRecords(BaseModel):
    '''
    Medical_record inheriting the BaseModel
    
    Attributes:
        Record Name (StringField):the name or tiltle of the medical record.
        User_id (StringField): Foreign key referncing the User
        HealthCare Prvider (StiringField): Name of the Hospital/HalthCare Provider.
        Type of Record (StringField): The type or Category of record e.g(lab report, Prescripton)
        Diagnosis (StringFeild): The nature of patient's illness
        Notes (StringField): Additional Notes about the record
        last_added (DateTimeField): Timestamp when the record was added.
        last_updated (DateTimeField): Timestamp when the record was last updated.
        Action
    '''
    __tablename__ = 'medical_records'

    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    record_name = db.Column(db.String(200), nullable=False)
    healthCare_Provider = db.Column(db.String(100), nullable=False)
    type_of_Record = db.Column(db.String(70), nullable=False)
    diagnsis = db.Column(db.String(100), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    last_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Refernce the User model
    user = db.relationship('Users', backref=db.backref('medical_records', lazy=True))
    def __repr__(self):
        '''
        Return string Representation of the medical_record instance showing record name and diagnosis
        '''

        return f'<Medical_reord{self.record_name} ({self.diagnosis})>'
    def to_dict():
        '''
        converts the medical_reord instance into a dictionary format
        '''
        return {
                'id': self.id,
                'user_id': self.user_id,
                'record_Name': self.Record_Name,
                'healthCare_Provider': self.HealthCare_Provider,
                'type_of_Record': self.Type_of_Record,
                'diagnosis': self.Diagnosis,
                'notes': self.Notes,
                'last_added': self.last_added.isoformat(),
                'last_updated': self.last_updated.isoformat(),
                'created_at': self.created_at.isoformat(),
                'updated_at': self.updated_at.isoformat(),
                }
