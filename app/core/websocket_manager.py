import json

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # 存储 user_id 到 WebSocket 连接列表的映射
        # { user_id: [websocket1, websocket2, ...] }
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """建立连接"""
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, websocket: WebSocket, user_id: str):
        """断开连接"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            # 如果该用户没有任何活跃连接了，清理键值
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: str):
        """向特定用户的所有连接发送消息"""
        if user_id in self.active_connections:
            content = json.dumps(message, ensure_ascii=False)
            # 遍历该用户的所有活跃标签页/设备，发送推送
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_text(content)
                except Exception:
                    # 如果发送失败（通常是连接已断开但还没进入 disconnect 逻辑），后续会由清理逻辑处理
                    pass

    async def broadcast_to_user(self, user_id: str, payload: dict):
        """业务层调用的广播接口"""
        await self.send_personal_message(payload, user_id)


# 全局单例管理器
ws_manager = ConnectionManager()
chat_ws_manager = ConnectionManager()
