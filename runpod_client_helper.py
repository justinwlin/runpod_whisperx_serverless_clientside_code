import time
import requests
import json
import ffmpeg
import os
import base64
import tempfile


class NoOutputFromRunpodException(Exception):
    """Exception raised when there is no output from Runpod."""


def check_health(api_key, server_endpoint):
    """
    Checks health and worker statistics of a particular endpoint.

    Args:
        api_key (str): Runpod API key.
        server_endpoint (str): Server endpoint.

    Returns:
        dict: Health statistics response from Runpod.
    """
    url = f"https://api.runpod.ai/v2/{server_endpoint}/health"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.get(url, headers=headers).json()
    return response


def cancel_job(job_id, api_key, server_endpoint):
    """
    Cancels a transcription job given its job ID.

    Args:
        job_id (str): Job ID of the transcription request to cancel.
        api_key (str): Runpod API key.
        server_endpoint (str): Server endpoint.

    Returns:
        dict: Cancellation response from Runpod.
    """
    url = f"https://api.runpod.ai/v2/{server_endpoint}/cancel/{job_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.post(url, headers=headers).json()
    return response


def send_async_transcription_request(
    base64_string_or_url, api_key, server_endpoint, execution_timeout=600000
):
    """
    Sends an asynchronous transcription request to Runpod.

    Args:
        base64_string_or_url (str): Base64-encoded audio data or a URL that starts with "http".
        api_key (str): Runpod API key.
        server_endpoint (str): Server endpoint.
        execution_timeout (int): Execution timeout in milliseconds, default is 600,000 (10 minutes).

    Returns:
        str: Job ID of the transcription request.
    """
    url = f"https://api.runpod.ai/v2/{server_endpoint}/run"

    payload_base64 = {"audio_base_64": base64_string_or_url}
    payload_url = {"audio_url": base64_string_or_url}

    policy = {"executionTimeout": execution_timeout}

    if base64_string_or_url.startswith("http"):
        payload = json.dumps({"input": payload_url, "policy": policy})
    else:
        payload = json.dumps({"input": payload_base64, "policy": policy})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.post(url, headers=headers, data=payload).json()
    return response["id"]


def get_transcription_status(job_id, api_key, server_endpoint):
    """
    Gets the status of a transcription job from Runpod.

    Args:
        job_id (str): Job ID of the transcription request.
        api_key (str): Runpod API key.
        server_endpoint (str): Server endpoint.

    Returns:
        dict: Status response from Runpod.
    """
    url = f"https://api.runpod.ai/v2/{server_endpoint}/status/{job_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    response = requests.get(url, headers=headers).json()
    return response


def wait_for_transcription_completion(
    job_id, api_key, server_endpoint, polling_interval=20
):
    """
    Waits for the transcription job to complete and returns the output.

    Args:
        job_id (str): Job ID of the transcription request.
        api_key (str): Runpod API key.
        server_endpoint (str): Server endpoint.
        sleep_interval (int, optional): Time in seconds to sleep between status checks. Default is 20 seconds.

    Returns:
        dict: Transcription output or status.
    """
    while True:
        status_response = get_transcription_status(job_id, api_key, server_endpoint)
        status = status_response["status"]

        if status in ["IN_PROGRESS", "IN_QUEUE"]:
            time.sleep(polling_interval)
        else:
            if status == "COMPLETED":
                return {
                    "status": "COMPLETED",
                    "output": status_response.get("output"),
                }
            else:
                raise NoOutputFromRunpodException(
                    f"Transcription job failed with status: {status}"
                )


def transcribe_audio(
    base64_string_or_url, runpod_api_key, server_endpoint, polling_interval=20
):
    """
    Transcribes audio using Runpod's API.

    Args:
        base64_string_or_url (str): Base64-encoded audio data or a URL that starts with "http".
        api_key (str): Runpod API key.
        server_endpoint (str): Server endpoint.

    Returns:
        dict: Transcription output or status.
    """
    job_id = send_async_transcription_request(
        base64_string_or_url, runpod_api_key, server_endpoint
    )
    return wait_for_transcription_completion(
        job_id, runpod_api_key, server_endpoint, polling_interval
    )


def convert_to_mp3_and_base64(input_path):
    """
    Converts an audio or video file to MP3 format with specified settings,
    then encodes the MP3 file to a Base64 string.

    This function takes an input file path, converts the file to a mono MP3
    file with a bitrate of 32k, and encodes this MP3 file to a Base64 string.
    It handles the creation and deletion of temporary files used during the conversion process.

    Args:
    input_path (str): The file path of the input audio or video file.

    Returns:
    str: A Base64 encoded string of the converted MP3 file.

    Raises:
    ffmpeg.Error: If an error occurs during the conversion process.
    """
    try:
        # Create a temporary file for the MP3
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_mp3_file:
            output_mp3_path = temp_mp3_file.name

            # Convert the file to MP3
            (
                ffmpeg.input(input_path)
                .output(output_mp3_path, ac=1, ar="22050", ab="32k", format="mp3")
                .run(overwrite_output=True)
            )
            print(
                f"Conversion to MP3 successful. Temp file created at {output_mp3_path}"
            )

            # Encode the MP3 file directly in Base64
            with open(output_mp3_path, "rb") as mp3_file:
                base64_encoded_data = base64.b64encode(mp3_file.read()).decode("utf-8")

        # Get the size of the Base64 string
        base64_size = len(base64_encoded_data.encode("utf-8")) / (
            1024 * 1024
        )  # size in MB
        print(f"Base64 Encoded Size: {base64_size:.2f} MB")

        # Clean up the temporary MP3 file
        os.remove(output_mp3_path)

        return [base64_encoded_data, base64_size]

    except ffmpeg.Error as e:
        print(f"An error occurred: {e}")
        return None


def decode_base64_to_mp3(base64_data, output_mp3_path):
    """
    Decodes a Base64 encoded string back into an MP3 file.

    This function takes a Base64 encoded string, representing an MP3 file,
    decodes it, and writes the result to a specified output file path. It is
    intended to be used as a reversal of the convert_to_mp3_and_base64 function.

    Args:
    base64_data (str): The Base64 encoded string of the MP3 file.
    output_mp3_path (str): The file path where the decoded MP3 file will be saved.

    Returns:
    None: The function does not return a value but saves the decoded MP3 file at the specified path.

    Raises:
    Exception: If any error occurs during the decoding and file writing process.
    """
    try:
        # Decode the Base64 string
        mp3_data = base64.b64decode(base64_data)

        # Write the decoded data to an MP3 file
        with open(output_mp3_path, "wb") as mp3_file:
            mp3_file.write(mp3_data)

        print(f"MP3 file created at {output_mp3_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


def checkFileSize(input_path):
    """
    Checks the size of an input file and returns the size in MB.
    """

    try:
        # Get the size of the input file
        input_size = os.path.getsize(input_path) / (1024 * 1024)  # size in MB
        print(f"Input File Size: {input_size:.2f} MB")

        # Return in MB to 2 decimal places
        return round(input_size, 2)

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def trim_audio_to_size(input_file: str, target_size_mb: float) -> str:
    """
    Trim the audio file to ensure it's below the specified size in MB.

    Args:
        input_file (str): The path to the input audio file.
        target_size_mb (float): The target file size in MB.

    Returns:
        str: The path to the trimmed audio file.
    """
    # Calculate current file size in MB
    current_size_mb = os.path.getsize(input_file) / (1024 * 1024)

    # If the file is already smaller than the target size, return the original file
    if current_size_mb <= target_size_mb:
        print(f"File size is already within the limit. No trimming needed.")
        return input_file

    # Calculate duration of the audio file
    probe = ffmpeg.probe(input_file)
    duration_seconds = float(probe['streams'][0]['duration'])

    # Calculate target duration based on target size
    target_duration_seconds = (target_size_mb / current_size_mb) * duration_seconds

    # Trim the audio file to the target duration
    output_file = input_file
    (
        ffmpeg
        .input(input_file)
        .output(output_file, t=target_duration_seconds)
        .run(overwrite_output=True)
    )

    print(f"Trimmed audio saved as {output_file}")
    return output_file
