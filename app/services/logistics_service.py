import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from app.common.errors import NotFoundError
from app.database.pgsql import get_pg
from app.entity.pgsql import OrderLogistics
from app.repo import order_logistics_repo, orders_repo
from app.schemas.logistics import LogisticsOut, OrderLogisticsOut


class LogisticsService:
    async def get_order_tracking(self, order_id: str) -> OrderLogisticsOut:
        """获取订单物理信息"""
        async with get_pg() as session:
            # 1. 获取订单基本信息
            order = await orders_repo.get_by_id(session, order_id)
            if not order:
                raise NotFoundError("订单不存在")

            # 2. 获取已有轨迹
            logs = await order_logistics_repo.get_by_order_id(session, order_id)

            # 3. 如果状态是已发货或已完成，尝试补全演示需要的模拟轨迹
            if order.status in ("shipped", "completed") and order.shipped_at:
                new_logs = await self._generate_mock_logs(
                    session, order, existing_logs=logs
                )
                if new_logs:
                    # 将新生成的插入到列表中并排序
                    logs.extend(new_logs)
                    logs.sort(key=lambda x: x.log_time)

            return OrderLogisticsOut(
                order_id=order.id,
                tracking_no=order.tracking_no,
                courier_name=order.courier_name,
                items=[LogisticsOut.model_validate(log) for log in logs],
            )

    async def _generate_mock_logs(
        self, session, order, existing_logs: list[OrderLogistics]
    ) -> list[OrderLogistics]:
        """模拟生成物流轨迹（快速演示版：10s间隔）"""
        from app.repo import addresses_repo

        base_time = order.shipped_at
        now = datetime.now(base_time.tzinfo)
        elapsed = (now - base_time).total_seconds()

        # 获取现有的状态信息，用于防重
        existing_messages = {log.status_message for log in existing_logs}

        items = []

        # 1. 初始节点 (T=0) - 通常 ship_order 已经加过了，这里做一次兜底或校验
        # 如果 existing_logs 为空，可以考虑加一个。但此处我们尊重 ship_order 的手动触发。

        # 2. 中点节点 (T+10s)
        mid_msg = "快件到达：业务分拣中心"
        if elapsed >= 10 and mid_msg not in existing_messages:
            items.append(
                OrderLogistics(
                    order_id=order.id,
                    status_message=mid_msg,
                    location="中点站",
                    log_time=base_time + timedelta(seconds=10),
                )
            )

        # 3. 终点节点 (T+20s)
        end_msg = "快件已送达目的地，准备派送"
        if elapsed >= 20 and end_msg not in existing_messages:
            address_str = "客户地址"
            try:
                addr = await addresses_repo.get_by_id(session, str(order.address_id))
                if addr:
                    address_str = f"{addr.province}{addr.city}{addr.district}"
            except Exception:
                pass

            items.append(
                OrderLogistics(
                    order_id=order.id,
                    status_message=end_msg,
                    location=address_str,
                    log_time=base_time + timedelta(seconds=20),
                )
            )

            # 如果订单已完成，追加签收记录
            final_msg = "包裹已签收，感谢您的支持！"
            if (
                order.status == "completed"
                and order.completed_at
                and final_msg not in existing_messages
            ):
                items.append(
                    OrderLogistics(
                        order_id=order.id,
                        status_message=final_msg,
                        location=address_str,
                        log_time=order.completed_at,
                    )
                )

        for log in items:
            session.add(log)

        if items:
            await session.flush()

        return items

    async def add_initial_log(
        self,
        order_id: uuid.UUID | str,
        courier_name: str,
        tracking_no: str,
        location: str,
    ) -> None:
        """添加发货时的初始轨迹"""
        async with get_pg() as session:
            log = OrderLogistics(
                order_id=uuid.UUID(str(order_id)),
                status_message=f"包裹已由【{courier_name}】揽收，单号：{tracking_no}",
                location=location,
                log_time=datetime.now(UTC),
            )
            await order_logistics_repo.add_log(session, log)
            await session.commit()

    async def simulate_shipping_progress(
        self, order_id: uuid.UUID, address_id: uuid.UUID
    ) -> None:
        """后台模拟物流演进：中点(10s) -> 终点(20s)"""
        from app.repo import addresses_repo

        # 1. 等待 10 秒后到达中转站
        await asyncio.sleep(10)
        async with get_pg() as session:
            log = OrderLogistics(
                order_id=order_id,
                status_message="快件到达：业务分拣中心",
                location="中点站",
                log_time=datetime.now(UTC),
            )
            session.add(log)
            # context manager handles commit

        # 2. 再等待 10 秒后到达目的地
        await asyncio.sleep(10)
        async with get_pg() as session:
            location = "目的地"
            try:
                addr = await addresses_repo.get_by_id(session, str(address_id))
                if addr:
                    location = f"{addr.province}{addr.city}{addr.district}"
            except Exception:
                pass

            log = OrderLogistics(
                order_id=order_id,
                status_message="快件已送达目的地，准备派送",
                location=location,
                log_time=datetime.now(UTC),
            )
            session.add(log)
            # context manager handles commit


logistics_service = LogisticsService()
