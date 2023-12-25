Runpod API Deployment Code:

https://github.com/justinwlin/runpodWhisperx

Clientside helper functions to call Runpod deployed API:

https://github.com/justinwlin/runpod_whisperx_serverless_clientside_code

Helper functions to generate SRT transcriptions:

https://github.com/justinwlin/WhisperXSRTGenerator

## Usage Example runpod_client_helper.py
``` python
    # Grab the output path sound and encode it to base64 string
    base64AudioString = encodeAudioToBase64("./output.mp3")

    apiResponse = transcribe_audio(
        base64_string=base64AudioString,
        runpod_api_key=RUNPOD_API_KEY,
        server_endpoint=SERVER_ENDPOINT,
        polling_interval=20
    )

    apiResponseOutput = apiResponse["output"]

    srtConverter = SRTConverter(apiResponseOutput["segments"])
    srtConverter.adjust_word_per_segment(words_per_segment=5)
    srtString = srtConverter.to_srt_highlight_word()
    srtConverter.write_to_file("output.srt", srtString)
```

## Usage Example asyncio_runpod_client_helper.py
(ASYNCHRONOUS)
``` python
import asyncio
import aiohttp
from utils.runpod_api_client import RunpodApiClient

async def send_request(client, input_payload, session):
    # Function to send a single request
    return await client.execute_async_api_request(input_payload, session)

async def main():
    # Example API key and endpoint
    api_key = "your_api_key"
    server_endpoint = "your_server_endpoint"

    # Initialize the API client
    client = RunpodApiClient(api_key, server_endpoint)

    # Example payloads for each request
    payloads = [
        {"example_key": "example_value_1"},
        {"example_key": "example_value_2"},
        {"example_key": "example_value_3"},
        {"example_key": "example_value_4"},
        {"example_key": "example_value_5"}
    ]

    # Create and gather tasks
    async with aiohttp.ClientSession() as session:
        tasks = [send_request(client, payload, session) for payload in payloads]
        responses = await asyncio.gather(*tasks)
    
    # Print the responses
    for i, response in enumerate(responses, 1):
        print(f"Response {i}: {response}")

asyncio.run(main())
```

(Synchronous)

```python
from utils.runpod_api_client import RunpodApiClient

# Example API key and endpoint
api_key = "your_api_key"
server_endpoint = "your_server_endpoint"

# Initialize the API client
client = RunpodApiClient(api_key, server_endpoint)

# Example payload
input_payload = {
    "example_key": "example_value"
    # ... other payload data ...
}

# Execute the request synchronously
response = client.execute_sync_api_request(input_payload)
print("Synchronous response:", response)
```

# Notes
runpod_client_helper.py 

Is a direct copy of my code that I run for my whisperx api endpoints. But the asyncio_runpod_client_helper.py is a modified version that is more generalized and can be used for any runpod api endpoint.It also uses asyncio to manage having polling being asynchronous rather than blocking for many requests.

