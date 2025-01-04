#ALL FILES UPLOADED - CREDITS 🌟 - @Sunrises_24
FROM python:3.10
WORKDIR /app
COPY . /app/
RUN pip install -r requirements.txt
CMD gunicorn app:app & python3 bot.py
