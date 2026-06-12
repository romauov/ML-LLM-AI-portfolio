from typing import Optional
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy import text


class Drug:
    """CRUD-класс для лекарственного препарата."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self.session_factory = session_factory

    async def create(self, trade_name: str, generic_name: str, drug_class: str, dosage_form: str,
                     route: str, manufacturer: str, target_animals: str, instruction: str):
        """
        Сохраняет экземпляр класса в базе данных.

        :param trade_name: Торговое наименование.
        :param generic_name: Генерическое наименование.
        :param drug_class: Класс препарата.
        :param dosage_form: Форма дозирования.
        :param route: Способ введения.
        :param manufacturer: Производитель.
        :param target_animals: Целевые животные.
        :param instruction: Инструкция.
        """
        query = text("""
            INSERT INTO drugs (trade_name, generic_name, drug_class, dosage_form, route, manufacturer, target_animals, instruction)
            VALUES (:trade_name, :generic_name, :drug_class, :dosage_form, :route, :manufacturer, :target_animals, :instruction)
        """)
        async with self.session_factory() as session:
            await session.execute(
                query,
                {
                    "trade_name": trade_name,
                    "generic_name": generic_name,
                    "drug_class": drug_class,
                    "dosage_form": dosage_form,
                    "route": route,
                    "manufacturer": manufacturer,
                    "target_animals": target_animals,
                    "instruction": instruction
                }
            )
            await session.commit()

    async def find_drug_by_id(self, drug_id: int) -> Optional[dict]:
        """
        Находит препарат по его ID.

        :param drug_id: ID препарата.
        :return: Словарь с данными препарата или None, если не найден.
        """
        query = text("SELECT * FROM drugs WHERE id = :drug_id")

        async with self.session_factory() as session:
            result = await session.execute(query, {"drug_id": drug_id})
            row = result.fetchone()
            return dict(row._mapping) if row else None