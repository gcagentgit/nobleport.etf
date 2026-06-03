import { ethers } from 'ethers';

interface Violation {
  reason: string;
  timestamp: number;
}

interface DrivingRecord {
  tickets: Array<{
    reason: string;
    movingViolation: boolean;
    dateUnix: number;
  }>;
}

interface VerificationResult {
  isEligible: boolean;
  violations: Violation[];
  driverAddress: string;
}

const TWO_YEARS_SECONDS = 730 * 24 * 60 * 60;

export async function verifyDrivingRecord(
  driverAddress: string,
  licenseNumber: string,
  state: string,
  contractAddress: string,
  contractABI: ethers.InterfaceAbi,
  rpcUrl: string,
  ownerPrivateKey: string
): Promise<VerificationResult> {
  const drivingRecord = await fetchDrivingRecordFromDMV(licenseNumber, state);

  const violations: Violation[] = [];
  const twoYearsAgo = Math.floor(Date.now() / 1000) - TWO_YEARS_SECONDS;

  for (const ticket of drivingRecord.tickets) {
    if (ticket.movingViolation) {
      violations.push({
        reason: ticket.reason,
        timestamp: ticket.dateUnix,
      });
    }
  }

  const hasRecentViolation = violations.some((v) => v.timestamp >= twoYearsAgo);
  const isEligible = !hasRecentViolation;

  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const wallet = new ethers.Wallet(ownerPrivateKey, provider);
  const contract = new ethers.Contract(contractAddress, contractABI, wallet);

  const tx = await contract.submitDrivingRecord(
    driverAddress,
    violations,
    Math.floor(Date.now() / 1000)
  );
  await tx.wait();

  console.log(
    `Driver ${driverAddress} is ${isEligible ? 'eligible' : 'ineligible'} for NobleRide`
  );

  return { isEligible, violations, driverAddress };
}

async function fetchDrivingRecordFromDMV(
  licenseNumber: string,
  state: string
): Promise<DrivingRecord> {
  // Production: integrate with Checkr, GoodHire, Sterling, or state DMV API
  // This is a mock implementation for development
  console.log(`Fetching DMV record for license ${licenseNumber} in ${state}`);

  return {
    tickets: [],
  };
}

export async function verifyDriverBackground(
  driverAddress: string,
  backgroundCheckHash: string,
  approved: boolean,
  contractAddress: string,
  contractABI: ethers.InterfaceAbi,
  rpcUrl: string,
  ownerPrivateKey: string
): Promise<void> {
  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const wallet = new ethers.Wallet(ownerPrivateKey, provider);
  const contract = new ethers.Contract(contractAddress, contractABI, wallet);

  const tx = await contract.verifyDriver(driverAddress, approved, backgroundCheckHash);
  await tx.wait();

  console.log(
    `Driver ${driverAddress} ${approved ? 'verified' : 'rejected'}`
  );
}
