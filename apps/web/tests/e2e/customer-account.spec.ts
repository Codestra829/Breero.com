import { expect, test } from "@playwright/test";

const widths=[375,430,768,1024,1280,1440];
for(const width of widths){test(`account dashboard is responsive at ${width}px`,async({page})=>{await page.setViewportSize({width,height:900});await page.goto("/account");await expect(page.getByRole("heading",{name:/Good afternoon/})).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth-document.documentElement.clientWidth)).toBeLessThanOrEqual(0);if(width<=900)await expect(page.getByLabel("Account section")).toBeVisible();else await expect(page.getByRole("navigation",{name:"Account navigation"})).toBeVisible();if([375,768,1440].includes(width))await page.screenshot({path:`test-results/account-${width}.png`,fullPage:true})})}

test("booking detail exposes customer-safe job information",async({page})=>{await page.goto("/account/bookings/BR-240817");await expect(page.getByRole("heading",{name:"Home cleaning",level:1})).toBeVisible();await expect(page.getByText("Your professional")).toBeVisible();await expect(page.getByText("Job timeline")).toBeVisible();await expect(page.getByText(/Provider and internal pricing information are never shown/)).toBeVisible()});

test("customer can approve a quote and continue to payment",async({page})=>{await page.goto("/account/quotes/QT-1048");await page.getByText("I’ve reviewed the work and terms").click();await page.getByRole("button",{name:"Approve quote"}).click();await expect(page.getByText("Quote approved")).toBeVisible();await expect(page.getByRole("button",{name:"Continue to payment"})).toBeVisible()});

test("session expiry gives a clear recovery path",async({page})=>{await page.goto("/account/session-expired");await expect(page.getByRole("heading",{name:"Your session has expired"})).toBeVisible();await expect(page.getByRole("link",{name:"Sign in again"})).toHaveAttribute("href","/account/login")});

test("unknown customer resources use the account not-found state",async({page})=>{await page.goto("/account/bookings/not-a-booking");await expect(page.getByRole("heading",{name:"We couldn’t find that"})).toBeVisible()});
