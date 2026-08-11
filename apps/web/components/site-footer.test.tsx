import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { SiteFooter } from "./site-footer";

describe("SiteFooter", () => {
  it("provides shared support and legal navigation", () => {
    render(<SiteFooter />);
    expect(screen.getByRole("contentinfo")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Help centre" })).toHaveAttribute("href", "/help");
    expect(screen.getByRole("link", { name: "Accessibility" })).toBeInTheDocument();
  });
});
