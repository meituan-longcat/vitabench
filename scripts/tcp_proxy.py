#!/usr/bin/env python3
import argparse
import asyncio
import signal
import time


def _timestamp() -> str:
    return time.strftime("%F %T")


def _ignore_sigterm() -> None:
    print(f"{_timestamp()} proxy ignored SIGTERM", flush=True)


async def _pipe(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass


async def _handle(
    target_host: str,
    target_port: int,
    client_reader: asyncio.StreamReader,
    client_writer: asyncio.StreamWriter,
) -> None:
    try:
        upstream_reader, upstream_writer = await asyncio.open_connection(
            target_host, target_port
        )
    except Exception:
        client_writer.close()
        return
    await asyncio.gather(
        _pipe(client_reader, upstream_writer),
        _pipe(upstream_reader, client_writer),
    )


async def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--listen-host", default="0.0.0.0")
    parser.add_argument("--listen-port", type=int, required=True)
    parser.add_argument("--target-host", default="127.0.0.1")
    parser.add_argument("--target-port", type=int, required=True)
    args = parser.parse_args()

    loop = asyncio.get_running_loop()
    try:
        loop.add_signal_handler(signal.SIGTERM, _ignore_sigterm)
    except NotImplementedError:
        signal.signal(signal.SIGTERM, lambda *_args: _ignore_sigterm())

    server = await asyncio.start_server(
        lambda reader, writer: _handle(
            args.target_host, args.target_port, reader, writer
        ),
        args.listen_host,
        args.listen_port,
        reuse_address=True,
    )
    print(
        f"{_timestamp()} proxy listening "
        f"{args.listen_host}:{args.listen_port} -> "
        f"{args.target_host}:{args.target_port}",
        flush=True,
    )
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(_main())
