from aware.server.celery_app import app


@app.task(name="assistant.assistant_response")
def assistant_response(user_message):
    # 1. Get user context from Redis (or load from Supabase if not in Redis)
    # 2. Get thought context from Redis
    # 3. Get user requests from Redis
    # 4. Format prompt based on the above data
    # 5. Send prompt to OpenAI and handle response asynchronously
