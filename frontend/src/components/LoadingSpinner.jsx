export default function LoadingSpinner({ size = "md", text = "Loading..." }) {
  const sizeClass = size === "sm" ? "w-5 h-5" : size === "lg" ? "w-10 h-10" : "w-7 h-7";
  return (
    <div className="flex flex-col items-center justify-center gap-2 py-12">
      <div className={`${sizeClass} border-4 border-blue-500 border-t-transparent rounded-full animate-spin`} />
      {text && <p className="text-sm text-gray-500">{text}</p>}
    </div>
  );
}
