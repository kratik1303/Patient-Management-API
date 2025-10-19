from fastapi import FastAPI,Path,HTTPException,Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, computed_field
from typing import Optional, Literal, Annotated
import json
app = FastAPI()

class Patient(BaseModel):
    id:Annotated[str, Field(...,description='ID of the patient',examples=['POOX'])]
    name:Annotated[str,Field(..., description='Name of the patient')]
    city:Annotated[str,Field(...,description='City where the patient is living')]
    age:Annotated[int,Field(...,gt=0,lt=105,description='Age of the patient')]
    gender:Annotated[Literal['male','female'],Field(...,description='gender of patient')]
    height:Annotated[float,Field(...,gt=0,description='Height of patient in ms')]
    weight:Annotated[float,Field(...,gt=0,description='Weight of patient in kgs')]

    @computed_field
    @property
    def bmi(self) -> float:
        bmi = round(self.weight/(self.height**2),2)
        return bmi
    
    
    @computed_field
    @property
    def verdict(self) -> float:
        if self.bmi < 18.5:
            return 'Underweight'
        elif self.bmi<30:
            return 'Normal'
        else:
            return 'Obese'

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)] 


def load_data():
    with open ('patients.json','r') as f:
        data = json.load(f)
    
    return data

def save_data(data):
    with open('patients.json','w') as f:
        json.dump(data,f)

@app.get('/')
def hello():
    return{'message':'Making a patient management system'}


@app.get('/about')
def aboutme():
    return {'Keeping records of patient'}

@app.get('/view')
def view():
    data = load_data()

    return data

@app.get('/patients/{patient_id}')
def view_patient(patient_id:str=Path(description='Enter a Patient id',example='P00X type')):
    data =load_data()

    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404,detail='Patient not found')

@app.get('/sort')
def sort_patients(sort_by: str = Query(...,description='Sort on the basis of height,weight or bmi'), order: str = Query('asc',description='can be ascending or descending order')):
    valid_fields=['height','weight','bmi']

    if sort_by not in valid_fields:
        raise HTTPException(status_code=400,detail=f'Invalid field select from {valid_fields}')
    
    if order not in ['asc','desc']:
        raise HTTPException(status_code=400,detail='Invalid order select between asc or desc')
    
    data = load_data()

    sort_order = True if order == 'desc' else False

    sorted_data = sorted(data.values(),key=lambda x:x.get(sort_by,0), reverse=sort_order)

    return sorted_data

   
@app.post('/create')
def create_patient(patient: Patient):

    #load existing data
    data = load_data()

    #check if patient already exists
    if patient.id in data:
        raise HTTPException(status_code=400,detail='Patient already exists')
    
    #new patient add
    data[patient.id]=patient.model_dump(exclude=['id']) #converts obj into dictionary

    #save data into Db
    save_data(data)

    return JSONResponse(status_code=201,content={'message':'patient created successfully'})

@app.delete('/delete/{patient_id}')
def delete_patient(patient_id:str):
    data = load_data()

    if patient_id not in data :
        raise HTTPException(status_code=400, detail='Patient not found')
    
    del data[patient_id]
    save_data(data)

    return JSONResponse(status_code=200,content={'message':'Patient dlt'})
        

@app.put('/edit/{patient_id}')
def update_patient(patient_id:str, patient_update:PatientUpdate):

    data = load_data()

    if patient_id not in data:
        raise HTTPException(status_code=404, detail='Patient not found')
    
    existing_patient_info = data[patient_id]

    updated_patient_info =patient_update.model_dump(exclude_unset=True)

    for key,value in updated_patient_info.items():
        existing_patient_info[key]=value

    #existing_patient ->pydantic obj ->update bmi + verdict
    existing_patient_info['id']=patient_id
    pydantic_patient_obj = Patient(**existing_patient_info)

    #pydantic obj into dict
    existing_patient_info = pydantic_patient_obj.model_dump(exclude='id')

    data[patient_id]=existing_patient_info

    save_data(data)

    return JSONResponse(status_code=200,content={'msg':'updated'})