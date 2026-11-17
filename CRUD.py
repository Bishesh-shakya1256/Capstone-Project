# CRUD.py - UPDATED TO USE LOCAL SQLALCHEMY DATABASE
from app.models import db, Plant, User, Rating, Review

def get_all_plants():
    """Fetches all plants from the local database"""
    plants = Plant.query.all()
    return [plant.to_dict() for plant in plants]

def get_plant_by_id(plant_id):
    """Fetches a single plant by ID"""
    plant = Plant.query.get(plant_id)
    return plant.to_dict() if plant else None

def search_plants(query_string):
    """Basic search by plant name"""
    plants = Plant.query.filter(Plant.plant_name.ilike(f"%{query_string}%")).all()
    return [plant.to_dict() for plant in plants]

# Add any other specific CRUD functions your frontend expects here