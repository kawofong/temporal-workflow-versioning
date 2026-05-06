"""Worker entry point.

Environment variables:
    TEMPORAL_ADDRESS      Temporal server address (default: localhost:7233)
    TEMPORAL_NAMESPACE    Temporal namespace (default: default)
    TASK_QUEUE            Task queue name (default: card-task-queue)
    DEPLOYMENT_NAME       Worker deployment name (default: card-service)
    BUILD_ID              Worker build ID — must be unique per code version (required)
"""

import asyncio
import concurrent.futures
import logging
import os

from activities.card import (
    generate_statement,
    persist_statement,
    send_statement_notification,
)
from temporalio.client import Client
from temporalio.worker import Worker, WorkerDeploymentConfig, WorkerDeploymentVersion
from workflows.card import CardWorkflow

logging.basicConfig(level=logging.INFO)


async def main() -> None:
    build_id = os.environ.get("BUILD_ID")
    if not build_id:
        raise ValueError("BUILD_ID environment variable is required")

    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    task_queue = os.environ.get("TASK_QUEUE", "card-task-queue")
    deployment_name = os.environ.get("DEPLOYMENT_NAME", "card-service")

    client = await Client.connect(address, namespace=namespace)

    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as activity_executor:
        worker = Worker(
            client,
            task_queue=task_queue,
            workflows=[CardWorkflow],
            activities=[
                generate_statement,
                persist_statement,
                send_statement_notification,
            ],
            activity_executor=activity_executor,
            deployment_config=WorkerDeploymentConfig(
                version=WorkerDeploymentVersion(
                    deployment_name=deployment_name,
                    build_id=build_id,
                ),
                use_worker_versioning=True,
            ),
        )

        logging.info(
            f"Worker started — deployment={deployment_name} build_id={build_id} "
            f"task_queue={task_queue} address={address}"
        )
        await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
