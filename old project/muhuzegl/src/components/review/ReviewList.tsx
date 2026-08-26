import { useReviews } from "../../context/ReviewContext";

interface Props {
  productId: number;
}

export default function ReviewList({
  productId,
}: Props) {
  const { getReviewsByProduct } = useReviews();

  const reviews = getReviewsByProduct(productId);

  if (reviews.length === 0) {
    return (
      <div className="mt-10">
        <h2 className="text-2xl font-bold">
          Customer Reviews
        </h2>

        <p className="text-gray-500 mt-4">
          No reviews yet.
        </p>
      </div>
    );
  }

  return (
    <div className="mt-10">

      <h2 className="text-2xl font-bold mb-6">
        Customer Reviews
      </h2>

      <div className="space-y-6">

        {reviews.map((review) => (

          <div
            key={review.id}
            className="border rounded-xl p-5"
          >

            <div className="flex justify-between">

              <h3 className="font-bold">
                {review.user}
              </h3>

              <span>
                {"⭐".repeat(review.rating)}
              </span>

            </div>

            <p className="mt-4">
              {review.comment}
            </p>

            <p className="text-gray-500 text-sm mt-4">
              {new Date(
                review.createdAt
              ).toLocaleDateString()}
            </p>

          </div>

        ))}

      </div>

    </div>
  );
}