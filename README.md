### RUN
```
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
### Run the app
```
uvicorn app.main:app --reload --port 8001

```
### Tests
```
pytest app/tests -q
```