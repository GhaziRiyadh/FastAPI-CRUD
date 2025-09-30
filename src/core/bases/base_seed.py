from abc import abstractmethod, ABC
from typing import List, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import text


class BaseSeeder(ABC):
    @abstractmethod
    def data(self) -> List[Any]:
        """Return a list of items to seed."""
        pass

    async def reset_auto_increment(
        self, session: AsyncSession, table_name: str, qty: int = 1
    ):
        """Reset the auto-increment value for a table."""
        result = await session.execute(
            text("SELECT pg_get_serial_sequence(:table, :column)"),
            {
                "table": table_name,
                "column": "id",
            },
        )
        sequence_name = result.scalar_one_or_none()
        if sequence_name:
            await session.execute(
                text(f"ALTER SEQUENCE {sequence_name} RESTART WITH {qty}")
            )

    async def execute(self, session: AsyncSession):
        """Seed the database with data, skipping existing items."""
        items = self.data()
        if not items:
            return

        counter = 0
        for item in items:
            item_id = getattr(item, "id", None)
            if item_id is not None:
                existing = await session.get(type(item), item_id)
                if existing:
                    continue
            counter += 1
            session.add(item)

        if counter > 0:
            table_name = getattr(items[0], "__tablename__", None)
            if table_name:
                await self.reset_auto_increment(session, table_name, counter)
            await session.commit()
