/** Shikoyat formasi: sabablar, validatsiya va xato xabarlari. */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";

import ReportModal from "./ReportModal";
import { reports as reportsApi } from "../../api/endpoints";
import { cleanup, renderWithProviders, screen, waitFor } from "../../test-utils";

vi.mock("../../api/endpoints", () => ({
  reports: { reasons: vi.fn(), create: vi.fn() },
}));

const REASONS = [
  { value: "scam", label: "Firibgarlik" },
  { value: "other", label: "Boshqa" },
];

beforeEach(() => {
  reportsApi.reasons.mockResolvedValue(REASONS);
  reportsApi.create.mockResolvedValue({ detail: "Qabul qilindi." });
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function open(props = {}) {
  const onClose = vi.fn();
  renderWithProviders(
    <ReportModal open onClose={onClose} slug="asus-rog" productTitle="ASUS ROG" {...props} />
  );
  return onClose;
}

describe("ReportModal", () => {
  it("sabablarni backenddan oladi", async () => {
    open();

    await waitFor(() => expect(screen.getByRole("option", { name: "Firibgarlik" })).toBeInTheDocument());
    // Ro'yxat frontendda qotirilsa moderator ko'rgan qiymatlar bilan mos kelmasdi.
    expect(reportsApi.reasons).toHaveBeenCalledOnce();
  });

  it("e'lon nomini ko'rsatadi", async () => {
    open();

    expect(await screen.findByText("ASUS ROG")).toBeInTheDocument();
  });

  it("yuborganda slug va sababni jo'natadi", async () => {
    const onClose = open();
    await screen.findByRole("option", { name: "Firibgarlik" });

    await userEvent.click(screen.getByRole("button", { name: /yuborish/i }));

    await waitFor(() =>
      expect(reportsApi.create).toHaveBeenCalledWith({
        slug: "asus-rog",
        reason: "scam",
        comment: "",
      })
    );
    expect(onClose).toHaveBeenCalled();
  });

  it('"Boshqa" sababida izoh majburiy', async () => {
    open();
    await screen.findByRole("option", { name: "Boshqa" });

    await userEvent.selectOptions(screen.getByRole("combobox"), "other");
    await userEvent.click(screen.getByRole("button", { name: /yuborish/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/izoh majburiy/i);
    expect(reportsApi.create).not.toHaveBeenCalled();
  });

  it("qisqa izoh ham yetarli emas", async () => {
    open();
    await screen.findByRole("option", { name: "Boshqa" });
    await userEvent.selectOptions(screen.getByRole("combobox"), "other");

    await userEvent.type(screen.getByRole("textbox"), "yomon");
    await userEvent.click(screen.getByRole("button", { name: /yuborish/i }));

    expect(reportsApi.create).not.toHaveBeenCalled();
  });

  it("takroriy shikoyatda backend xabarini ko'rsatadi", async () => {
    reportsApi.create.mockRejectedValue({
      response: { data: { error: { message: "Siz allaqachon shikoyat yuborgansiz." } } },
    });
    const onClose = open();
    await screen.findByRole("option", { name: "Firibgarlik" });

    await userEvent.click(screen.getByRole("button", { name: /yuborish/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/allaqachon/i);
    // Xato bo'lsa oyna yopilmasligi kerak — foydalanuvchi sababni ko'rsin.
    expect(onClose).not.toHaveBeenCalled();
  });

  it("bekor qilish oynani yopadi", async () => {
    const onClose = open();

    await userEvent.click(screen.getByRole("button", { name: /bekor qilish/i }));

    expect(onClose).toHaveBeenCalled();
  });
});
