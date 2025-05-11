FROM python:3.13-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBUG=True

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt --no-cache-dir

EXPOSE 8000

ENTRYPOINT ["sh"]

CMD ["bin/entrypoint.sh"]
