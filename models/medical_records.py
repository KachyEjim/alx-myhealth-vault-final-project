from datetime import datetime
from base_model import Basemodel
from api import db

class Medical_records(base_model):
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
    Record_Name = db.Column(db.String(200), nullable=False)
    HealthCare_Provider = db.Column(db.String(100), nullable=False)
    Type_of_Record = db.Column(db.String(70), nullable=False)
    Diagnsis = db.Column(db.String(100), nullable=False)
    Notes = db.Column(db.Text, nullable=True)
    last_added = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdated=datetime.utcnow)

    # Refernce the User model
    user = db.relationship('Users', backref=db.backref('edical_records', lazy=True))
    def __repr__(self):
        '''
        Return string Representation of the medical_record instance showing record name and diagnosis
        '''

        return f'<Medical_reord{self.Record_Name} ({self.Diagnosis})>'
    def to_dit():
        '''
        converts the medical_reord instance into a dictionary format
        '''
        return {
                'id': self.id,
                'user_id': self.user_id,
                'Record_Name': self.Record_Name,
                'HealthCare_Provider': self.HealthCare_Provider,
                'Type_of_Record': self.Type_of_Record,
                'Diagnosis': self.Diagnosis,
                'Notes': self.Notes,
                'last_added' self.last_added.isoformat(),
                'last_updated': self.last_updated.isoformat(),
                'created_at': self.created_at.isoformat(),
                'updated_at': self.updated_at.isoformat(),
                }
