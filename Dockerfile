# use Docker-provided Python image
FROM python:3.10-slim

# set the working directory
WORKDIR /app

# copy requirements file to working directory
COPY requirements.txt .

# install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# copy application files to working directory
COPY . .

# expose port for app to run on
EXPOSE 5001

# set run command
CMD ["python", "app.py"]
