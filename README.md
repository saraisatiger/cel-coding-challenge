To build and start the application, run the following from the project root directory:
```commandline
docker compose up --build
```

Assumptions:
- Highest and lowest temperature forecasts are filtered by requested latitude, longitude, date, and hour of day in UTC
- Temperature responses returned from Weather.gov are Integer values
- Weather.gov experimental headers are not used
- Proper project structure is not used
- Error handling is not robust