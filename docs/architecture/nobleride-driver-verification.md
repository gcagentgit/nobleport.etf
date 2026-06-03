# NobleRide Driver Verification Architecture

NobleRide.io is a blockchain-based ridesharing platform with strict driver eligibility requirements based on driving record verification.

## Core Requirement

**No speeding tickets or moving violations in the last 2 consecutive years.**

This is an objective, legally defensible safety standard that applies equally to all drivers.

---

## Verification Flow

| Step | Requirement | Verified By |
|------|-------------|-------------|
| 1 | Driver registers | Self-report (name, optional gender) |
| 2 | Submit driving record (last 3-5 years) | Owner / Oracle / DMV API |
| 3 | **2-year clean record check** | Smart contract (automatic) |
| 4 | Full background check | Owner / DAO |
| 5 | Verified status granted | On-chain |
| 6 | Optional: Passenger prefers women drivers | Frontend filter |

---

## Smart Contract Architecture

### Driver States

```
Unregistered → PendingRecordCheck → PendingBackground → Verified
                      ↓                    ↓
                RecordFailed            Rejected
```

### Key Functions

- `registerDriver(name, isWoman)` — Initial registration
- `submitDrivingRecord(driver, violations, timestamp)` — Oracle submits DMV data
- `verifyDriver(driver, approved, backgroundHash)` — Final approval
- `requestRide(price)` — Passenger requests ride
- `acceptRide(rideId)` — Verified driver accepts
- `completeRide(rideId)` — Transfer payment to driver

### Eligibility Computation

The contract automatically checks if any violation occurred within the last 730 days:

```solidity
uint256 twoYearsAgo = block.timestamp - 730 days;
for (uint i = 0; i < violations.length; i++) {
    if (violations[i].timestamp >= twoYearsAgo) {
        isClean = false;
        break;
    }
}
```

---

## Off-Chain Verification Service

### DMV Integration Options

| Provider | Coverage | Notes |
|----------|----------|-------|
| Checkr | US nationwide | FCRA compliant, API available |
| GoodHire | US nationwide | Background + driving records |
| Sterling | US + international | Enterprise-grade |
| State DMV APIs | State-specific | Direct integration where available |

### FCRA Compliance Requirements

When using third-party background check services:

1. **Written consent** — Driver must provide explicit written authorization
2. **Adverse action notice** — If rejected based on record, must notify driver
3. **Dispute rights** — Driver can dispute inaccurate information
4. **Data retention limits** — Cannot retain records indefinitely

---

## Frontend Features

### Passenger Preferences

Passengers can optionally filter for women drivers. This is:

- **Legal** — Customer preference, not platform discrimination
- **Optional** — Does not exclude male drivers from the platform
- **Transparent** — Passengers make the choice, not the algorithm

### Driver Display

- Name and gender indicator
- Completed ride count
- Rating (when implemented)
- Verification status badge

---

## Legal Considerations

### What's Allowed

- Eligibility based on **driving record** (objective safety standard)
- Passengers **choosing** to prefer certain drivers
- Transparent verification criteria

### What's Risky

- Platform **requiring** only one gender (Title VII violation in US)
- Hidden algorithmic bias
- Discriminatory pricing

### Recommended Approach

Focus on **safety standards** (clean driving record, background check) that apply equally to all drivers. Gender preference is a passenger choice, not a platform requirement.

---

## File Structure

```
nobleride/
├── contracts/
│   └── NobleRide.sol          # Main smart contract
├── services/
│   └── drivingRecordVerification.ts  # DMV integration service
└── components/
    └── NobleRideApp.tsx       # React frontend
```

---

## Deployment Checklist

- [ ] Deploy NobleRide.sol to testnet
- [ ] Configure oracle wallet for driving record submissions
- [ ] Integrate with DMV API provider (Checkr recommended)
- [ ] Implement FCRA consent flow
- [ ] Deploy frontend with wallet connection
- [ ] Set up event indexing for driver queries
- [ ] Security audit of smart contract
- [ ] Legal review of terms of service

---

## Future Enhancements

- **DAO governance** — Drivers vote on rule changes (e.g., 2-year → 3-year requirement)
- **Rating system** — Passengers rate drivers, affects visibility
- **Insurance integration** — On-chain proof of coverage
- **Multi-chain deployment** — Polygon, Arbitrum for lower fees
