import { useState, useEffect, useCallback } from 'react';
import { ethers } from 'ethers';

interface Driver {
  address: string;
  name: string;
  isWoman: boolean;
  completedRides: number;
}

interface NobleRideAppProps {
  contractAddress: string;
  contractABI: ethers.InterfaceAbi;
}

export function NobleRideApp({ contractAddress, contractABI }: NobleRideAppProps) {
  const [contract, setContract] = useState<ethers.Contract | null>(null);
  const [eligibleDrivers, setEligibleDrivers] = useState<Driver[]>([]);
  const [preferWomen, setPreferWomen] = useState(false);
  const [ridePrice, setRidePrice] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadEligibleDrivers = useCallback(
    async (nobleRide: ethers.Contract) => {
      try {
        const verifiedEventFilter = nobleRide.filters.DriverVerified();
        const events = await nobleRide.queryFilter(verifiedEventFilter);
        const driverAddresses = [...new Set(events.map((e) => e.args?.driver))];

        const driverData = await Promise.all(
          driverAddresses.map(async (addr) => {
            const driver = await nobleRide.drivers(addr);
            return {
              address: addr,
              isWoman: driver.isWoman,
              name: driver.name,
              completedRides: Number(driver.completedRides),
            };
          })
        );

        let filtered = driverData;
        if (preferWomen) {
          filtered = driverData.filter((d) => d.isWoman === true);
        }
        setEligibleDrivers(filtered);
      } catch (err) {
        setError('Failed to load drivers');
        console.error(err);
      }
    },
    [preferWomen]
  );

  const loadContract = useCallback(async () => {
    if (!window.ethereum) {
      setError('Please install MetaMask');
      return;
    }

    try {
      const provider = new ethers.BrowserProvider(window.ethereum);
      const signer = await provider.getSigner();
      const nobleRide = new ethers.Contract(contractAddress, contractABI, signer);
      setContract(nobleRide);
      await loadEligibleDrivers(nobleRide);
    } catch (err) {
      setError('Failed to connect wallet');
      console.error(err);
    }
  }, [contractAddress, contractABI, loadEligibleDrivers]);

  useEffect(() => {
    loadContract();
  }, [loadContract]);

  useEffect(() => {
    if (contract) {
      loadEligibleDrivers(contract);
    }
  }, [contract, preferWomen, loadEligibleDrivers]);

  const requestRide = async () => {
    if (!contract || !ridePrice) return;

    setLoading(true);
    setError(null);

    try {
      const priceWei = ethers.parseEther(ridePrice);
      const tx = await contract.requestRide(priceWei, { value: priceWei });
      await tx.wait();
      setRidePrice('');
      alert('Ride requested! Matching with eligible driver...');
    } catch (err) {
      setError('Failed to request ride');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="noble-ride-app">
      <header>
        <h1>NobleRide.io</h1>
        <p className="tagline">Safe, Vetted Drivers</p>
      </header>

      <section className="requirements">
        <h2>Driver Requirements</h2>
        <ul>
          <li>No speeding tickets or moving violations in the last 2 consecutive years</li>
          <li>Background check verified on-chain</li>
          <li>Identity verification through DMV records</li>
        </ul>
      </section>

      {error && <div className="error">{error}</div>}

      <section className="preferences">
        <label>
          <input
            type="checkbox"
            checked={preferWomen}
            onChange={(e) => setPreferWomen(e.target.checked)}
          />
          Prefer women drivers (if available)
        </label>
      </section>

      <section className="drivers">
        <h3>Available Drivers ({eligibleDrivers.length})</h3>
        {eligibleDrivers.length === 0 ? (
          <p>No verified drivers available{preferWomen ? ' matching your preference' : ''}</p>
        ) : (
          <ul>
            {eligibleDrivers.map((d) => (
              <li key={d.address}>
                <span className="driver-name">{d.name}</span>
                <span className="driver-gender">{d.isWoman ? '(W)' : '(M)'}</span>
                <span className="driver-rides">{d.completedRides} rides</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="request-ride">
        <h3>Request a Ride</h3>
        <div className="form-group">
          <input
            type="text"
            placeholder="Price in ETH (e.g., 0.01)"
            value={ridePrice}
            onChange={(e) => setRidePrice(e.target.value)}
            disabled={loading}
          />
          <button onClick={requestRide} disabled={loading || !ridePrice}>
            {loading ? 'Requesting...' : 'Request Ride'}
          </button>
        </div>
      </section>
    </div>
  );
}

export default NobleRideApp;
