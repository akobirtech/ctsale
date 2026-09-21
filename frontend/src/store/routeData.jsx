/** SSR'da yuklangan ma'lumotni sahifalarga yetkazadi. */

import { createContext, useContext } from "react";

const RouteDataContext = createContext({ data: null, routeId: null });

export function RouteDataProvider({ value, children }) {
  return <RouteDataContext.Provider value={value}>{children}</RouteDataContext.Provider>;
}

/**
 * SSR yuklagan ma'lumot. Brauzerdagi navigatsiyada `null` bo'ladi —
 * shunda sahifa o'zi TanStack Query orqali yuklaydi.
 */
export function useRouteData(routeId) {
  const context = useContext(RouteDataContext);
  if (routeId && context.routeId !== routeId) return null;
  return context.data;
}
