import Button from "../../ui/Button";

interface Seller {
  _id: string;
  fullName: string;
  email: string;
  phone: string;
  profileImage?: string;
}

interface Props {
  sellerId: string | Seller;
}

export default function MarketplaceContact({
  sellerId,
}: Props) {
  const seller =
    typeof sellerId === "string"
      ? null
      : sellerId;

  const sellerPhone = seller?.phone
    ? seller.phone.replace(/\s+/g, "")
    : "";

  const whatsappNumber = sellerPhone
    ? sellerPhone.startsWith("+")
      ? sellerPhone
      : sellerPhone.startsWith("0")
        ? `250${sellerPhone.substring(1)}`
        : sellerPhone
    : "";

  const whatsappUrl = whatsappNumber
    ? `https://wa.me/${whatsappNumber}`
    : "#";

  const handleChat = () => {
    if (!seller) {
      alert(
        "Seller information is not available yet."
      );
      return;
    }

    alert(
      "Chat will be connected to the MUHUZE messaging system."
    );
  };

  return (
    <section
      id="marketplace-contact"
      className="
        mt-12
        rounded-3xl
        border
        bg-white
        p-6
        shadow-sm
      "
    >
      {/* ==============================
          TITLE
      =============================== */}

      <h2 className="text-2xl font-bold mb-3">
        Contact Seller
      </h2>

      <p className="text-gray-500 mb-6">
        Interested in this listing? Contact
        the seller directly.
      </p>

      {/* ==============================
          SELLER INFORMATION
      =============================== */}

      {seller ? (
        <div
          className="
            mb-6
            rounded-2xl
            bg-gray-50
            p-5
          "
        >
          <div className="flex items-center gap-4">

            {seller.profileImage ? (
              <img
                src={seller.profileImage}
                alt={seller.fullName}
                className="
                  h-14
                  w-14
                  rounded-full
                  object-cover
                "
              />
            ) : (
              <div
                className="
                  flex
                  h-14
                  w-14
                  items-center
                  justify-center
                  rounded-full
                  bg-blue-100
                  text-xl
                  font-bold
                  text-blue-600
                "
              >
                {seller.fullName
                  ?.charAt(0)
                  .toUpperCase()}
              </div>
            )}

            <div>
              <p className="font-semibold text-lg">
                {seller.fullName}
              </p>

              <p className="text-sm text-gray-500">
                MUHUZE Seller
              </p>
            </div>

          </div>

          <div className="mt-5 space-y-2 text-gray-600">

            <p>
              <strong>Email:</strong>{" "}
              {seller.email}
            </p>

            <p>
              <strong>Phone:</strong>{" "}
              {seller.phone}
            </p>

          </div>
        </div>
      ) : (
        <div
          className="
            mb-6
            rounded-2xl
            bg-gray-50
            p-5
            text-gray-500
          "
        >
          Seller contact information is
          currently unavailable.
        </div>
      )}

      {/* ==============================
          CONTACT ACTIONS
      =============================== */}

      <div className="grid gap-4 md:grid-cols-3">

        {/* CHAT */}

        <Button
          className="w-full"
          onClick={handleChat}
        >
          Chat Seller
        </Button>

        {/* CALL */}

        {seller ? (
          <a
            href={`tel:${seller.phone}`}
            className="
              flex
              w-full
              items-center
              justify-center
              rounded-xl
              bg-blue-600
              px-4
              py-3
              font-semibold
              text-white
              transition
              hover:bg-blue-700
            "
          >
            Call Seller
          </a>
        ) : (
          <Button
            className="w-full"
            disabled
          >
            Call Seller
          </Button>
        )}

        {/* EMAIL */}

        {seller ? (
          <a
            href={`mailto:${seller.email}`}
            className="
              flex
              w-full
              items-center
              justify-center
              rounded-xl
              bg-blue-600
              px-4
              py-3
              font-semibold
              text-white
              transition
              hover:bg-blue-700
            "
          >
            Email Seller
          </a>
        ) : (
          <Button
            className="w-full"
            disabled
          >
            Email Seller
          </Button>
        )}

      </div>

      {/* ==============================
          WHATSAPP
      =============================== */}

      {seller && whatsappNumber && (
        <div className="mt-4">

          <a
            href={whatsappUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="
              flex
              w-full
              items-center
              justify-center
              rounded-xl
              bg-green-600
              px-4
              py-3
              font-semibold
              text-white
              transition
              hover:bg-green-700
            "
          >
            WhatsApp Seller
          </a>

        </div>
      )}

      {/* ==============================
          SELLER ID
      =============================== */}

      <p className="mt-6 text-sm text-gray-400">
        Seller ID:{" "}
        {typeof sellerId === "string"
          ? sellerId
          : sellerId._id}
      </p>

    </section>
  );
}