import { useState } from "react";

import Button from "../ui/Button";

import { useReviews } from "../../context/ReviewContext";
import { useToast } from "../ui/Toast";
interface Props {
  productId: number;
}

export default function ReviewForm({
  productId,
}: Props) {
  const { addReview } = useReviews();

  const [rating, setRating] = useState(5);

  const [comment, setComment] = useState("");
const { showToast } = useToast();
  const currentUser = JSON.parse(
    localStorage.getItem("currentUser") || "null"
  );

  const handleSubmit = () => {
    if (!comment.trim()) {
      showToast("Please write a review.","warning");
      return;
    }

    addReview({
      id: Date.now(),
      productId,
      user: currentUser?.fullName || "Anonymous",
      rating,
      comment,
      createdAt: new Date().toISOString(),
    });

    setComment("");

    setRating(5);

    showToast("Review submitted successfully!", "success");
  };

  return (
    <div className="border rounded-xl p-6 mt-10">

      <h2 className="text-2xl font-bold mb-6">
        Write a Review
      </h2>

      <label className="block mb-2">
        Rating
      </label>

      <select
        value={rating}
        onChange={(e) =>
          setRating(Number(e.target.value))
        }
        className="border rounded-lg px-3 py-2 w-full"
      >
        <option value={5}>⭐⭐⭐⭐⭐</option>
        <option value={4}>⭐⭐⭐⭐</option>
        <option value={3}>⭐⭐⭐</option>
        <option value={2}>⭐⭐</option>
        <option value={1}>⭐</option>
      </select>

      <textarea
        className="border rounded-lg w-full mt-5 p-3 h-32"
        placeholder="Write your review..."
        value={comment}
        onChange={(e) =>
          setComment(e.target.value)
        }
      />

      <Button
        className="mt-5"
        onClick={handleSubmit}
      >
        Submit Review
      </Button>

    </div>
  );
}