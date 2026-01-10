interface ComingSoonProps {
  title: string;
  description: string;
}

export function ComingSoon({ title, description }: ComingSoonProps) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="font-mono text-4xl text-teal-600/20 dark:text-cream-300/20">
        //
      </div>
      <h2 className="mt-6 font-mono text-xl tracking-tight text-teal-800 dark:text-cream-100">
        {title.toUpperCase()}
      </h2>
      <p className="mt-3 max-w-md text-sm text-teal-600/60 dark:text-cream-300/60">
        {description}
      </p>
      <div className="mt-6 border border-cream-300 px-4 py-2 font-mono text-xs text-teal-600/60 dark:border-teal-700 dark:text-cream-300/60">
        COMING SOON
      </div>
    </div>
  );
}
