from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver



async def get_postgress_checkpointer():
    DB_URI = "postgresql://postgres:root@localhost:5432/postgres?sslmode=disable"

    async with AsyncPostgresSaver.from_conn_string(DB_URI) as checkpointer:
        await checkpointer.setup()
        # Note: If used as a context manager, the checkpointer
        # closes the connection when exiting this block.
        return checkpointer
