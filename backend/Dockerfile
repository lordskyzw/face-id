FROM python:3.11

RUN apt-get update && apt-get install -y libgl1-mesa-glx

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["python", "app.py", "--host=0.0.0.0", "--port=5000"]
