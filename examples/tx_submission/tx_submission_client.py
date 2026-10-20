"""
Transaction submission client example
"""

import asyncio

from pyogmios.connection import (
    InteractionContextOptions,
    create_interaction_context,
)
from pyogmios.enums import InteractionType
from pyogmios.ouroboros_mini_protocols.tx_submission.tx_submission_client import (
    create_tx_submission_client,
)


async def main():
    """
    This run the tx submission client and print the output.
    """
    interaction_context_options = InteractionContextOptions(
        interaction_type=InteractionType.ONE_TIME, log_level="INFO"
    )
    interaction_context = await create_interaction_context(options=interaction_context_options)
    await asyncio.sleep(1)
    print(interaction_context.socket.sock.connected)

    tx_submission_client = await create_tx_submission_client(interaction_context)

    tx_cbor = "84a5008182582047103aaf73dd59926e10d9f0c48389d9c497ccbf5020636c2f8b125dbce517f4000181a200583900b3282e51ccf3ac9cd06955dfbcc6a758148e3d4ce898be04535fb6c73ca4ae128a01e1cd444e4fe9d10a1365c9074132b742a8eef8915371011b00000002361cdc6b021a00031e15031a020375e8048382008200581c3ca4ae128a01e1cd444e4fe9d10a1365c9074132b742a8eef89153718a03581c58fa45ec1acf9718f0c7d2615e58f1f7d7fa6af361536696959b6c395820241f9ca94ef891d08679759d087c4fae27723c53933e66e17c5a6e1746ba35ec1a3b9aca001a1443fd00d81e82011819581de03ca4ae128a01e1cd444e4fe9d10a1365c9074132b742a8eef891537181581c3ca4ae128a01e1cd444e4fe9d10a1365c9074132b742a8eef8915371818400190bb944228bcf63f682782768747470733a2f2f6d6574612e77617665706f6f6c2e6469676974616c2f777662672e6a736f6e58203a1f908cdde67ff446c912a0c5169702b2719c9991ca581398b770c18492bd7783028200581c3ca4ae128a01e1cd444e4fe9d10a1365c9074132b742a8eef8915371581c58fa45ec1acf9718f0c7d2615e58f1f7d7fa6af361536696959b6c39a1008382582051d3e6dd9c7b885981f4bdbc009fe9287778520fccf2d370fcc263103c4acfa25840463c9642ec3568e2780667653e3d0203fb691e6bc1d533224b262198e3ea00f4e069f8dfcd5ad70a19d8734a5bb1f291013a4c68aa1fe2d0ee09e0ea9f7da50682582028c6fc0b05a6ec6f0b29429edc9939878823e9f4fc6080cd6b5a09b0b8f666b35840f966ae8bdee73facab2540d3893646b839b3dff518a9e0622830d737b5e67efa526615858bc537c66bfa329f81a8e76ae719d1aa747e8fee7b26c19cc26a230382582097ecb851227546a760295eba586580a0646893f061c0faf0ca39031d7dbb3d2a5840a471cf551ed64ef0b3152ecd762accfba3b5a33fda94a5c248c5a8031f4460dac1318ceb87e2f26a43f01a28646e43e7a7dca62333a96711aa5fb161c3132e0af5f6"
    # print("Submit Tx")
    # result = await tx_submission_client.submit_tx(tx_cbor)
    # print(f"Transaction submission result: {result}")

    # tx_id = TxId(__root__="810b37cc2eb254a4cd6bde6149d08dbca8138b7ba4ec5ad996dbcb971271beb4")
    result = await tx_submission_client.evaluate_tx(tx_cbor)
    print(f"Transaction evaluation result: {result}")

    print("Shutting down")
    await tx_submission_client.shutdown()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
