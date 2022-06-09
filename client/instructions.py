import enum
import struct
from solana.publickey import PublicKey
from solana.system_program import SYS_PROGRAM_ID
from solana.transaction import AccountMeta, TransactionInstruction


class __InstructionId(enum.Enum):
    Echo = 0
    InitializeAuthorizedEcho = 1
    AuthorizedEcho = 2
    InitializeVendingMachineEcho = 3
    VendingMachineEcho = 4


def echo(
    program_id: PublicKey, buffer: PublicKey, data: bytes
) -> TransactionInstruction:
    return TransactionInstruction(
        keys=[AccountMeta(pubkey=buffer, is_signer=False, is_writable=True)],
        program_id=program_id,
        data=b"".join([struct.pack("<B", __InstructionId.Echo.value), data]),
    )


def initialize_authorized_echo(
    authorized_buffer: PublicKey,
    authority: PublicKey,
    program_id: PublicKey,
    buffer_seed: int,
    buffer_size: int,
) -> TransactionInstruction:
    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=authorized_buffer, is_signer=False, is_writable=True),
            AccountMeta(pubkey=authority, is_signer=True, is_writable=False),
            AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        ],
        program_id=program_id,
        data=b"".join(
            [
                struct.pack("<B", __InstructionId.InitializeAuthorizedEcho.value),
                struct.pack("<Q", buffer_seed),
                struct.pack("<Q", buffer_size),
            ]
        ),
    )


def authorized_echo(
    authorized_buffer: PublicKey,
    authority: PublicKey,
    program_id: PublicKey,
    data: bytes,
) -> TransactionInstruction:
    return TransactionInstruction(
        keys=[
            AccountMeta(pubkey=authorized_buffer, is_signer=False, is_writable=True),
            AccountMeta(pubkey=authority, is_signer=True, is_writable=False),
        ],
        program_id=program_id,
        data=b"".join(
            [
                struct.pack("<B", __InstructionId.AuthorizedEcho.value),
                struct.pack("<I", len(data)),
                data,
            ]
        ),
    )
