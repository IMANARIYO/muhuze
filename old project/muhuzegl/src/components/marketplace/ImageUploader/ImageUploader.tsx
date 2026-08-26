import { FaTrash } from "react-icons/fa";

interface Props {
  existingImages: string[];
  newImages: File[];

  onExistingImagesChange: (
    images: string[]
  ) => void;

  onNewImagesChange: (
    images: File[]
  ) => void;
}

export default function ImageUploader({
  existingImages,
  newImages,
  onExistingImagesChange,
  onNewImagesChange,
}: Props) {

  function handleFiles(
  event: React.ChangeEvent<HTMLInputElement>
) {
  if (!event.target.files) return;

  onNewImagesChange([
    ...newImages,
    ...Array.from(event.target.files),
  ]);
}

function removeExistingImage(index: number) {
  onExistingImagesChange(
    existingImages.filter(
      (_, i) => i !== index
    )
  );
}

function removeNewImage(index: number) {
  onNewImagesChange(
    newImages.filter(
      (_, i) => i !== index
    )
  );
}
 

  return (
    <div className="space-y-5">

      <div>
        <label className="block mb-2 font-medium">
          Images
        </label>

        <input
          type="file"
          multiple
          accept="image/*"
          onChange={handleFiles}
          className="
            w-full
            rounded-xl
            border
            px-4
            py-3
          "
        />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">

  {existingImages.map((image, index) => (
    <div
      key={`existing-${index}`}
      className="relative"
    >
      <img
        src={`http://localhost:5000${image}`}
        alt="Existing"
        className="
          h-36
          w-full
          object-cover
          rounded-xl
          border
        "
      />

      <button
        type="button"
        onClick={() => removeExistingImage(index)}
        className="
          absolute
          top-2
          right-2
          bg-red-600
          text-white
          p-2
          rounded-full
        "
      >
        <FaTrash />
      </button>
    </div>
  ))}

  {newImages.map((image, index) => (
  <div
    key={`new-${index}`}
    className="relative"
  >
    <img
      src={URL.createObjectURL(image)}
      alt="Preview"
      className="
        h-36
        w-full
        object-cover
        rounded-xl
        border
      "
    />

    <button
      type="button"
      onClick={() => removeNewImage(index)}
      className="
        absolute
        top-2
        right-2
        bg-red-600
        text-white
        p-2
        rounded-full
      "
    >
      <FaTrash />
    </button>
  </div>
))}

  
</div>
    </div>
  );
}