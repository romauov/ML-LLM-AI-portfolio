import traceback
from fastapi import APIRouter, HTTPException, status

from app.bot_manager import BotManager
from app.schemas import ClientCreateRequest, ClientData
from utils.logger import logger as log

# Создаем основной роутер
router = APIRouter()

# Глобальный экземпляр менеджера
bot_manager = BotManager()


@router.post("/clients/", status_code=status.HTTP_201_CREATED)
async def create_client(client_data: ClientCreateRequest):
    """Добавить и запустить нового клиента"""
    try:
        # Создаем объект ClientData
        client = ClientData(**client_data.model_dump())

        # Добавляем и запускаем клиента
        await bot_manager.add_and_start_client(client)
        result = f"Bot '{client.client_name}' started successfully"
        log.info(result)
        return result

    except Exception as e:
        log.error(f"Error starting bot: {str(e)}")
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start bot: {str(e)}"
        )


@router.delete("/clients/{client_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(client_name: str):
    """Удалить клиента и остановить его бота"""
    try:
        if client_name not in bot_manager.clients:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Bot '{client_name}' not found"
            )

        await bot_manager.remove_client(client_name)
        log.info(f"Bot '{client_name}' removed successfully")
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Error removing client: {str(e)}")
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove bot: {str(e)}"
        )


@router.get("/clients/")
async def list_clients():
    """Получить список всех клиентов"""
    clients = list(bot_manager.clients.keys())
    return clients


@router.post("/shutdown", status_code=status.HTTP_202_ACCEPTED)
async def shutdown_all():
    """Остановить всех ботов"""
    try:
        await bot_manager.stop_all()
        log.info("All clients stopped successfully")
        return {"message": "All bots stopped successfully"}
    except Exception as e:
        log.error(f"Error stopping all bots: {str(e)}")
        log.error(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop all bots: {str(e)}"
        )
