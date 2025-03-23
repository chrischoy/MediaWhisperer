# MediaWhisperer API

## Setup

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment:

```bash
# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r ../../requirements.txt
```

4. Create uploads directory:

```bash
mkdir -p uploads/temp/pdf
```

5. Run the server:

```bash
python main.py
```

The API will be available at http://localhost:8000

## Development

- API documentation is available at http://localhost:8000/docs
- The OpenAPI schema is available at http://localhost:8000/openapi.json
