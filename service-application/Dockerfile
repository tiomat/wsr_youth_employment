# start by pulling the python image
FROM python:3.8.0-slim

# copy the requirements file into the image
COPY ./requirements.txt /app/requirements.txt
COPY ./app.py /app/app.py
COPY ./init.py /app/init.py

# switch working directory
WORKDIR /app

# install the dependencies and packages in the requirements file
RUN apt-get update \
    && apt-get install gcc -y \
    && apt-get clean

RUN pip install -r requirements.txt
RUN python init.py

# copy every content from the local file to the image
# COPY . /app

# configure the container to run in an executed manner
ENTRYPOINT [ "python"]
CMD ["app.py"]