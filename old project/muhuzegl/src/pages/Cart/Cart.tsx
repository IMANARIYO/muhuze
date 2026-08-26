import Container from "../../components/ui/Container";
import SectionTitle from "../../components/ui/SectionTitle";

import { useCart } from "../../context/CartContext";

import CartItem from "../../components/cart/CartItem";
import CartSummary from "../../components/cart/CartSummary";

export default function Cart() {
  const { cart } = useCart();

  return (
    <section className="py-16">
      <Container>
        <SectionTitle
          title="Shopping Cart"
          subtitle="Review your selected products before checkout."
        />

        {cart.length === 0 ? (
          <p className="text-center mt-12">
            Your cart is empty.
          </p>
        ) : (
          <>
            <div className="space-y-6 mt-10">
              {cart.map((item) => (
                <CartItem
                  key={item.item._id}
                  item={item}
                />
              ))}
            </div>

            <div className="mt-10">
              <CartSummary />
            </div>
          </>
        )}
      </Container>
    </section>
  );
}