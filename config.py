import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://user:password@db:5432/forecast')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', 60))
