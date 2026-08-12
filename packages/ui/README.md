# @breero/ui

Shared BREERO consumer design system. Components are exported from `@breero/ui`; global tokens and component styles are available from `@breero/ui/styles.css` and should be imported once by the application root.

## Usage

```tsx
import { Button, Card, Container, FormField, Input } from "@breero/ui";

<Container>
  <Card>
    <FormField label="Postcode" htmlFor="postcode" required>
      <Input id="postcode" name="postcode" autoComplete="postal-code" />
    </FormField>
    <Button type="submit">Continue</Button>
  </Card>
</Container>
```

## Included

Buttons, icon buttons, form controls, choice controls, dialogs, drawers, sheets, tabs, cards, badges, avatars, status, table primitives, pagination, toast, loading/skeleton/empty/error states, price, timeline, date/time choices, upload shells, breadcrumbs and responsive layout primitives.

All controls expose native attributes, so feature teams should pass `id`, `name`, `aria-*`, disabled and validation state as normal. Overlay components manage initial focus, focus trapping, Escape dismissal, focus restoration and page scroll locking. `ToastProvider` is already installed by the public application shell.

Public marketplace and internal portals share primitives but may use different composed layouts.
