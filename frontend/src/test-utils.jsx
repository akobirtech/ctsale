/**
 * Testlar uchun umumiy o'rash.
 *
 * Komponentlarning aksariyati i18n, router va toast kontekstiga
 * tayanadi. Har bir testda ularni qo'lda yig'ish o'rniga shu yerda
 * bir marta.
 */

import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { I18nProvider } from "./i18n";
import { ToastProvider } from "./hooks/useToast";

export function renderWithProviders(ui, { route = "/uz", lang = "uz" } = {}) {
  return render(
    <MemoryRouter initialEntries={[route]}>
      <I18nProvider lang={lang}>
        <ToastProvider>{ui}</ToastProvider>
      </I18nProvider>
    </MemoryRouter>
  );
}

export * from "@testing-library/react";
