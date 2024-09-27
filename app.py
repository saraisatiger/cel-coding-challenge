import threading

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import requests
from config import Config
from datetime import datetime, timedelta

# load app with configs
app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

# create forecast table
class ForecastRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    hour_of_day_utc = db.Column(db.Integer, nullable=False)
    temperature = db.Column(db.Integer, nullable=False)

# create database & table
with app.app_context():
    db.create_all()

# call weather.gov apis
def get_forecast_for_location(latitude, longitude):
    points_api_url = f"https://api.weather.gov/points/{latitude},{longitude}"

    try:
        location_response = requests.get(points_api_url)

        # parse initial location response if successful
        if location_response.status_code == 200:
            data = location_response.json()
            hourly_forecast_url = data.get('forecastHourly')
            print("Location data received from weather.gov:", data)

            # fetch hourly forecast response
            forecast_response = requests.get(hourly_forecast_url)
            if forecast_response.status_code == 200:
                print("Forecast data received from weather.gov:", data)

                # parse hourly forecast response
                data = forecast_response.json()
                periods = data.get('periods')

                for period in periods:
                    temperature = period.get('temperature')
                    date_time_string = period.get('startTime')

                    if temperature is not None and date_time_string is not None:
                        # parse date and hour of day from date time string
                        date_time_obj = datetime.fromisoformat(date_time_string)
                        date = date_time_obj.date()  # parse date
                        hour_of_day_utc = date_time_obj.hour  # parse hour of day

                        # create and save forecast record to db
                        new_record = ForecastRecord(
                            latitude=float(latitude),
                            longitude=float(longitude),
                            date=date,
                            hour_of_day_utc=hour_of_day_utc,
                            temperature=temperature
                        )

                        db.session.add(new_record)
                    else:
                        print("Unexpected data format:", data)

                # commit after all records have been added
                db.session.commit()

            else:
                print("Failed to retrieve forecast data from weather.gov:", forecast_response.status_code)

        else:
            print("Failed to retrieve location data from weather.gov:", location_response.status_code)
    except Exception as e:
        print("Error calling weather.gov:", str(e))

# initialize last call timestamp
last_api_call = datetime.min

@app.route('/poll-for-forecast', methods=['POST'])
def get_polled_forecast():
    # parse request body
    data = request.get_json()
    location = data.get('location', {})
    latitude = location.get('latitude')
    longitude = location.get('longitude')

    # validate request parameters
    if location is None or latitude is None or longitude is None:
        return jsonify({"error": "All parameters (location, latitude, longitude) are required."}), 400

    global last_api_call
    current_time = datetime.now()

    # hack: check if enough time has passed since the last method call
    if current_time - last_api_call >= timedelta(minutes=Config.POLLING_INTERVAL):
        last_api_call = current_time  # update the last call timestamp
        # poll for forecast for requested location
        threading.Thread(target=get_forecast_for_location(latitude, longitude)).start()
        return

    return

@app.route('/forecast', methods=['GET'])
def get_forecast():
    # parse request body
    data = request.get_json()
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    date = data.get('date')
    hour_of_day_utc = data.get('hour_of_day_utc')

    # validate request parameters
    if latitude is None or longitude is None or date is None or hour_of_day_utc is None:
        return jsonify({"error": "All parameters (latitude, longitude, date, hour_of_day_utc) are required."}), 400

    # fetch the highest and lowest temperatures based on the request
    highest_temp = db.session.query(db.func.max(ForecastRecord.temperature)).filter_by(
        latitude=float(latitude),
        longitude=float(longitude),
        date=date,
        hour_of_day_utc=int(hour_of_day_utc)
    ).scalar()

    lowest_temp = db.session.query(db.func.min(ForecastRecord.temperature)).filter_by(
        latitude=float(latitude),
        longitude=float(longitude),
        date=date,
        hour_of_day_utc=int(hour_of_day_utc)
    ).scalar()

    return jsonify({
        'highest_temperature': highest_temp,
        'lowest_temperature': lowest_temp
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
