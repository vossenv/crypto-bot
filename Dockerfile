

FROM python:3
COPY ./crypto_bot /app/crypto_bot
COPY ./setup.py /app
WORKDIR /app
RUN pip install .

EXPOSE 8033
CMD [ "python", "/app/crypto_bot/app.py" ]