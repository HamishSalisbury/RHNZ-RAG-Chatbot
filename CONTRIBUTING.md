## To run Django:

On windows
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
docker build -t rhnz-chatbot .
docker run -p 8000:8000 rhnz-chatbot
```

Or
```
docker compose up
```