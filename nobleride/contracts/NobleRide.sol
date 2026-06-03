// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract NobleRide {
    address public owner;
    mapping(address => Driver) public drivers;
    mapping(uint256 => Ride) public rides;
    uint256 public rideCounter;

    enum DriverStatus { Unregistered, PendingRecordCheck, RecordFailed, PendingBackground, Verified, Rejected }
    enum RideStatus { Pending, Active, Completed, Cancelled }

    struct Violation {
        string reason;
        uint256 timestamp;
    }

    struct DrivingRecord {
        Violation[] violations;
        uint256 lastChecked;
        bool twoYearClean;
    }

    struct Driver {
        string name;
        DriverStatus status;
        bool isWoman;
        DrivingRecord drivingRecord;
        string backgroundHash;
        uint256 completedRides;
        uint256 ratingSum;
        uint256 ratingCount;
    }

    struct Ride {
        address passenger;
        address driver;
        uint256 price;
        RideStatus status;
        uint256 timestamp;
    }

    event DriverRegistered(address indexed driver, string name);
    event DrivingRecordSubmitted(address indexed driver, uint256 violationCount);
    event DriverRecordCleared(address indexed driver);
    event DriverVerified(address indexed driver);
    event RideRequested(uint256 rideId, address passenger, uint256 price);
    event RideAccepted(uint256 rideId, address driver);
    event RideCompleted(uint256 rideId);

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function registerDriver(string memory _name, bool _isWoman) external {
        require(drivers[msg.sender].status == DriverStatus.Unregistered, "Already registered");
        drivers[msg.sender] = Driver({
            name: _name,
            status: DriverStatus.PendingRecordCheck,
            isWoman: _isWoman,
            drivingRecord: DrivingRecord({violations: new Violation[](0), lastChecked: 0, twoYearClean: false}),
            backgroundHash: "",
            completedRides: 0,
            ratingSum: 0,
            ratingCount: 0
        });
        emit DriverRegistered(msg.sender, _name);
    }

    function submitDrivingRecord(
        address _driver,
        Violation[] memory _violations,
        uint256 _lastChecked
    ) external onlyOwner {
        Driver storage d = drivers[_driver];
        require(d.status == DriverStatus.PendingRecordCheck, "Driver not pending record check");

        delete d.drivingRecord.violations;
        for (uint i = 0; i < _violations.length; i++) {
            d.drivingRecord.violations.push(_violations[i]);
        }
        d.drivingRecord.lastChecked = _lastChecked;

        bool isClean = true;
        uint256 twoYearsAgo = block.timestamp - 730 days;

        for (uint i = 0; i < _violations.length; i++) {
            if (_violations[i].timestamp >= twoYearsAgo) {
                isClean = false;
                break;
            }
        }

        if (isClean && _violations.length == 0) {
            d.drivingRecord.twoYearClean = true;
            d.status = DriverStatus.PendingBackground;
            emit DriverRecordCleared(_driver);
        } else {
            d.status = DriverStatus.RecordFailed;
        }

        emit DrivingRecordSubmitted(_driver, _violations.length);
    }

    function verifyDriver(address _driver, bool _approved, string memory _backgroundHash) external onlyOwner {
        Driver storage d = drivers[_driver];
        require(d.status == DriverStatus.PendingBackground, "Driver not ready for verification");
        require(d.drivingRecord.twoYearClean == true, "Driver does not meet 2-year clean record");

        if (_approved) {
            d.backgroundHash = _backgroundHash;
            d.status = DriverStatus.Verified;
            emit DriverVerified(_driver);
        } else {
            d.status = DriverStatus.Rejected;
        }
    }

    function requestRide(uint256 _price) external payable returns (uint256 rideId) {
        require(msg.value == _price, "Send exact price");
        rideId = rideCounter++;
        rides[rideId] = Ride({
            passenger: msg.sender,
            driver: address(0),
            price: _price,
            status: RideStatus.Pending,
            timestamp: block.timestamp
        });
        emit RideRequested(rideId, msg.sender, _price);
    }

    function acceptRide(uint256 _rideId) external {
        Ride storage r = rides[_rideId];
        require(r.status == RideStatus.Pending, "Ride not pending");
        require(drivers[msg.sender].status == DriverStatus.Verified, "Driver not verified");
        r.driver = msg.sender;
        r.status = RideStatus.Active;
        emit RideAccepted(_rideId, msg.sender);
    }

    function completeRide(uint256 _rideId) external {
        Ride storage r = rides[_rideId];
        require(r.status == RideStatus.Active, "Ride not active");
        require(msg.sender == r.passenger || msg.sender == r.driver, "Not participant");
        r.status = RideStatus.Completed;
        payable(r.driver).transfer(r.price);
        drivers[r.driver].completedRides++;
        emit RideCompleted(_rideId);
    }

    function getDriverStatus(address _driver) external view returns (DriverStatus) {
        return drivers[_driver].status;
    }

    function getDriverRating(address _driver) external view returns (uint256 avgRating, uint256 totalRides) {
        Driver storage d = drivers[_driver];
        if (d.ratingCount == 0) return (0, d.completedRides);
        return (d.ratingSum / d.ratingCount, d.completedRides);
    }
}
