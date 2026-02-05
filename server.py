import asyncio

clients = {}

async def broadcast(message, sender_writer=None):
    if not clients:
        return
    
    msg_bytes = f"{message}\n".encode()
    for writer in list(clients.keys()):
        if writer != sender_writer:
            try:
                writer.write(msg_bytes)
                await writer.drain()
            except Exception:
                clients.pop(writer, None)

async def handle_client(reader, writer):
    addr = writer.get_extra_info('peername')
    try:
        name_data = await reader.readline()
        if not name_data:
            return
        
        username = name_data.decode().strip()
        clients[writer] = username
        print(f"CONNECTED: {username} from {addr}")
        await broadcast(f"{username} joined the chat!")

        while True:
            data = await reader.readline()
            if not data:
                break
            
            message = data.decode().strip()
            print(f"[{username}]: {message}")
            await broadcast(f"{username}: {message}", sender_writer=writer)

    except Exception as e:
        print(f"Error with {addr}: {e}")
    finally:
        user = clients.pop(writer, "Someone")
        print(f"DISCONNECTED: {user}")
        await broadcast(f"{user} left the chat.")
        writer.close()
        await writer.wait_closed()

async def main():
    server = await asyncio.start_server(handle_client, '127.0.0.1', 8888)
    print("Chat Server running on port 8888...")
    async with server:
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())