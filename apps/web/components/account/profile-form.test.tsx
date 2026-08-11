import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProfileForm } from "./profile-form";

const {updateProfile}=vi.hoisted(()=>({updateProfile:vi.fn().mockResolvedValue({})}));
vi.mock("@/lib/customer/api",()=>({customerApi:{customer:{updateProfile}}}));
describe("ProfileForm",()=>{it("presents customer details without allowing unverified email edits",()=>{render(<ProfileForm/>);expect(screen.getByLabelText("Email")).toBeDisabled();expect(screen.getByLabelText(/First name/)).toHaveValue("Maya")});it("submits supported profile fields",async()=>{render(<ProfileForm/>);fireEvent.change(screen.getByLabelText("Phone number"),{target:{value:"+44 7700 900999"}});fireEvent.click(screen.getByRole("button",{name:"Save changes"}));expect(await screen.findByRole("status")).toHaveTextContent("updated");expect(updateProfile).toHaveBeenCalledWith(expect.objectContaining({phone:"+44 7700 900999"}))})});
