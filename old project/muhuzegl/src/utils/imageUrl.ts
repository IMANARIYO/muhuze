const API_BASE_URL = "http://localhost:5000";

export function getImageUrl(image?: string) {
  if (!image) {
    return "/placeholder-image.png";
  }

  if (image.startsWith("http")) {
    return image;
  }

  return `${API_BASE_URL}${image}`;
}