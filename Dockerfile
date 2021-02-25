FROM python:3

WORKDIR /usr/src/app

RUN apt-get update && apt-get install -y poppler-utils && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir pdf2image discord.py requests python-dotenv

ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

COPY files .

CMD [ "python", "-u", "updates.py" ]