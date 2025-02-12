import asyncio
from typing import Any

from hiero_sdk_python import Client, PrivateKey, TransactionReceipt
from hiero_sdk_python.query.query import Query
from hiero_sdk_python.transaction.transaction import Transaction


async def sign_hcs_transaction_async(transaction: Transaction, signing_keys: list[PrivateKey]) -> Transaction:
    def sign_transaction():
        signed_transaction = transaction
        for signing_key in signing_keys:
            signed_transaction = signed_transaction.sign(signing_key)
        return signed_transaction

    signing_task = asyncio.create_task(asyncio.to_thread(sign_transaction))
    await signing_task

    return signing_task.result()


async def execute_hcs_transaction_async(transaction: Transaction, client: Client) -> TransactionReceipt:
    execution_task = asyncio.create_task(asyncio.to_thread(lambda: transaction.execute(client)))
    await execution_task
    return execution_task.result()


async def execute_hcs_query_async(query: Query, client: Client) -> Any:
    query_task = asyncio.create_task(asyncio.to_thread(lambda: query.execute(client)))
    await query_task
    return query_task.result()
