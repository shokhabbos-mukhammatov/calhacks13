FROM apify/actor-python:3.13

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# firedrill/ and cards/ are copied in by scripts/sync_actors.py before a push,
# so the Actor ships the same source the tests run against.
COPY . ./

CMD ["python3", "-m", "src"]
