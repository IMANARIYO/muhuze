import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import type { Review } from "../../types/review";

interface ReviewContextType {
  reviews: Review[];

  addReview: (review: Review) => void;

  deleteReview: (id: number) => void;

  getReviewsByProduct: (
    productId: number
  ) => Review[];
}

const ReviewContext = createContext<
  ReviewContextType | undefined
>(undefined);

interface Props {
  children: ReactNode;
}

export function ReviewProvider({
  children,
}: Props) {
  const [reviews, setReviews] = useState<Review[]>(() => {
    const saved = localStorage.getItem("reviews");

    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem(
      "reviews",
      JSON.stringify(reviews)
    );
  }, [reviews]);

  const addReview = (review: Review) => {
    setReviews((current) => [
      ...current,
      review,
    ]);
  };

  const deleteReview = (id: number) => {
    setReviews((current) =>
      current.filter(
        (review) => review.id !== id
      )
    );
  };

  const getReviewsByProduct = (
    productId: number
  ) => {
    return reviews.filter(
      (review) =>
        review.productId === productId
    );
  };

  return (
    <ReviewContext.Provider
      value={{
        reviews,
        addReview,
        deleteReview,
        getReviewsByProduct,
      }}
    >
      {children}
    </ReviewContext.Provider>
  );
}

export function useReviews() {
  const context = useContext(ReviewContext);

  if (!context) {
    throw new Error(
      "useReviews must be used inside ReviewProvider"
    );
  }

  return context;
}

export default ReviewContext;