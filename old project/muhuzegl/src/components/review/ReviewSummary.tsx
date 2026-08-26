import { useReviews } from "../../context/ReviewContext";

interface Props {
  productId: number;
}

export default function ReviewSummary({
  productId,
}: Props) {
  const { getReviewsByProduct } = useReviews();

  const reviews = getReviewsByProduct(productId);

  if (reviews.length === 0) {
    return null;
  }

  const average =
    reviews.reduce(
      (sum, review) => sum + review.rating,
      0
    ) / reviews.length;

  return (
    <div className="border rounded-xl p-5 mt-10">

      <h2 className="text-2xl font-bold">
        Reviews Summary
      </h2>

      <h1 className="text-5xl mt-5 font-bold text-blue-600">
        {average.toFixed(1)}
      </h1>

      <p className="mt-2">
        Based on {reviews.length} review
        {reviews.length > 1 ? "s" : ""}
      </p>

    </div>
  );
}