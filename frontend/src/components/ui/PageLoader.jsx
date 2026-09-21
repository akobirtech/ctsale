export default function PageLoader() {
  return (
    <div className="container-page py-16" role="status" aria-live="polite">
      <div className="space-y-4">
        <div className="skeleton h-8 w-1/3" />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 8 }).map((_, index) => (
            <div key={index} className="space-y-2">
              <div className="skeleton aspect-[4/3] w-full" />
              <div className="skeleton h-4 w-full" />
              <div className="skeleton h-4 w-2/3" />
            </div>
          ))}
        </div>
      </div>
      <span className="sr-only">Yuklanmoqda</span>
    </div>
  );
}
