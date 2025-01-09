from flask import Flask, request, Response, stream_with_context
from flask_cors import CORS
from openai import OpenAI
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/chat": {"origins": "*"}})

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def stream_openai_response(query):
    try:
        stream = client.chat.completions.create(
            model="gpt-4o-mini",  # Using gpt-3.5-turbo for faster responses
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": query}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=1000
        )

        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield f"data: {json.dumps({'content': chunk.choices[0].delta.content})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    # Handle preflight request
    if request.method == 'OPTIONS':
        response = app.make_default_options_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    if not request.is_json:
        return {"error": "Content-Type must be application/json"}, 415

    data = request.get_json()
    query = data.get('query')

    if not query:
        return {"error": "Query parameter is required"}, 400

    response = Response(
        stream_with_context(stream_openai_response(query)),
        content_type='text/event-stream'
    )
    
    # Add required headers
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['X-Accel-Buffering'] = 'no'
    
    return response

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)