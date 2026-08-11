# @breero/api-client

Typed API client shared by BREERO frontend applications.

Modules should mirror backend boundaries:

- auth
- services
- addresses
- availability
- bookings
- customer
- partner
- ops
- payments
- finance

Frontend applications must not scatter raw API URLs through components. Centralize transport, authentication, errors and typed contracts here.
