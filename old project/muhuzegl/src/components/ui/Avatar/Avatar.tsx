interface AvatarProps {
  src: string;
  alt: string;
  size?: "sm" | "md" | "lg";
}

const sizes = {
  sm: "w-10 h-10",
  md: "w-16 h-16",
  lg: "w-24 h-24",
};

export default function Avatar({
  src,
  alt,
  size = "md",
}: AvatarProps) {
  return (
    <img
      src={src}
      alt={alt}
      className={`
        ${sizes[size]}
        rounded-full
        object-cover
        border-2
        border-blue-500
      `}
    />
  );
}