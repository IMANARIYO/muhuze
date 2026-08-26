import {
  useEffect,
  useState,
} from "react";

import type { MarketplaceItem } from "../../../types/marketplaceItem";

import { getImageUrl } from "../../../utils/imageUrl";

interface Props {
  item: MarketplaceItem;
}

export default function MarketplaceImageGallery({
  item,
}: Props) {
  /*
   * Keep only valid image paths.
   */
  const validImages = Array.isArray(item.images)
    ? item.images.filter(
        (image) =>
          typeof image === "string" &&
          image.trim() !== ""
      )
    : [];

  const [selectedImage, setSelectedImage] =
    useState<string>(
      validImages[0] ?? ""
    );

  const [isZoomed, setIsZoomed] =
    useState(false);

  /*
   * Reset the selected image whenever
   * the marketplace item changes.
   */
  useEffect(() => {
    const images = Array.isArray(item.images)
      ? item.images.filter(
          (image) =>
            typeof image === "string" &&
            image.trim() !== ""
        )
      : [];

    setSelectedImage(images[0] ?? "");
    setIsZoomed(false);
  }, [item]);

  /*
   * Find current image position.
   */
  const currentIndex = Math.max(
    validImages.findIndex(
      (image) => image === selectedImage
    ),
    0
  );

  /*
   * Show previous image.
   */
  function showPrevious() {
    if (validImages.length === 0) {
      return;
    }

    if (currentIndex <= 0) {
      setSelectedImage(
        validImages[validImages.length - 1]
      );
    } else {
      setSelectedImage(
        validImages[currentIndex - 1]
      );
    }
  }

  /*
   * Show next image.
   */
  function showNext() {
    if (validImages.length === 0) {
      return;
    }

    if (
      currentIndex >=
      validImages.length - 1
    ) {
      setSelectedImage(validImages[0]);
    } else {
      setSelectedImage(
        validImages[currentIndex + 1]
      );
    }
  }

  /*
   * When an image cannot be loaded,
   * replace it with the placeholder.
   */
  function handleImageError(
    event: React.SyntheticEvent<HTMLImageElement>
  ) {
    const image = event.currentTarget;

    if (
      image.src.includes(
        "/placeholder-image.png"
      )
    ) {
      return;
    }

    image.src = "/placeholder-image.png";
  }

  return (
    <div className="space-y-4">

      {/* =========================
          MAIN IMAGE
      ========================== */}

      <div className="relative">
        <img
          src={
            selectedImage
              ? getImageUrl(selectedImage)
              : "/placeholder-image.png"
          }
          alt={
            item.title ||
            "Marketplace Image"
          }
          onError={handleImageError}
          onClick={() => {
            if (selectedImage) {
              setIsZoomed(true);
            }
          }}
          className="
            w-full
            h-[500px]
            object-cover
            rounded-3xl
            border
            cursor-zoom-in
            transition-all
            duration-300
          "
        />

        {/* Previous / Next buttons */}

        {validImages.length > 1 && (
          <>
            <button
              type="button"
              onClick={showPrevious}
              className="
                absolute
                left-4
                top-1/2
                -translate-y-1/2
                w-12
                h-12
                rounded-full
                bg-black/60
                hover:bg-black/80
                text-white
                text-2xl
                transition
              "
              aria-label="Previous image"
            >
              ‹
            </button>

            <button
              type="button"
              onClick={showNext}
              className="
                absolute
                right-4
                top-1/2
                -translate-y-1/2
                w-12
                h-12
                rounded-full
                bg-black/60
                hover:bg-black/80
                text-white
                text-2xl
                transition
              "
              aria-label="Next image"
            >
              ›
            </button>
          </>
        )}
      </div>

      {/* =========================
          THUMBNAILS
      ========================== */}

      {validImages.length > 1 && (
        <div className="grid grid-cols-4 md:grid-cols-5 gap-4">
          {validImages.map(
            (image, index) => (
              <button
                key={`${image}-${index}`}
                type="button"
                onClick={() =>
                  setSelectedImage(image)
                }
                className={`
                  overflow-hidden
                  rounded-xl
                  border-2
                  transition-all
                  duration-300
                  ${
                    selectedImage === image
                      ? "border-blue-600 scale-105"
                      : "border-gray-200 hover:border-blue-300"
                  }
                `}
              >
                <img
                  src={getImageUrl(image)}
                  alt={`${item.title} ${
                    index + 1
                  }`}
                  onError={handleImageError}
                  className="
                    w-full
                    h-24
                    object-cover
                  "
                />
              </button>
            )
          )}
        </div>
      )}

      {/* =========================
          ZOOM MODAL
      ========================== */}

      {isZoomed && (
        <div
          className="
            fixed
            inset-0
            z-50
            bg-black/90
            flex
            items-center
            justify-center
            p-6
          "
          onClick={() =>
            setIsZoomed(false)
          }
        >
          {/* Close */}

          <button
            type="button"
            onClick={() =>
              setIsZoomed(false)
            }
            className="
              absolute
              top-6
              right-8
              text-white
              text-5xl
              hover:text-gray-300
            "
            aria-label="Close image"
          >
            ×
          </button>

          {/* Previous */}

          {validImages.length > 1 && (
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                showPrevious();
              }}
              className="
                absolute
                left-6
                text-white
                text-6xl
                hover:text-gray-300
              "
              aria-label="Previous image"
            >
              ‹
            </button>
          )}

          {/* Zoomed image */}

          <img
            src={
              selectedImage
                ? getImageUrl(selectedImage)
                : "/placeholder-image.png"
            }
            alt={
              item.title ||
              "Marketplace Image"
            }
            onError={handleImageError}
            onClick={(event) =>
              event.stopPropagation()
            }
            className="
              max-h-[90vh]
              max-w-[90vw]
              object-contain
              rounded-2xl
              transition-all
              duration-300
            "
          />

          {/* Next */}

          {validImages.length > 1 && (
            <button
              type="button"
              onClick={(event) => {
                event.stopPropagation();
                showNext();
              }}
              className="
                absolute
                right-6
                text-white
                text-6xl
                hover:text-gray-300
              "
              aria-label="Next image"
            >
              ›
            </button>
          )}
        </div>
      )}
    </div>
  );
}