interface ComingSoonProps {
  title: string;
  description: string;
}

export function ComingSoon({ title, description }: ComingSoonProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <h2 className="mb-2 text-xl font-semibold text-gray-800 dark:text-gray-200">
        {title}
      </h2>
      <p className="mb-4 max-w-md text-gray-600 dark:text-gray-400">{description}</p>
      <span className="rounded-full bg-amber-100 px-3 py-1 text-sm text-amber-800 dark:bg-amber-900/30 dark:text-amber-200">
        Coming Soon
      </span>
    </div>
  );
}
