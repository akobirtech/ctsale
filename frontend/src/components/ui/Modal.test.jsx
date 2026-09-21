/** Modal: yopilish yo'llari, fokus va sahifani qulflash. */

import { afterEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";

import Modal from "./Modal";
import { cleanup, renderWithProviders, screen } from "../../test-utils";

afterEach(cleanup);

function open(props = {}) {
  const onClose = vi.fn();
  renderWithProviders(
    <Modal open onClose={onClose} title="Sarlavha" {...props}>
      <input aria-label="birinchi" />
      <button type="button">ichki</button>
    </Modal>
  );
  return onClose;
}

describe("Modal", () => {
  it("yopiq bo'lsa hech narsa chizmaydi", () => {
    renderWithProviders(
      <Modal open={false} onClose={() => {}} title="Sarlavha">
        matn
      </Modal>
    );

    expect(screen.queryByText("Sarlavha")).not.toBeInTheDocument();
  });

  it("dialog roli va nomi bor", () => {
    open();

    expect(screen.getByRole("dialog")).toHaveAttribute("aria-modal", "true");
    expect(screen.getByRole("dialog")).toHaveAccessibleName("Sarlavha");
  });

  it("Escape bosilsa yopiladi", async () => {
    const onClose = open();

    await userEvent.keyboard("{Escape}");

    expect(onClose).toHaveBeenCalled();
  });

  it("orqa fonga bosilsa yopiladi", async () => {
    const onClose = open();

    await userEvent.click(screen.getAllByRole("button", { name: /yopish/i })[0]);

    expect(onClose).toHaveBeenCalled();
  });

  it("ochilganda fokus ichkariga ko'chadi", () => {
    open();

    // Aks holda klaviatura orqa fondagi sahifada qolib ketardi.
    expect(screen.getByLabelText("birinchi")).toHaveFocus();
  });

  it("ochiq turganda sahifa aylanmaydi", () => {
    open();

    expect(document.body.style.overflow).toBe("hidden");
  });

  it("yopilgandan keyin aylanish tiklanadi", () => {
    const { unmount } = renderWithProviders(
      <Modal open onClose={() => {}} title="Sarlavha">
        matn
      </Modal>
    );

    unmount();

    expect(document.body.style.overflow).not.toBe("hidden");
  });

  it("tavsif va pastki tugmalarni ko'rsatadi", () => {
    open({ description: "Tushuntirish", footer: <button type="button">Saqlash</button> });

    expect(screen.getByText("Tushuntirish")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Saqlash" })).toBeInTheDocument();
  });
});
