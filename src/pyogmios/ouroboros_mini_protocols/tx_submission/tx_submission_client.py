from typing import Callable, Optional, Coroutine, Any, List

from pyogmios.connection import InteractionContext
from pyogmios.exceptions import WebSocketClosedError
from pyogmios.models import BaseModel, Utxo, TxId, EvaluationResult
from pyogmios.models.response_model import (
    SubmitTxResponse,
    Response,
    EvaluateTxResponse,
)
from pyogmios.ouroboros_mini_protocols.tx_submission.evaluate_tx import (
    evaluate_tx,
)
from pyogmios.ouroboros_mini_protocols.tx_submission.submission_errors import (
    SubmitTxErrorShelley,
)
from pyogmios.ouroboros_mini_protocols.tx_submission.submit_tx import submit_tx
from pyogmios.utils.socket_utils import ensure_socket_is_open


class TxSubmissionClient(BaseModel):
    context: InteractionContext
    evaluate_tx: Callable[
        [str, Utxo], Coroutine[Any, Any, EvaluationResult | List[Exception]]
    ]
    submit_tx: Callable[[str], Coroutine[Any, Any, TxId | List[SubmitTxErrorShelley]]]
    shutdown: Callable[[], Coroutine[Any, Any, None]]


def match_submit_tx(response: Response) -> SubmitTxResponse | None:
    """
    Check if is a submit tx response.
    :param response: The response
    :return: The submit tx response
    """
    return response if isinstance(response, SubmitTxResponse) else None


def match_evaluate_tx(response: Response) -> EvaluateTxResponse | None:
    """
    Check if is an evaluate tx response.
    :param response: The response
    :return: The evaluate tx response
    """
    return response if isinstance(response, EvaluateTxResponse) else None


async def create_tx_submission_client(
    context: InteractionContext,
) -> TxSubmissionClient:
    """
    Creates a tx submission client.
    :param context: The interaction context
    :return: The tx submission client
    """
    websocket_app = context.socket

    try:

        async def default_submit_tx(bytes_: str) -> TxId | List[SubmitTxErrorShelley]:
            """
            Submit a transaction.
            :param bytes_: The bytes
            :return: The tx id
            """
            try:
                await ensure_socket_is_open(context.socket)
                return await submit_tx(context, bytes_)
            except Exception as err:
                print(err)
                await shutdown()

        async def default_evaluate_tx(
            bytes_: str, additional_utxo_set: Optional[Utxo] = None
        ) -> EvaluationResult | List[Exception]:
            """
            Evaluate a transaction.
            :param bytes_: The bytes
            :param additional_utxo_set: The additional utxo set
            :return: The evaluation result
            """
            try:
                await ensure_socket_is_open(context.socket)
                return await evaluate_tx(context, bytes_, additional_utxo_set)
            except Exception as err:
                print(err)
                await shutdown()

        async def shutdown() -> None:
            """
            Shutdown the tx submission client.
            """
            try:
                await ensure_socket_is_open(websocket_app)
                websocket_app.close()
            except (WebSocketClosedError, AttributeError):
                print("TxSubmission Client already closed.")
            else:
                print("Shutting down TxSubmission Client...")

        return TxSubmissionClient(
            context=context,
            shutdown=shutdown,
            evaluate_tx=default_evaluate_tx,
            submit_tx=default_submit_tx,
        )
    except Exception as e:
        print(e)
