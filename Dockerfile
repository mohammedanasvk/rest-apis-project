FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY . .
CMD ["C:\Program Files\Git\bin\bash","docker-entrypoint.sh"]