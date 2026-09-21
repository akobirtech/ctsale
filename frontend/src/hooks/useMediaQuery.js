import { useEffect, useState } from "react";

/**
 * SSR'da har doim `false` qaytaradi — server ekran o'lchamini bilmaydi.
 * Shuning uchun uni faqat qo'shimcha xulq uchun ishlatamiz, asosiy
 * tartib esa CSS orqali moslashadi (hydrate mos kelmasligi bo'lmasin).
 */
export function useMediaQuery(query) {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const list = window.matchMedia(query);
    setMatches(list.matches);
    const handler = (event) => setMatches(event.matches);
    list.addEventListener("change", handler);
    return () => list.removeEventListener("change", handler);
  }, [query]);

  return matches;
}

export const useIsMobile = () => useMediaQuery("(max-width: 767px)");
