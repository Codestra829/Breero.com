# SECURITY / AUTHORIZATION MATRIX

## Customer

Can:

```
own ProjectRequests

own Quotes

own Conversations

own Bookings

own Jobs

own Reviews

own Disputes
```

Cannot access another customer's records.

## Provider Owner

Can access resources for active provider memberships.

## Provider Manager

Same scope with permissions limited by assigned role.

## Worker

Only:

```
assigned jobs

own availability

own credentials

approved job actions
```

## Dispatcher

Can:

```
inspect matching

manage operational assignment

manage jobs
```

Cannot:

```
approve payouts

refund money
```

## Support

Can assist customer/provider operations subject to explicit permission.

Does not automatically gain credentials or finance authority.

## Trust & Safety

Can:

```
credentials

provider suspension

reviews moderation

disputes
```

## Finance

Can:

```
refund

payout approval

financial reports
```

Does not automatically gain Ops/Admin rights.

## Admin

Configuration/administrative permission only as explicitly granted.

---
