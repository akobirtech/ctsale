/** Mega-menyu va uning mobil (akkordeon) varianti. */

import { afterEach, describe, expect, it } from "vitest";
import userEvent from "@testing-library/user-event";

import CategoryMenu, { CategoryAccordion } from "./CategoryMenu";
import { cleanup, renderWithProviders, screen } from "../../test-utils";

afterEach(cleanup);

const CATEGORIES = [
  {
    id: 1,
    slug: "noutbuklar",
    name: "Noutbuklar",
    products_count: 14,
    children: [
      { id: 2, slug: "gaming-noutbuklar", name: "Gaming noutbuklar", products_count: 6, children: [] },
      { id: 3, slug: "ultrabuklar", name: "Ultrabuklar", products_count: 3, children: [] },
    ],
  },
  { id: 4, slug: "monitorlar", name: "Monitorlar", products_count: 7, children: [] },
];

describe("CategoryMenu", () => {
  it("boshida yopiq turadi", () => {
    renderWithProviders(<CategoryMenu categories={CATEGORIES} />);

    expect(screen.getByRole("button", { name: /kategoriyalar/i })).toHaveAttribute(
      "aria-expanded",
      "false"
    );
    expect(screen.queryByRole("link", { name: /gaming/i })).not.toBeInTheDocument();
  });

  it("bosilganda birinchi bo'limning ichki bo'limlarini ko'rsatadi", async () => {
    renderWithProviders(<CategoryMenu categories={CATEGORIES} />);

    await userEvent.click(screen.getByRole("button", { name: /kategoriyalar/i }));

    // Ichkisini ko'rish uchun bosish shart emas — birinchisi o'zi ochiq.
    expect(screen.getByRole("link", { name: /gaming noutbuklar/i })).toBeInTheDocument();
  });

  it("sichqoncha boshqa bo'limga olib borilsa o'ng ustun almashadi", async () => {
    renderWithProviders(<CategoryMenu categories={CATEGORIES} />);
    await userEvent.click(screen.getByRole("button", { name: /kategoriyalar/i }));

    await userEvent.hover(screen.getByRole("link", { name: /monitorlar/i }));

    expect(screen.queryByRole("link", { name: /gaming noutbuklar/i })).not.toBeInTheDocument();
    expect(screen.getByText(/ichki bo'lim yo'q/i)).toBeInTheDocument();
  });

  it("Escape bosilsa yopiladi", async () => {
    renderWithProviders(<CategoryMenu categories={CATEGORIES} />);
    await userEvent.click(screen.getByRole("button", { name: /kategoriyalar/i }));

    await userEvent.keyboard("{Escape}");

    expect(screen.queryByRole("link", { name: /gaming/i })).not.toBeInTheDocument();
  });

  it("havolalar til prefiksini saqlaydi", async () => {
    renderWithProviders(<CategoryMenu categories={CATEGORIES} />, { route: "/ru", lang: "ru" });
    await userEvent.click(screen.getByRole("button", { name: /категории/i }));

    expect(screen.getByRole("link", { name: /ultrabuklar/i })).toHaveAttribute(
      "href",
      "/ru/category/ultrabuklar"
    );
  });

  it("kategoriya bo'lmasa tugma ham chiqmaydi", () => {
    // Bo'sh menyuni ochadigan tugma foydalanuvchini chalg'itadi.
    renderWithProviders(<CategoryMenu categories={[]} />);

    expect(screen.queryByRole("button", { name: /kategoriyalar/i })).not.toBeInTheDocument();
  });
});

describe("CategoryAccordion", () => {
  it("ichki bo'limlar boshida yopiq", () => {
    renderWithProviders(<CategoryAccordion categories={CATEGORIES} />);

    expect(screen.queryByRole("link", { name: /gaming/i })).not.toBeInTheDocument();
  });

  it("strelka bosilganda ochiladi", async () => {
    renderWithProviders(<CategoryAccordion categories={CATEGORIES} />);

    await userEvent.click(screen.getByRole("button", { name: "Noutbuklar" }));

    expect(screen.getByRole("link", { name: /gaming noutbuklar/i })).toBeInTheDocument();
  });

  it("ichki bo'limi yo'q kategoriyada strelka ko'rinmaydi", () => {
    renderWithProviders(<CategoryAccordion categories={CATEGORIES} />);

    expect(screen.queryByRole("button", { name: "Monitorlar" })).not.toBeInTheDocument();
  });
});
