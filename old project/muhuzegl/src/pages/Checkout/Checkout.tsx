import { useState } from "react";

import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import { useNavigate } from "react-router-dom";

import { useCart } from "../../context/CartContext";
import { useOrders } from "../../context/OrderContext";
import { useToast } from "../../components/ui/Toast";
import { useAuth } from "../../context/AuthContext";

import CustomerInformation from "../../components/checkout/CustomerInformation";
import DeliveryAddress from "../../components/checkout/DeliveryAddress";
import PaymentMethod from "../../components/checkout/PaymentMethod";
import OrderReview from "../../components/checkout/OrderReview";
import PlaceOrderButton from "../../components/checkout/PlaceOrderButton";

export default function Checkout() {
  const navigate = useNavigate();

  const { showToast } = useToast();

  const { cart, clearCart } = useCart();

  const { currentUser } = useAuth();

  const { addOrder } = useOrders();

  const [fullName, setFullName] =
    useState("");

  const [email, setEmail] =
    useState("");

  const [phoneNumber, setPhoneNumber] =
    useState("");

  const [province, setProvince] =
    useState("");

  const [district, setDistrict] =
    useState("");

  const [sector, setSector] =
    useState("");

  const [streetAddress, setStreetAddress] =
    useState("");

  const [paymentMethod, setPaymentMethod] =
    useState("");

  const [placingOrder, setPlacingOrder] =
    useState(false);

  /**
   * ==========================================
   * PLACE ORDER
   * ==========================================
   */
  const handlePlaceOrder = async () => {
    /*
     * Prevent double-clicking the
     * Place Order button.
     */
    if (placingOrder) {
      return;
    }

    /**
     * ==========================================
     * AUTHENTICATION
     * ==========================================
     */
    if (!currentUser) {
      showToast(
        "Please login before placing an order.",
        "error"
      );

      return;
    }

    /**
     * ==========================================
     * CUSTOMER INFORMATION
     * ==========================================
     */
    if (!fullName.trim()) {
      showToast(
        "Please enter your full name.",
        "warning"
      );

      return;
    }

    if (!email.trim()) {
      showToast(
        "Please enter your email.",
        "warning"
      );

      return;
    }

    if (!phoneNumber.trim()) {
      showToast(
        "Please enter your phone number.",
        "warning"
      );

      return;
    }

    /**
     * ==========================================
     * DELIVERY ADDRESS
     * ==========================================
     */
    if (!province.trim()) {
      showToast(
        "Please enter your province.",
        "warning"
      );

      return;
    }

    if (!district.trim()) {
      showToast(
        "Please enter your district.",
        "warning"
      );

      return;
    }

    if (!sector.trim()) {
      showToast(
        "Please enter your sector.",
        "warning"
      );

      return;
    }

    if (!streetAddress.trim()) {
      showToast(
        "Please enter your street address.",
        "warning"
      );

      return;
    }

    /**
     * ==========================================
     * PAYMENT METHOD
     * ==========================================
     */
    if (!paymentMethod) {
      showToast(
        "Please choose a payment method.",
        "warning"
      );

      return;
    }

    /**
     * ==========================================
     * CART
     * ==========================================
     */
    if (cart.length === 0) {
      showToast(
        "Your cart is empty.",
        "error"
      );

      return;
    }

    try {
      setPlacingOrder(true);

      /**
       * ========================================
       * BUILD ORDER DATA
       * ========================================
       *
       * IMPORTANT:
       *
       * The frontend sends only:
       *
       * - buyerId
       * - buyer
       * - products
       * - deliveryAddress
       * - paymentMethod
       *
       * The backend is responsible for:
       *
       * - calculating the real total
       * - setting order status
       * - setting payment status
       */
      const orderData = {
        buyerId: currentUser._id,

        buyer: currentUser.fullName,

        products: cart.map((cartItem) => ({
          productId:
            cartItem.item._id,

          quantity:
            cartItem.quantity,
        })),

        deliveryAddress:
          `${province}, ${district}, ${sector}, ${streetAddress}`,

        paymentMethod,
      };

      /**
       * ========================================
       * CREATE ORDER
       * ========================================
       *
       * This waits for MongoDB/backend
       * confirmation.
       */
      const createdOrder =
        await addOrder(orderData);

      console.log(
        "ORDER CREATED:",
        createdOrder
      );

      /**
       * ========================================
       * VERIFY ORDER ID
       * ========================================
       */
      if (!createdOrder?._id) {
        throw new Error(
          "Order was created but no order ID was returned."
        );
      }

      /**
       * ========================================
       * SUCCESS
       * ========================================
       */
      showToast(
        "Order placed successfully!",
        "success"
      );

      /**
       * Clear cart ONLY after the
       * backend successfully creates
       * the order.
       */
      clearCart();

      /**
       * ========================================
       * ORDER CONFIRMATION
       * ========================================
       *
       * Pass the real MongoDB order ID
       * to the confirmation page.
       */
      navigate(
        `/order-confirmation?orderId=${createdOrder._id}`
      );

    } catch (error) {
      console.error(
        "PLACE ORDER ERROR:",
        error
      );

      showToast(
        error instanceof Error
          ? error.message
          : "Unable to place your order.",
        "error"
      );

    } finally {
      setPlacingOrder(false);
    }
  };

  return (
    <section className="py-16">

      <Container>

        <SectionTitle
          title="Checkout"
          subtitle="Complete your order securely."
        />

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-3 gap-10">

          {/* =================================
              LEFT SIDE
          ================================= */}

          <div className="lg:col-span-2 space-y-10">

            <CustomerInformation
              fullName={fullName}
              email={email}
              phoneNumber={phoneNumber}
              setFullName={setFullName}
              setEmail={setEmail}
              setPhoneNumber={setPhoneNumber}
            />

            <DeliveryAddress
              province={province}
              district={district}
              sector={sector}
              streetAddress={streetAddress}
              setProvince={setProvince}
              setDistrict={setDistrict}
              setSector={setSector}
              setStreetAddress={
                setStreetAddress
              }
            />

            <PaymentMethod
              paymentMethod={paymentMethod}
              setPaymentMethod={
                setPaymentMethod
              }
            />

          </div>

          {/* =================================
              RIGHT SIDE
          ================================= */}

          <div className="space-y-6">

            <OrderReview />

            <PlaceOrderButton
              onPlaceOrder={
                handlePlaceOrder
              }
            />

            {placingOrder && (
              <p className="text-center text-sm text-gray-500">
                Creating your order...
              </p>
            )}

          </div>

        </div>

      </Container>

    </section>
  );
}