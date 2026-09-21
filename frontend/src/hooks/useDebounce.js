import { useEffect, useState } from "react";

/** Qidiruv maydonida har harf uchun so'rov yubormaslik uchun. */
export function useDebounce(value, delay = 350) {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);

  return debounced;
}
