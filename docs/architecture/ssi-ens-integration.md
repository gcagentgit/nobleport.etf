# Self-Sovereign Identity (SSI) & ENS Integration

NoblePort Fund leverages Self-Sovereign Identity (SSI) principles through ENS-based Decentralized Identifiers (DIDs) to provide cryptographic identity verification for all ecosystem participants.

## ENS DID Architecture

```
NoblePort SSI Layer
├── Identity Resolution
│   ├── did:ens:nobleport.eth (Root Identity)
│   ├── did:ens:etf.nobleport.eth (Fund Identity)
│   └── Subname DIDs for properties/participants
│
├── Resolution Stack
│   ├── did-resolver (Universal DID resolution)
│   ├── ens-did-resolver (ENS-specific resolver)
│   └── ethers.js (Ethereum provider)
│
└── Verification Layer
    ├── DID Documents
    ├── Verification Methods
    └── Service Endpoints
```

## Installation

```bash
npm install ens-did-resolver did-resolver ethers
```

## Usage

### Resolve NoblePort Root DID

```typescript
import { resolveEnsDid, NOBLEPORT_ENS } from './src/lib/ensDidResolver';

const didDocument = await resolveEnsDid('did:ens:nobleport.eth');
console.log(didDocument.verificationMethod);
```

### Resolve ENS Address

```typescript
import { resolveEnsAddress } from './src/lib/ensDidResolver';

const address = await resolveEnsAddress('nobleport.eth');
// Returns '0x...' or null
```

### Get ENS Text Records

```typescript
import { getEnsTextRecords } from './src/lib/ensDidResolver';

const records = await getEnsTextRecords('nobleport.eth', [
  'url',
  'email',
  'description',
  'com.twitter',
  'com.github',
]);
```

## Configuration

Create a `.env` file with your Ethereum provider credentials:

```bash
NEXT_PUBLIC_INFURA_ID=your_infura_project_id
# Or use Alchemy
NEXT_PUBLIC_ALCHEMY_KEY=your_alchemy_key
```

## SSI Dashboard

The NoblePort SSI Architecture dashboard (`src/components/NoblePortSSIArchitecture.tsx`) provides:

- **Identity Resolution**: Resolve any ENS name to its DID Document
- **Address Lookup**: View associated Ethereum addresses
- **Text Records**: Display ENS profile information
- **Architecture Visualization**: Interactive SSI flow diagram

## DID Document Structure

A resolved `did:ens:nobleport.eth` returns a DID Document:

```json
{
  "id": "did:ens:nobleport.eth",
  "verificationMethod": [
    {
      "id": "did:ens:nobleport.eth#controller",
      "type": "EcdsaSecp256k1RecoveryMethod2020",
      "controller": "did:ens:nobleport.eth",
      "blockchainAccountId": "eip155:1:0x..."
    }
  ],
  "authentication": ["did:ens:nobleport.eth#controller"],
  "service": [
    {
      "id": "did:ens:nobleport.eth#website",
      "type": "LinkedDomains",
      "serviceEndpoint": "https://nobleport.etf"
    }
  ]
}
```

---

## Integration with Fund Operations

### Investor Verification
- Verify investor identities through their ENS DIDs
- Cryptographic proof of accreditation status
- Automated KYC/AML compliance through DID credentials

### Asset Provenance
- Each tokenized property has an associated DID
- Verifiable credentials for property documentation
- Immutable audit trail on Ethereum

### Governance Participation
- DID-based voting for NBPT token holders
- Verifiable delegation of voting rights
- Transparent governance record

---

## Resources

- [DID:ENS Method Specification](https://github.com/veramolabs/did-ens-spec)
- [ENS DID Resolver](https://github.com/veramolabs/ens-did-resolver)
- [ENS Documentation](https://docs.ens.domains/)
- [DID Core Specification](https://www.w3.org/TR/did-core/)
