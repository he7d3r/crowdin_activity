FROM joyzoursky/python-chromedriver:3.9-selenium
WORKDIR /usr/crowdin_activity
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache -r requirements.txt
COPY src/crowdin_activity .
CMD ["python3", "-u", "main.py"]
