from os import path
import click
import struct
import base64
from solana.publickey import PublicKey
from solana.keypair import Keypair
from solana.rpc.api import Client
from solana.rpc.types import TxOpts
from solana.rpc.commitment import Confirmed
from solana.transaction import Transaction
from solders.keypair import Keypair as SoldersKeypair

import instructions


API_URL = "https://api.devnet.solana.com"


def get_authority_key(cache_filepath: str) -> Keypair:
    if path.exists(cache_filepath):
        click.echo("Reading authority key from file")
        with open(cache_filepath, "rb") as f:
            authority = Keypair.from_solders(SoldersKeypair.from_bytes(f.read()))
    else:
        click.echo("Creating a new authority key")
        authority = Keypair()
        with open(cache_filepath, "wb") as f:
            f.write(bytes(authority.to_solders()))
    return authority


@click.group()
def cli():
    pass


@cli.command()
@click.argument("program_id")
@click.argument("data")
@click.option("--authkey", default="./auth.key")
@click.option("--buffer-seed", default=123907)
def write(program_id, data: str, authkey: str, buffer_seed: int):
    click.echo("Writing to buffer")

    program_id = PublicKey(program_id)
    authority = get_authority_key(authkey)

    client = Client(API_URL)
    print("Requesting Airdrop of 2 SOL...")
    client.request_airdrop(authority.public_key, int(2e9))
    print("Airdrop received")

    authorized_buffer_key, bump_seed = PublicKey.find_program_address(
        [b"authority", bytes(authority.public_key), struct.pack("<Q", buffer_seed)],
        program_id,
    )
    print(f"Authorized buffer key: {authorized_buffer_key}, bump seed: {bump_seed}")

    tx = Transaction()
    signers = []
    if not client.get_account_info(authorized_buffer_key, commitment=Confirmed):
        tx.add(
            instructions.initialize_authorized_echo(
                program_id=program_id,
                authorized_buffer=authorized_buffer_key,
                authority=authority.public_key,
                buffer_seed=buffer_seed,
                buffer_size=len(data),
            )
        )
        signers.append(authority)

    tx.add(
        instructions.authorized_echo(
            program_id=program_id,
            authorized_buffer=authorized_buffer_key,
            authority=authority.public_key,
            data=data.encode("utf-8"),
        )
    )
    signers.append(authority)

    result = client.send_transaction(tx, *signers, opts=TxOpts(skip_preflight=True))
    tx_hash = result["result"]
    client.confirm_transaction(tx_hash, commitment="confirmed")

    print(f"Transaction: https://explorer.solana.com/tx/{tx_hash}?cluster=devnet")


@cli.command()
@click.argument("program_id")
@click.option("--authkey", default="./auth.key")
@click.option("--buffer-seed", default=123907)
def read(program_id: str, authkey: str, buffer_seed: int):
    click.echo("Reading from buffer")

    program_id = PublicKey(program_id)

    authority = get_authority_key(authkey)
    authorized_buffer_key, _ = PublicKey.find_program_address(
        [b"authority", bytes(authority.public_key), struct.pack("<Q", buffer_seed)],
        program_id,
    )
    client = Client(API_URL)

    acct_info = client.get_account_info(authorized_buffer_key, commitment=Confirmed)
    if acct_info["result"]["value"] is None:
        click.echo(f"Failed to get account with address '{authorized_buffer_key}'")
        return

    data = base64.b64decode(acct_info["result"]["value"]["data"][0])
    data = data[9:]
    print('Data in the buffer: "{}"'.format(data.decode("utf-8")))


if __name__ == "__main__":
    cli()
