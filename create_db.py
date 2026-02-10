from app import app, db
#Script to create the database tables from the models.py file
with app.app_context():
    print("Creating the database tables...")
    db.create_all()
    print("Database tables created.")