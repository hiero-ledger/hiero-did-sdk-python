import asyncio
from typing import Any, cast

from hiero_sdk_python import Client, PrivateKey, ResponseCode, TransactionReceipt
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
    receipt = cast(TransactionReceipt, execution_task.result())

    # We need additional validation since Hiero SDK Python do not catch error statuses in some cases (in recent versions)
    if receipt.status != ResponseCode.SUCCESS:
        error_reason = ResponseCode.get_name(receipt.status) if receipt.status else "Response code is empty"
        raise Exception(f"Error retrieving transaction receipt: {error_reason}")

    return receipt


async def execute_hcs_query_async(query: Query, client: Client) -> Any:
    # Hiero Python SDK removed 'execute' method from 'Query' base class
    # It looks non-optimal for public API and there is actually no 'Query' subclasses that do not implement 'execute'
    # It makes sense to use simple runtime check until this problem is addressed
    if not query.execute:  # pyright: ignore [reportAttributeAccessIssue]
        raise Exception("Query instance do not implement 'execute' method")
    query_task = asyncio.create_task(asyncio.to_thread(lambda: query.execute(client)))  # pyright: ignore [reportAttributeAccessIssue]
    await query_task
    return query_task.result()
