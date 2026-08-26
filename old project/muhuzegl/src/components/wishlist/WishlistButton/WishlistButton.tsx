import { useState } from "react";
import { useToast } from "../../ui/Toast";

export default function WishlistButton() {

  const [liked, setLiked] = useState(false);
  const { showToast } = useToast();

  return (

    <button
      onClick={() => {
        showToast("Clicked!", "info");
        setLiked(!liked);
      }}
      className="px-4 py-2 bg-red-500 text-white rounded-lg"
    >
      {liked ? "Liked" : "Like"}
    </button>

  );

}