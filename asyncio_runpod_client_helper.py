import asyncio
import aiohttp
import json


class RunpodApiClient:
    def __init__(self, api_key, server_endpoint):
        self.api_key = api_key
        self.server_endpoint = server_endpoint

    class RunpodApiException(Exception):
        """Exception raised when there is an issue with the Runpod API request."""

    async def send_async_api_request(
        self, input_payload, session, execution_timeout=600000
    ):  # 10 minutes in milliseconds
        """Sends an asynchronous request to the specified Runpod API endpoint."""
        url = f"https://api.runpod.ai/v2/{self.server_endpoint}/run"
        payload = {
            "input": input_payload,
            "policy": {"executionTimeout": execution_timeout},
        }
        json_payload = json.dumps(payload)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        async with session.post(url, headers=headers, data=json_payload) as response:
            response_json = await response.json()
            return response_json["id"]

    async def get_api_request_status(self, job_id, session):
        """Gets the status of an API request job."""
        url = f"https://api.runpod.ai/v2/{self.server_endpoint}/status/{job_id}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        async with session.get(url, headers=headers) as response:
            return await response.json()

    async def wait_for_api_request_completion(
        self, job_id, session, polling_interval=20
    ):
        """Waits for the API request job to complete and returns the output."""
        while True:
            status_response = await self.get_api_request_status(job_id, session)
            status = status_response["status"]

            if status in ["IN_PROGRESS", "IN_QUEUE"]:
                await asyncio.sleep(polling_interval)
            else:
                if status == "COMPLETED":
                    return {
                        "status": "COMPLETED",
                        "output": status_response.get("output"),
                    }
                else:
                    raise self.RunpodApiException(
                        f"API request job failed with status: {status}"
                    )

    async def execute_async_api_request(
        self, input_payload, session, polling_interval=20, execution_timeout=600000
    ):
        """Helper method for executing an asynchronous API request."""
        job_id = await self.send_async_api_request(
            input_payload, session, execution_timeout
        )
        return await self.wait_for_api_request_completion(
            job_id, session, polling_interval
        )

    def execute_sync_api_request(
        self, input_payload, polling_interval=20, execution_timeout=600000
    ):
        """Synchronously executes an API request using the provided service API."""

        async def sync_wrapper():
            async with aiohttp.ClientSession() as session:
                return await self.execute_async_api_request(
                    input_payload, session, polling_interval, execution_timeout
                )

        return asyncio.run(sync_wrapper())
