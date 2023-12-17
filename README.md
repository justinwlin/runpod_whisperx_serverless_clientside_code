Runpod API Deployment Code:

https://github.com/justinwlin/runpodWhisperx

Clientside helper functions to call Runpod deployed API:

https://github.com/justinwlin/runpod_whisperx_serverless_clientside_code

Helper functions to generate SRT transcriptions:

https://github.com/justinwlin/WhisperXSRTGenerator

## Usage Example
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