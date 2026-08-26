import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type {
  Order,
  CreateOrder,
} from "../../types/order";

import { orderService } from "../../business/services/orderService";

interface OrderContextType {
  orders: Order[];

  addOrder: (
    order: CreateOrder
  ) => Promise<Order>;

  updateOrder: (
    order: Order
  ) => Promise<void>;

  deleteOrder: (
    id: string
  ) => Promise<void>;

  refreshOrders: () => Promise<void>;

  getOrdersByBuyer: (
    buyerId: string
  ) => Promise<Order[]>;

  updateOrderStatus: (
    id: string,
    status: Order["status"]
  ) => Promise<void>;
}

const OrderContext =
  createContext<OrderContextType | undefined>(
    undefined
  );

interface Props {
  children: ReactNode;
}

export function OrderProvider({
  children,
}: Props) {
  const [orders, setOrders] =
    useState<Order[]>([]);

  useEffect(() => {
    refreshOrders();
  }, []);

  /**
   * ==========================================
   * LOAD ALL ORDERS
   * ==========================================
   */
  async function refreshOrders() {
    try {
      const data =
        await orderService.getAll();

      setOrders(data);
    } catch (error) {
      console.error(
        "Failed to load orders:",
        error
      );
    }
  }

  /**
   * ==========================================
   * CREATE ORDER
   * ==========================================
   *
   * IMPORTANT:
   * Return the order created by the backend.
   *
   * This allows Checkout to know:
   *
   * createdOrder._id
   * createdOrder.paymentMethod
   * createdOrder.paymentStatus
   * createdOrder.total
   */
  async function addOrder(
    order: CreateOrder
  ): Promise<Order> {
    const createdOrder =
      await orderService.create(order);

    await refreshOrders();

    return createdOrder;
  }

  /**
   * ==========================================
   * UPDATE ORDER
   * ==========================================
   */
  async function updateOrder(
    order: Order
  ) {
    await orderService.update(order);

    await refreshOrders();
  }

  /**
   * ==========================================
   * DELETE ORDER
   * ==========================================
   */
  async function deleteOrder(
    id: string
  ) {
    await orderService.delete(id);

    await refreshOrders();
  }

  /**
   * ==========================================
   * GET ORDERS BY BUYER
   * ==========================================
   */
  async function getOrdersByBuyer(
    buyerId: string
  ): Promise<Order[]> {
    return await orderService.findByBuyer(
      buyerId
    );
  }

  /**
   * ==========================================
   * UPDATE ORDER STATUS
   * ==========================================
   */
  async function updateOrderStatus(
    id: string,
    status: Order["status"]
  ) {
    await orderService.updateStatus(
      id,
      status
    );

    await refreshOrders();
  }

  return (
    <OrderContext.Provider
      value={{
        orders,

        addOrder,

        updateOrder,

        deleteOrder,

        refreshOrders,

        getOrdersByBuyer,

        updateOrderStatus,
      }}
    >
      {children}
    </OrderContext.Provider>
  );
}

export function useOrders() {
  const context =
    useContext(OrderContext);

  if (!context) {
    throw new Error(
      "useOrders must be used inside OrderProvider"
    );
  }

  return context;
}

export default OrderContext;