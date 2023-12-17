import time
import requests
import json


class NoOutputFromRunpodException(Exception):
    """Exception raised when there is no output from Runpod."""


def send_async_transcription_request(base64_string, api_key, server_endpoint):
    """
    Sends an asynchronous transcription request to Runpod.

    Args:
        base64_string (str): Base64-encoded audio data.
        api_key (str): Runpod API key.
        server_endpoint (str): Server endpoint.

    Returns:
        str: Job ID of the transcription request.
    """
    url = f"https://api.runpod.ai/v2/{server_endpoint}/run"
    payload = json.dumps({"input": {"audio_base_64": base64_string}})
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


def transcribe_audio(base64_string, runpod_api_key, server_endpoint, polling_interval=20):
    """
    Transcribes audio using Runpod's API.

    Args:
        base64_string (str): Base64-encoded audio data.
        api_key (str): Runpod API key.
        server_endpoint (str): Server endpoint.

    Returns:
        dict: Transcription output or status.
    """
    job_id = send_async_transcription_request(base64_string, runpod_api_key, server_endpoint)
    return wait_for_transcription_completion(job_id, runpod_api_key, server_endpoint, polling_interval)

