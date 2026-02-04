// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MassachusettsBuildingPermits
 * @author NoblePort ETF - Building Permits Module
 * @notice MA-780-CMR compliant building permit management for Massachusetts
 * @dev Production-ready contract with:
 *      - Primary permits + trade sub-permits (electrical, plumbing, gas, mechanical)
 *      - Sequential approval workflow (zoning → building → trades)
 *      - USDC fee payments with full audit trail
 *      - Role-segmented authority model with license verification
 *      - Immutable plan anchoring (IPFS/Arweave)
 *      - Town-scoped jurisdiction permissions
 *
 * Compliance: Massachusetts State Building Code 780 CMR (9th Edition)
 * Reference: https://www.mass.gov/orgs/board-of-building-regulations-and-standards
 */

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract MassachusettsBuildingPermits is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // ============ 780 CMR Code Reference ============

    string public constant MA_BUILDING_CODE_VERSION = "780 CMR 9th Edition (2017, as amended)";
    string public constant COMPLIANCE_REFERENCE = "MGL c.143, ss.93-100";

    // ============ Role Hierarchy (Authority Model) ============

    // State-level roles
    bytes32 public constant STATE_BUILDING_COMMISSIONER = keccak256("STATE_BUILDING_COMMISSIONER");
    bytes32 public constant STATE_FIRE_MARSHAL = keccak256("STATE_FIRE_MARSHAL");

    // Municipality roles (town-scoped)
    bytes32 public constant BUILDING_OFFICIAL = keccak256("BUILDING_OFFICIAL");      // Can approve building permits
    bytes32 public constant ELECTRICAL_INSPECTOR = keccak256("ELECTRICAL_INSPECTOR"); // Trade-specific
    bytes32 public constant PLUMBING_INSPECTOR = keccak256("PLUMBING_INSPECTOR");     // Trade-specific
    bytes32 public constant GAS_INSPECTOR = keccak256("GAS_INSPECTOR");               // Trade-specific
    bytes32 public constant MECHANICAL_INSPECTOR = keccak256("MECHANICAL_INSPECTOR"); // Trade-specific (HVAC)
    bytes32 public constant FIRE_INSPECTOR = keccak256("FIRE_INSPECTOR");             // Fire protection
    bytes32 public constant ZONING_OFFICER = keccak256("ZONING_OFFICER");             // Zoning approval
    bytes32 public constant MUNICIPAL_CLERK = keccak256("MUNICIPAL_CLERK");           // Fee collection/audit

    // Licensed professionals
    bytes32 public constant LICENSED_CONTRACTOR = keccak256("LICENSED_CONTRACTOR");
    bytes32 public constant LICENSED_ELECTRICIAN = keccak256("LICENSED_ELECTRICIAN");
    bytes32 public constant LICENSED_PLUMBER = keccak256("LICENSED_PLUMBER");
    bytes32 public constant LICENSED_GAS_FITTER = keccak256("LICENSED_GAS_FITTER");

    // ============ Enums ============

    enum PrimaryPermitType {
        RESIDENTIAL_NEW_CONSTRUCTION,    // 1-2 family, <35ft height
        RESIDENTIAL_ADDITION,            // Additions to existing
        RESIDENTIAL_RENOVATION,          // Alterations
        MULTIFAMILY_NEW_CONSTRUCTION,    // 3+ units
        COMMERCIAL_NEW_CONSTRUCTION,     // Use groups A, B, E, M
        COMMERCIAL_TENANT_FITOUT,        // Interior buildout
        INDUSTRIAL_NEW_CONSTRUCTION,     // Use groups F, H, S
        MIXED_USE,                       // Combined residential/commercial
        DEMOLITION_FULL,                 // Complete demolition
        DEMOLITION_PARTIAL,              // Partial demolition
        FOUNDATION_ONLY,                 // Foundation permit
        SHELL_ONLY,                      // Core/shell only
        ACCESSORY_DWELLING_UNIT,         // ADU per Housing Choice Act
        DECK_PORCH,                      // Exterior structures
        SWIMMING_POOL,                   // Pool installation
        SOLAR_PV,                        // Solar/PV per 780 CMR 115.R10
        TEMPORARY_STRUCTURE,             // Tents, temp buildings
        CHANGE_OF_USE                    // Use/occupancy change
    }

    enum TradePermitType {
        ELECTRICAL,          // Per 527 CMR
        PLUMBING,           // Per 248 CMR
        GAS,                // Per 248 CMR
        MECHANICAL_HVAC,    // Per 780 CMR Chapter 12
        FIRE_SUPPRESSION,   // Sprinkler systems
        FIRE_ALARM,         // Fire alarm systems
        LOW_VOLTAGE,        // Security, data, telecom
        ELEVATOR,           // Per 524 CMR
        FUEL_STORAGE        // Underground/aboveground tanks
    }

    enum ApprovalPhase {
        DRAFT,                    // Application created
        ZONING_REVIEW,            // Awaiting zoning clearance
        ZONING_APPROVED,          // Zoning cleared
        ZONING_VARIANCE_REQUIRED, // Needs ZBA variance
        PLAN_REVIEW,              // Technical plan review
        PLAN_CORRECTIONS_NEEDED,  // Plans need revision
        PLAN_APPROVED,            // Plans approved, pending fees
        FEES_PENDING,             // Awaiting fee payment
        FEES_PAID,                // All fees paid
        PERMIT_ISSUED,            // Permit card issued
        CONSTRUCTION_ACTIVE,      // Work in progress
        INSPECTION_REQUIRED,      // Inspection needed
        INSPECTION_FAILED,        // Failed inspection
        INSPECTION_PASSED,        // Passed inspection
        TRADES_PENDING,           // Awaiting trade permits
        FINAL_INSPECTION,         // Final inspection phase
        CO_PENDING,               // Awaiting C/O
        COMPLETED,                // Certificate of Occupancy issued
        EXPIRED,                  // Permit expired (180 days no activity)
        REVOKED,                  // Permit revoked
        VOIDED,                   // Permit voided (refund eligible)
        SUSPENDED                 // Permit suspended (stop work)
    }

    enum InspectionCategory {
        // Building inspections
        FOOTING_FOUNDATION,
        FOUNDATION_WATERPROOFING,
        ROUGH_FRAMING,
        SHEATHING,
        INSULATION_ENERGY,       // Per 780 CMR Chapter 13 (IECC)
        FIRE_BLOCKING,
        FINAL_BUILDING,
        // Trade inspections (must be by licensed trade inspector)
        ELECTRICAL_ROUGH,
        ELECTRICAL_FINAL,
        PLUMBING_ROUGH,
        PLUMBING_FINAL,
        PLUMBING_WATER_TEST,
        GAS_ROUGH,
        GAS_FINAL,
        GAS_PRESSURE_TEST,
        MECHANICAL_ROUGH,
        MECHANICAL_FINAL,
        FIRE_SUPPRESSION_ROUGH,
        FIRE_SUPPRESSION_FINAL,
        FIRE_ALARM,
        // Final
        CERTIFICATE_OF_OCCUPANCY
    }

    // ============ Structs ============

    struct Municipality {
        bytes32 id;
        string name;
        string maCounty;              // One of 14 MA counties
        uint16 townCode;              // MA DOR town code (001-351)
        address treasury;             // USDC collection address
        address buildingDepartment;   // Primary contact
        bool acceptsOnlinePermits;
        bool isActive;
        uint256 totalRevenue;         // Total fees collected (6 decimals)
        uint256 permitsIssued;
        uint256 createdAt;
    }

    struct JurisdictionGrant {
        bytes32 municipalityId;
        bytes32 role;
        uint256 grantedAt;
        uint256 expiresAt;            // 0 = no expiry
        bool isActive;
    }

    struct License {
        address holder;
        string licenseNumber;
        string licenseType;           // CSL, HIC, Master Electrician, etc.
        string ensName;               // ENS DID for verification
        bytes32 issuingAuthority;     // State board that issued
        uint256 issuedAt;
        uint256 expiresAt;
        bool isActive;
        bool isSuspended;
    }

    struct PropertyRecord {
        string streetAddress;
        string unit;
        string city;
        string zipCode;
        bytes32 municipalityId;
        string parcelId;              // Assessor's map-lot
        string zoningDistrict;        // R1, R2, B1, I1, etc.
        string floodZone;             // FEMA flood zone if applicable
        bool isHistoricDistrict;
        bool requiresHDCApproval;     // Historic District Commission
    }

    struct StampedPlanSet {
        string plansCID;              // IPFS/Arweave CID - IMMUTABLE after lock
        string specsDocCID;           // Specifications CID
        string structuralCalcsCID;    // Structural calculations CID
        string energyComplianceCID;   // REScheck/COMcheck CID
        address stampedBy;            // Licensed architect/engineer
        string peLicenseNumber;       // PE/RA license number
        uint256 stampedAt;
        bool isLocked;                // Once true, cannot be modified
        uint256 lockedAt;
    }

    struct PlanAmendment {
        uint256 amendmentNumber;
        string previousCID;
        string newCID;
        string reason;
        address approvedBy;
        uint256 approvedAt;
    }

    struct FeeScheduleEntry {
        PrimaryPermitType permitType;
        uint256 baseFee;              // 6 decimals (USDC)
        uint256 perSqFtFee;           // 6 decimals per sq ft
        uint256 planReviewPercent;    // Basis points (6500 = 65%)
        uint256 minimumFee;           // 6 decimals
        uint256 maximumFee;           // 6 decimals (0 = no max)
    }

    struct TradeFeeEntry {
        TradePermitType tradeType;
        uint256 baseFee;              // 6 decimals
        uint256 perFixtureFee;        // Per outlet/fixture
        uint256 minimumFee;
    }

    struct PaymentRecord {
        uint256 paymentId;
        uint256 permitId;
        uint256 amount;               // 6 decimals
        string paymentType;           // APPLICATION, PERMIT, TRADE, INSPECTION
        bytes32 receiptHash;          // Keccak256 of receipt data
        address paidBy;
        uint256 paidAt;
        bool isRefunded;
        uint256 refundedAt;
        string refundReason;
    }

    struct PrimaryPermit {
        uint256 permitId;
        bytes32 municipalityId;
        PrimaryPermitType permitType;
        ApprovalPhase phase;
        PropertyRecord property;

        // Applicant info
        address applicant;
        address propertyOwner;
        string contractorLicense;     // Required for most work

        // Project details
        string projectDescription;
        uint256 estimatedCost;        // 6 decimals
        uint256 grossSquareFootage;
        uint8 numberOfStories;
        string useGroup;              // A, B, E, F, H, I, M, R, S, U per 780 CMR
        string constructionType;      // I-A through V-B

        // Stamped plans (immutable after approval)
        StampedPlanSet plans;
        PlanAmendment[] amendments;

        // Fees
        uint256 applicationFee;
        uint256 permitFee;
        uint256 totalPaid;

        // Timestamps
        uint256 submittedAt;
        uint256 zoningApprovedAt;
        uint256 planApprovedAt;
        uint256 permitIssuedAt;
        uint256 expiresAt;
        uint256 completedAt;

        // Linked permits
        uint256[] tradePermitIds;
        bool requiresTradePermits;

        // State review
        bool requiresStateReview;     // Projects >$50M or special hazards
        bool stateApproved;
    }

    struct TradePermit {
        uint256 tradePermitId;
        uint256 parentPermitId;       // Links to primary permit
        TradePermitType tradeType;
        ApprovalPhase phase;

        // Licensed tradesperson
        address licensedTradesperson;
        string tradePersonLicense;

        // Scope
        string workDescription;
        uint256 fixtureCount;         // Outlets, fixtures, BTU, etc.
        uint256 estimatedCost;

        // Fees
        uint256 permitFee;
        uint256 totalPaid;

        // Timestamps
        uint256 submittedAt;
        uint256 approvedAt;
        uint256 expiresAt;
        uint256 completedAt;

        // Inspector assignment
        address assignedInspector;
    }

    struct Inspection {
        uint256 inspectionId;
        uint256 permitId;
        bool isTradePermit;           // true = trade permit, false = primary
        InspectionCategory category;

        address scheduledBy;
        address assignedInspector;
        uint256 scheduledDate;
        uint256 completedDate;

        bool passed;
        string resultCode;            // PASS, FAIL, PARTIAL, REINSPECT
        string notes;
        string[] photoCIDs;           // IPFS CIDs of inspection photos

        // For failed inspections
        string[] corrections;
        uint256 reinspectionDeadline;
    }

    struct CertificateOfOccupancy {
        uint256 coId;
        uint256 permitId;
        bytes32 municipalityId;
        string coNumber;              // Official C/O number
        string occupancyType;         // Use group
        uint256 maxOccupancy;
        bool isTemporary;
        uint256 temporaryExpiresAt;
        address issuedBy;
        uint256 issuedAt;
        string coCID;                 // IPFS CID of signed C/O document
    }

    // ============ State Variables ============

    // USDC token for payments (Ethereum mainnet: 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)
    IERC20 public immutable usdc;

    // Counters
    uint256 private _permitIdCounter = 1;
    uint256 private _tradePermitIdCounter = 1;
    uint256 private _inspectionIdCounter = 1;
    uint256 private _paymentIdCounter = 1;
    uint256 private _coIdCounter = 1;

    // State treasury
    address public stateTreasury;
    uint256 public stateFeePercent = 500;  // 5% to state (basis points)

    // Permit validity periods
    uint256 public constant PERMIT_VALIDITY_PERIOD = 365 days;
    uint256 public constant PERMIT_INACTIVITY_EXPIRY = 180 days;
    uint256 public constant MAX_EXTENSION_PERIOD = 180 days;

    // State review threshold (per 780 CMR 107.1.1)
    uint256 public stateReviewThreshold = 50_000_000 * 10**6; // $50M in USDC decimals

    // ============ Mappings ============

    // Municipality registry
    mapping(bytes32 => Municipality) public municipalities;
    bytes32[] public municipalityList;

    // Jurisdiction grants (address => municipalityId => role => grant)
    mapping(address => mapping(bytes32 => mapping(bytes32 => JurisdictionGrant))) public jurisdictionGrants;

    // License registry
    mapping(address => License) public licenses;
    mapping(string => address) public licenseNumberToAddress;

    // Permits
    mapping(uint256 => PrimaryPermit) public permits;
    mapping(uint256 => TradePermit) public tradePermits;
    mapping(uint256 => Inspection[]) public permitInspections;
    mapping(uint256 => PaymentRecord[]) public permitPayments;
    mapping(uint256 => CertificateOfOccupancy) public certificatesOfOccupancy;

    // Fee schedules (municipalityId => permitType => fee entry)
    mapping(bytes32 => mapping(PrimaryPermitType => FeeScheduleEntry)) public feeSchedules;
    mapping(bytes32 => mapping(TradePermitType => TradeFeeEntry)) public tradeFeeSchedules;

    // Lookups
    mapping(address => uint256[]) public applicantPermits;
    mapping(bytes32 => uint256[]) public municipalityPermits;
    mapping(string => uint256[]) public parcelPermitHistory;  // All permits for a parcel

    // ============ Events ============

    event MunicipalityRegistered(bytes32 indexed id, string name, uint16 townCode);
    event MunicipalityUpdated(bytes32 indexed id);

    event JurisdictionGranted(address indexed official, bytes32 indexed municipalityId, bytes32 role);
    event JurisdictionRevoked(address indexed official, bytes32 indexed municipalityId, bytes32 role);

    event LicenseRegistered(address indexed holder, string licenseNumber, string licenseType);
    event LicenseSuspended(address indexed holder, string reason);
    event LicenseReinstated(address indexed holder);

    event PermitApplicationSubmitted(uint256 indexed permitId, bytes32 indexed municipalityId, address indexed applicant);
    event PermitPhaseChanged(uint256 indexed permitId, ApprovalPhase previousPhase, ApprovalPhase newPhase, address changedBy);
    event ZoningApproved(uint256 indexed permitId, address approvedBy);
    event ZoningVarianceRequired(uint256 indexed permitId, string reason);
    event PlansSubmitted(uint256 indexed permitId, string plansCID);
    event PlansLocked(uint256 indexed permitId, string plansCID, uint256 lockedAt);
    event PlanAmendmentApproved(uint256 indexed permitId, uint256 amendmentNumber, string newCID);
    event PermitApproved(uint256 indexed permitId, address approvedBy);
    event PermitIssued(uint256 indexed permitId, uint256 expiresAt);
    event PermitExtended(uint256 indexed permitId, uint256 newExpiresAt);
    event PermitSuspended(uint256 indexed permitId, string reason);
    event PermitRevoked(uint256 indexed permitId, string reason);
    event PermitVoided(uint256 indexed permitId, uint256 refundAmount);

    event TradePermitSubmitted(uint256 indexed tradePermitId, uint256 indexed parentPermitId, TradePermitType tradeType);
    event TradePermitApproved(uint256 indexed tradePermitId, address approvedBy);
    event TradePermitCompleted(uint256 indexed tradePermitId);

    event InspectionScheduled(uint256 indexed inspectionId, uint256 indexed permitId, InspectionCategory category);
    event InspectionCompleted(uint256 indexed inspectionId, bool passed, string resultCode);
    event InspectionFailed(uint256 indexed inspectionId, string[] corrections);

    event PaymentReceived(uint256 indexed paymentId, uint256 indexed permitId, uint256 amount, string paymentType);
    event RefundIssued(uint256 indexed paymentId, uint256 amount, string reason);

    event CertificateOfOccupancyIssued(uint256 indexed coId, uint256 indexed permitId, string coNumber);

    event FeeScheduleUpdated(bytes32 indexed municipalityId, PrimaryPermitType permitType);
    event TradeFeeScheduleUpdated(bytes32 indexed municipalityId, TradePermitType tradeType);

    // ============ Modifiers ============

    modifier onlyStateOfficial() {
        require(
            hasRole(STATE_BUILDING_COMMISSIONER, msg.sender) ||
            hasRole(STATE_FIRE_MARSHAL, msg.sender) ||
            hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "Not a state official"
        );
        _;
    }

    modifier onlyJurisdiction(bytes32 _municipalityId, bytes32 _role) {
        require(
            _hasJurisdiction(msg.sender, _municipalityId, _role) ||
            hasRole(STATE_BUILDING_COMMISSIONER, msg.sender) ||
            hasRole(DEFAULT_ADMIN_ROLE, msg.sender),
            "No jurisdiction for this action"
        );
        _;
    }

    modifier onlyLicensed(bytes32 _licenseType) {
        require(
            licenses[msg.sender].isActive &&
            !licenses[msg.sender].isSuspended &&
            licenses[msg.sender].expiresAt > block.timestamp,
            "Valid license required"
        );
        _;
    }

    modifier permitExists(uint256 _permitId) {
        require(permits[_permitId].permitId != 0, "Permit not found");
        _;
    }

    modifier tradePermitExists(uint256 _tradePermitId) {
        require(tradePermits[_tradePermitId].tradePermitId != 0, "Trade permit not found");
        _;
    }

    // ============ Constructor ============

    constructor(address _usdc, address _stateTreasury) {
        require(_usdc != address(0), "Invalid USDC address");
        require(_stateTreasury != address(0), "Invalid state treasury");

        usdc = IERC20(_usdc);
        stateTreasury = _stateTreasury;

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(STATE_BUILDING_COMMISSIONER, msg.sender);
    }

    // ============ Jurisdiction Management ============

    function _hasJurisdiction(
        address _official,
        bytes32 _municipalityId,
        bytes32 _role
    ) internal view returns (bool) {
        JurisdictionGrant storage grant = jurisdictionGrants[_official][_municipalityId][_role];
        if (!grant.isActive) return false;
        if (grant.expiresAt != 0 && grant.expiresAt < block.timestamp) return false;
        return true;
    }

    /**
     * @notice Grant jurisdiction to an official for a specific municipality and role
     * @param _official Official's address
     * @param _municipalityId Municipality identifier
     * @param _role Role to grant (BUILDING_OFFICIAL, ELECTRICAL_INSPECTOR, etc.)
     * @param _expiresAt Expiration timestamp (0 = no expiry)
     */
    function grantJurisdiction(
        address _official,
        bytes32 _municipalityId,
        bytes32 _role,
        uint256 _expiresAt
    ) external onlyStateOfficial {
        require(_official != address(0), "Invalid official address");
        require(municipalities[_municipalityId].isActive, "Municipality not active");

        jurisdictionGrants[_official][_municipalityId][_role] = JurisdictionGrant({
            municipalityId: _municipalityId,
            role: _role,
            grantedAt: block.timestamp,
            expiresAt: _expiresAt,
            isActive: true
        });

        emit JurisdictionGranted(_official, _municipalityId, _role);
    }

    /**
     * @notice Revoke jurisdiction from an official
     */
    function revokeJurisdiction(
        address _official,
        bytes32 _municipalityId,
        bytes32 _role
    ) external onlyStateOfficial {
        jurisdictionGrants[_official][_municipalityId][_role].isActive = false;
        emit JurisdictionRevoked(_official, _municipalityId, _role);
    }

    // ============ Municipality Management ============

    /**
     * @notice Register a Massachusetts municipality
     * @param _name Municipality name
     * @param _county MA county name
     * @param _townCode MA DOR town code (1-351)
     * @param _treasury USDC treasury address
     */
    function registerMunicipality(
        string calldata _name,
        string calldata _county,
        uint16 _townCode,
        address _treasury
    ) external onlyStateOfficial {
        require(_treasury != address(0), "Invalid treasury");
        require(_townCode >= 1 && _townCode <= 351, "Invalid MA town code");

        bytes32 id = keccak256(abi.encodePacked(_name, _townCode));
        require(municipalities[id].createdAt == 0, "Municipality exists");

        municipalities[id] = Municipality({
            id: id,
            name: _name,
            maCounty: _county,
            townCode: _townCode,
            treasury: _treasury,
            buildingDepartment: _treasury,
            acceptsOnlinePermits: true,
            isActive: true,
            totalRevenue: 0,
            permitsIssued: 0,
            createdAt: block.timestamp
        });

        municipalityList.push(id);
        emit MunicipalityRegistered(id, _name, _townCode);
    }

    /**
     * @notice Update municipality settings
     */
    function updateMunicipality(
        bytes32 _id,
        address _treasury,
        address _buildingDepartment,
        bool _acceptsOnlinePermits,
        bool _isActive
    ) external onlyStateOfficial {
        require(municipalities[_id].createdAt != 0, "Municipality not found");

        Municipality storage m = municipalities[_id];
        m.treasury = _treasury;
        m.buildingDepartment = _buildingDepartment;
        m.acceptsOnlinePermits = _acceptsOnlinePermits;
        m.isActive = _isActive;

        emit MunicipalityUpdated(_id);
    }

    // ============ License Registry ============

    /**
     * @notice Register a professional license
     * @param _holder License holder's wallet
     * @param _licenseNumber Official license number
     * @param _licenseType Type (CSL, HIC, Master Electrician, Journeyman Plumber, etc.)
     * @param _ensName ENS name for DID verification
     * @param _issuingAuthority Issuing state board
     * @param _expiresAt License expiration
     */
    function registerLicense(
        address _holder,
        string calldata _licenseNumber,
        string calldata _licenseType,
        string calldata _ensName,
        bytes32 _issuingAuthority,
        uint256 _expiresAt
    ) external onlyStateOfficial {
        require(_holder != address(0), "Invalid holder");
        require(licenseNumberToAddress[_licenseNumber] == address(0), "License number exists");

        licenses[_holder] = License({
            holder: _holder,
            licenseNumber: _licenseNumber,
            licenseType: _licenseType,
            ensName: _ensName,
            issuingAuthority: _issuingAuthority,
            issuedAt: block.timestamp,
            expiresAt: _expiresAt,
            isActive: true,
            isSuspended: false
        });

        licenseNumberToAddress[_licenseNumber] = _holder;

        // Grant appropriate role based on license type
        if (keccak256(bytes(_licenseType)) == keccak256("CSL") ||
            keccak256(bytes(_licenseType)) == keccak256("HIC")) {
            _grantRole(LICENSED_CONTRACTOR, _holder);
        } else if (keccak256(bytes(_licenseType)) == keccak256("Master Electrician") ||
                   keccak256(bytes(_licenseType)) == keccak256("Journeyman Electrician")) {
            _grantRole(LICENSED_ELECTRICIAN, _holder);
        } else if (keccak256(bytes(_licenseType)) == keccak256("Master Plumber") ||
                   keccak256(bytes(_licenseType)) == keccak256("Journeyman Plumber")) {
            _grantRole(LICENSED_PLUMBER, _holder);
        } else if (keccak256(bytes(_licenseType)) == keccak256("Gas Fitter")) {
            _grantRole(LICENSED_GAS_FITTER, _holder);
        }

        emit LicenseRegistered(_holder, _licenseNumber, _licenseType);
    }

    /**
     * @notice Suspend a license
     */
    function suspendLicense(address _holder, string calldata _reason) external onlyStateOfficial {
        licenses[_holder].isSuspended = true;
        emit LicenseSuspended(_holder, _reason);
    }

    /**
     * @notice Reinstate a suspended license
     */
    function reinstateLicense(address _holder) external onlyStateOfficial {
        licenses[_holder].isSuspended = false;
        emit LicenseReinstated(_holder);
    }

    // ============ Fee Schedule Management ============

    /**
     * @notice Set fee schedule for a municipality
     */
    function setFeeSchedule(
        bytes32 _municipalityId,
        PrimaryPermitType _permitType,
        uint256 _baseFee,
        uint256 _perSqFtFee,
        uint256 _planReviewPercent,
        uint256 _minimumFee,
        uint256 _maximumFee
    ) external onlyJurisdiction(_municipalityId, MUNICIPAL_CLERK) {
        feeSchedules[_municipalityId][_permitType] = FeeScheduleEntry({
            permitType: _permitType,
            baseFee: _baseFee,
            perSqFtFee: _perSqFtFee,
            planReviewPercent: _planReviewPercent,
            minimumFee: _minimumFee,
            maximumFee: _maximumFee
        });

        emit FeeScheduleUpdated(_municipalityId, _permitType);
    }

    /**
     * @notice Set trade permit fee schedule
     */
    function setTradeFeeSchedule(
        bytes32 _municipalityId,
        TradePermitType _tradeType,
        uint256 _baseFee,
        uint256 _perFixtureFee,
        uint256 _minimumFee
    ) external onlyJurisdiction(_municipalityId, MUNICIPAL_CLERK) {
        tradeFeeSchedules[_municipalityId][_tradeType] = TradeFeeEntry({
            tradeType: _tradeType,
            baseFee: _baseFee,
            perFixtureFee: _perFixtureFee,
            minimumFee: _minimumFee
        });

        emit TradeFeeScheduleUpdated(_municipalityId, _tradeType);
    }

    // ============ Primary Permit Application ============

    /**
     * @notice Submit a new building permit application
     * @dev Sequential workflow: Zoning → Plan Review → Approval → Fee Payment → Issuance
     */
    function submitPermitApplication(
        bytes32 _municipalityId,
        PrimaryPermitType _permitType,
        PropertyRecord calldata _property,
        address _propertyOwner,
        string calldata _contractorLicense,
        string calldata _projectDescription,
        uint256 _estimatedCost,
        uint256 _grossSquareFootage,
        uint8 _numberOfStories,
        string calldata _useGroup,
        string calldata _constructionType
    ) external nonReentrant whenNotPaused returns (uint256) {
        require(municipalities[_municipalityId].isActive, "Municipality not active");
        require(municipalities[_municipalityId].acceptsOnlinePermits, "Online permits not accepted");
        require(_propertyOwner != address(0), "Invalid property owner");

        // Verify contractor license if required
        if (_permitType != PrimaryPermitType.DEMOLITION_FULL &&
            _permitType != PrimaryPermitType.DEMOLITION_PARTIAL) {
            address contractor = licenseNumberToAddress[_contractorLicense];
            require(
                licenses[contractor].isActive && !licenses[contractor].isSuspended,
                "Valid contractor license required"
            );
        }

        // Calculate application fee
        FeeScheduleEntry storage feeEntry = feeSchedules[_municipalityId][_permitType];
        uint256 applicationFee = _calculateApplicationFee(_municipalityId, _permitType);

        // Collect application fee
        require(usdc.balanceOf(msg.sender) >= applicationFee, "Insufficient USDC balance");
        _collectPayment(msg.sender, _municipalityId, applicationFee);

        uint256 permitId = _permitIdCounter++;

        permits[permitId].permitId = permitId;
        permits[permitId].municipalityId = _municipalityId;
        permits[permitId].permitType = _permitType;
        permits[permitId].phase = ApprovalPhase.ZONING_REVIEW;
        permits[permitId].property = _property;
        permits[permitId].applicant = msg.sender;
        permits[permitId].propertyOwner = _propertyOwner;
        permits[permitId].contractorLicense = _contractorLicense;
        permits[permitId].projectDescription = _projectDescription;
        permits[permitId].estimatedCost = _estimatedCost;
        permits[permitId].grossSquareFootage = _grossSquareFootage;
        permits[permitId].numberOfStories = _numberOfStories;
        permits[permitId].useGroup = _useGroup;
        permits[permitId].constructionType = _constructionType;
        permits[permitId].applicationFee = applicationFee;
        permits[permitId].totalPaid = applicationFee;
        permits[permitId].submittedAt = block.timestamp;
        permits[permitId].requiresStateReview = _estimatedCost >= stateReviewThreshold;
        permits[permitId].requiresTradePermits = _requiresTradePermits(_permitType);

        // Record payment
        _recordPayment(permitId, applicationFee, "APPLICATION");

        // Add to lookups
        applicantPermits[msg.sender].push(permitId);
        municipalityPermits[_municipalityId].push(permitId);
        parcelPermitHistory[_property.parcelId].push(permitId);

        emit PermitApplicationSubmitted(permitId, _municipalityId, msg.sender);
        emit PermitPhaseChanged(permitId, ApprovalPhase.DRAFT, ApprovalPhase.ZONING_REVIEW, msg.sender);

        return permitId;
    }

    // ============ Zoning Review ============

    /**
     * @notice Approve zoning for a permit application
     */
    function approveZoning(uint256 _permitId)
        external
        permitExists(_permitId)
        onlyJurisdiction(permits[_permitId].municipalityId, ZONING_OFFICER)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(permit.phase == ApprovalPhase.ZONING_REVIEW, "Not in zoning review");

        ApprovalPhase previousPhase = permit.phase;
        permit.phase = ApprovalPhase.ZONING_APPROVED;
        permit.zoningApprovedAt = block.timestamp;

        emit ZoningApproved(_permitId, msg.sender);
        emit PermitPhaseChanged(_permitId, previousPhase, permit.phase, msg.sender);
    }

    /**
     * @notice Indicate zoning variance is required
     */
    function requireZoningVariance(uint256 _permitId, string calldata _reason)
        external
        permitExists(_permitId)
        onlyJurisdiction(permits[_permitId].municipalityId, ZONING_OFFICER)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(permit.phase == ApprovalPhase.ZONING_REVIEW, "Not in zoning review");

        permit.phase = ApprovalPhase.ZONING_VARIANCE_REQUIRED;

        emit ZoningVarianceRequired(_permitId, _reason);
        emit PermitPhaseChanged(_permitId, ApprovalPhase.ZONING_REVIEW, permit.phase, msg.sender);
    }

    // ============ Plan Submission & Locking ============

    /**
     * @notice Submit stamped construction plans
     * @dev Plans must be submitted after zoning approval
     * @param _permitId Permit identifier
     * @param _plansCID IPFS/Arweave CID of construction plans
     * @param _specsDocCID IPFS/Arweave CID of specifications
     * @param _structuralCalcsCID IPFS/Arweave CID of structural calculations
     * @param _energyComplianceCID IPFS/Arweave CID of energy compliance docs
     * @param _peLicenseNumber License number of stamping PE/RA
     */
    function submitPlans(
        uint256 _permitId,
        string calldata _plansCID,
        string calldata _specsDocCID,
        string calldata _structuralCalcsCID,
        string calldata _energyComplianceCID,
        string calldata _peLicenseNumber
    ) external permitExists(_permitId) {
        PrimaryPermit storage permit = permits[_permitId];
        require(
            permit.phase == ApprovalPhase.ZONING_APPROVED ||
            permit.phase == ApprovalPhase.PLAN_CORRECTIONS_NEEDED,
            "Cannot submit plans in current phase"
        );
        require(
            permit.applicant == msg.sender || permit.propertyOwner == msg.sender,
            "Not authorized"
        );
        require(!permit.plans.isLocked, "Plans already locked");
        require(bytes(_plansCID).length > 0, "Plans CID required");

        permit.plans = StampedPlanSet({
            plansCID: _plansCID,
            specsDocCID: _specsDocCID,
            structuralCalcsCID: _structuralCalcsCID,
            energyComplianceCID: _energyComplianceCID,
            stampedBy: msg.sender,
            peLicenseNumber: _peLicenseNumber,
            stampedAt: block.timestamp,
            isLocked: false,
            lockedAt: 0
        });

        permit.phase = ApprovalPhase.PLAN_REVIEW;

        emit PlansSubmitted(_permitId, _plansCID);
        emit PermitPhaseChanged(_permitId, ApprovalPhase.ZONING_APPROVED, permit.phase, msg.sender);
    }

    /**
     * @notice Request plan corrections
     */
    function requestPlanCorrections(uint256 _permitId, string calldata _corrections)
        external
        permitExists(_permitId)
        onlyJurisdiction(permits[_permitId].municipalityId, BUILDING_OFFICIAL)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(permit.phase == ApprovalPhase.PLAN_REVIEW, "Not in plan review");
        require(!permit.plans.isLocked, "Plans already locked");

        permit.phase = ApprovalPhase.PLAN_CORRECTIONS_NEEDED;

        emit PermitPhaseChanged(_permitId, ApprovalPhase.PLAN_REVIEW, permit.phase, msg.sender);
    }

    /**
     * @notice Approve plans and lock them (immutable after this)
     */
    function approvePlansAndLock(uint256 _permitId)
        external
        permitExists(_permitId)
        onlyJurisdiction(permits[_permitId].municipalityId, BUILDING_OFFICIAL)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(permit.phase == ApprovalPhase.PLAN_REVIEW, "Not in plan review");
        require(bytes(permit.plans.plansCID).length > 0, "No plans submitted");
        require(!permit.plans.isLocked, "Plans already locked");

        // Lock plans - IMMUTABLE after this point
        permit.plans.isLocked = true;
        permit.plans.lockedAt = block.timestamp;
        permit.planApprovedAt = block.timestamp;
        permit.phase = ApprovalPhase.PLAN_APPROVED;

        // Calculate permit fee
        permit.permitFee = _calculatePermitFee(
            permit.municipalityId,
            permit.permitType,
            permit.grossSquareFootage,
            permit.estimatedCost
        );

        permit.phase = ApprovalPhase.FEES_PENDING;

        emit PlansLocked(_permitId, permit.plans.plansCID, block.timestamp);
        emit PermitApproved(_permitId, msg.sender);
        emit PermitPhaseChanged(_permitId, ApprovalPhase.PLAN_REVIEW, permit.phase, msg.sender);
    }

    /**
     * @notice Approve a plan amendment (creates new CID, preserves history)
     * @dev Only allowed after permit issuance, requires building official approval
     */
    function approvePlanAmendment(
        uint256 _permitId,
        string calldata _newCID,
        string calldata _reason
    ) external permitExists(_permitId) onlyJurisdiction(permits[_permitId].municipalityId, BUILDING_OFFICIAL) {
        PrimaryPermit storage permit = permits[_permitId];
        require(
            permit.phase == ApprovalPhase.PERMIT_ISSUED ||
            permit.phase == ApprovalPhase.CONSTRUCTION_ACTIVE,
            "Cannot amend in current phase"
        );

        uint256 amendmentNumber = permit.amendments.length + 1;

        permit.amendments.push(PlanAmendment({
            amendmentNumber: amendmentNumber,
            previousCID: permit.plans.plansCID,
            newCID: _newCID,
            reason: _reason,
            approvedBy: msg.sender,
            approvedAt: block.timestamp
        }));

        // Update current CID but preserve history in amendments array
        permit.plans.plansCID = _newCID;
        permit.plans.lockedAt = block.timestamp;

        emit PlanAmendmentApproved(_permitId, amendmentNumber, _newCID);
    }

    // ============ Fee Payment ============

    /**
     * @notice Pay permit fees (after plan approval)
     */
    function payPermitFees(uint256 _permitId)
        external
        nonReentrant
        permitExists(_permitId)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(permit.phase == ApprovalPhase.FEES_PENDING, "Fees not pending");
        require(permit.permitFee > 0, "No fee calculated");

        uint256 remainingFee = permit.permitFee;
        require(usdc.balanceOf(msg.sender) >= remainingFee, "Insufficient USDC");

        _collectPayment(msg.sender, permit.municipalityId, remainingFee);
        permit.totalPaid += remainingFee;
        permit.phase = ApprovalPhase.FEES_PAID;

        _recordPayment(_permitId, remainingFee, "PERMIT");

        emit PaymentReceived(_paymentIdCounter - 1, _permitId, remainingFee, "PERMIT");
        emit PermitPhaseChanged(_permitId, ApprovalPhase.FEES_PENDING, permit.phase, msg.sender);
    }

    /**
     * @notice Issue permit after fees paid
     */
    function issuePermit(uint256 _permitId)
        external
        permitExists(_permitId)
        onlyJurisdiction(permits[_permitId].municipalityId, BUILDING_OFFICIAL)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(permit.phase == ApprovalPhase.FEES_PAID, "Fees not paid");
        require(permit.plans.isLocked, "Plans not locked");

        // State review check
        if (permit.requiresStateReview) {
            require(permit.stateApproved, "State approval required");
        }

        permit.phase = ApprovalPhase.PERMIT_ISSUED;
        permit.permitIssuedAt = block.timestamp;
        permit.expiresAt = block.timestamp + PERMIT_VALIDITY_PERIOD;

        municipalities[permit.municipalityId].permitsIssued++;

        emit PermitIssued(_permitId, permit.expiresAt);
        emit PermitPhaseChanged(_permitId, ApprovalPhase.FEES_PAID, permit.phase, msg.sender);
    }

    // ============ Trade Permits ============

    /**
     * @notice Submit a trade permit (electrical, plumbing, gas, mechanical)
     * @dev Trade permits require a valid parent building permit
     */
    function submitTradePermit(
        uint256 _parentPermitId,
        TradePermitType _tradeType,
        string calldata _workDescription,
        uint256 _fixtureCount,
        uint256 _estimatedCost
    ) external nonReentrant permitExists(_parentPermitId) returns (uint256) {
        PrimaryPermit storage parent = permits[_parentPermitId];
        require(
            parent.phase == ApprovalPhase.PERMIT_ISSUED ||
            parent.phase == ApprovalPhase.CONSTRUCTION_ACTIVE ||
            parent.phase == ApprovalPhase.TRADES_PENDING,
            "Parent permit not active"
        );

        // Verify tradesperson license
        bytes32 requiredRole = _getRequiredTradeRole(_tradeType);
        require(hasRole(requiredRole, msg.sender), "Trade license required");
        require(
            licenses[msg.sender].isActive && !licenses[msg.sender].isSuspended,
            "License not valid"
        );

        // Calculate and collect trade permit fee
        TradeFeeEntry storage feeEntry = tradeFeeSchedules[parent.municipalityId][_tradeType];
        uint256 fee = feeEntry.baseFee + (feeEntry.perFixtureFee * _fixtureCount);
        if (fee < feeEntry.minimumFee) fee = feeEntry.minimumFee;

        require(usdc.balanceOf(msg.sender) >= fee, "Insufficient USDC");
        _collectPayment(msg.sender, parent.municipalityId, fee);

        uint256 tradePermitId = _tradePermitIdCounter++;

        tradePermits[tradePermitId] = TradePermit({
            tradePermitId: tradePermitId,
            parentPermitId: _parentPermitId,
            tradeType: _tradeType,
            phase: ApprovalPhase.PLAN_REVIEW,
            licensedTradesperson: msg.sender,
            tradePersonLicense: licenses[msg.sender].licenseNumber,
            workDescription: _workDescription,
            fixtureCount: _fixtureCount,
            estimatedCost: _estimatedCost,
            permitFee: fee,
            totalPaid: fee,
            submittedAt: block.timestamp,
            approvedAt: 0,
            expiresAt: 0,
            completedAt: 0,
            assignedInspector: address(0)
        });

        // Link to parent permit
        parent.tradePermitIds.push(tradePermitId);
        if (parent.phase == ApprovalPhase.PERMIT_ISSUED) {
            parent.phase = ApprovalPhase.TRADES_PENDING;
        }

        _recordPayment(_parentPermitId, fee, "TRADE");

        emit TradePermitSubmitted(tradePermitId, _parentPermitId, _tradeType);

        return tradePermitId;
    }

    /**
     * @notice Approve a trade permit
     */
    function approveTradePermit(uint256 _tradePermitId)
        external
        tradePermitExists(_tradePermitId)
    {
        TradePermit storage trade = tradePermits[_tradePermitId];
        PrimaryPermit storage parent = permits[trade.parentPermitId];

        bytes32 requiredInspectorRole = _getRequiredInspectorRole(trade.tradeType);
        require(
            _hasJurisdiction(msg.sender, parent.municipalityId, requiredInspectorRole),
            "Not authorized trade inspector"
        );
        require(trade.phase == ApprovalPhase.PLAN_REVIEW, "Not in review");

        trade.phase = ApprovalPhase.PERMIT_ISSUED;
        trade.approvedAt = block.timestamp;
        trade.expiresAt = parent.expiresAt; // Inherits parent expiration
        trade.assignedInspector = msg.sender;

        emit TradePermitApproved(_tradePermitId, msg.sender);
    }

    // ============ Inspections ============

    /**
     * @notice Schedule an inspection
     */
    function scheduleInspection(
        uint256 _permitId,
        bool _isTradePermit,
        InspectionCategory _category,
        uint256 _scheduledDate
    ) external permitExists(_permitId) returns (uint256) {
        require(_scheduledDate > block.timestamp, "Must be future date");

        uint256 inspectionId = _inspectionIdCounter++;

        permitInspections[_permitId].push(Inspection({
            inspectionId: inspectionId,
            permitId: _permitId,
            isTradePermit: _isTradePermit,
            category: _category,
            scheduledBy: msg.sender,
            assignedInspector: address(0),
            scheduledDate: _scheduledDate,
            completedDate: 0,
            passed: false,
            resultCode: "",
            notes: "",
            photoCIDs: new string[](0),
            corrections: new string[](0),
            reinspectionDeadline: 0
        }));

        // Update permit phase
        PrimaryPermit storage permit = permits[_permitId];
        if (permit.phase == ApprovalPhase.PERMIT_ISSUED ||
            permit.phase == ApprovalPhase.CONSTRUCTION_ACTIVE ||
            permit.phase == ApprovalPhase.INSPECTION_PASSED) {
            permit.phase = ApprovalPhase.INSPECTION_REQUIRED;
        }

        emit InspectionScheduled(inspectionId, _permitId, _category);

        return inspectionId;
    }

    /**
     * @notice Complete an inspection
     * @param _permitId Permit identifier
     * @param _inspectionIndex Index in the inspections array
     * @param _passed Whether inspection passed
     * @param _resultCode Result code (PASS, FAIL, PARTIAL, REINSPECT)
     * @param _notes Inspector notes
     * @param _photoCIDs IPFS CIDs of inspection photos
     * @param _corrections Required corrections if failed
     */
    function completeInspection(
        uint256 _permitId,
        uint256 _inspectionIndex,
        bool _passed,
        string calldata _resultCode,
        string calldata _notes,
        string[] calldata _photoCIDs,
        string[] calldata _corrections
    ) external permitExists(_permitId) {
        PrimaryPermit storage permit = permits[_permitId];
        require(_inspectionIndex < permitInspections[_permitId].length, "Invalid index");

        Inspection storage inspection = permitInspections[_permitId][_inspectionIndex];

        // Verify inspector has jurisdiction for this inspection type
        bytes32 requiredRole = _getRequiredInspectorRoleForCategory(inspection.category);
        require(
            _hasJurisdiction(msg.sender, permit.municipalityId, requiredRole),
            "Not authorized inspector"
        );
        require(inspection.completedDate == 0, "Already completed");

        inspection.assignedInspector = msg.sender;
        inspection.completedDate = block.timestamp;
        inspection.passed = _passed;
        inspection.resultCode = _resultCode;
        inspection.notes = _notes;

        for (uint i = 0; i < _photoCIDs.length; i++) {
            inspection.photoCIDs.push(_photoCIDs[i]);
        }

        if (_passed) {
            if (inspection.category == InspectionCategory.CERTIFICATE_OF_OCCUPANCY) {
                permit.phase = ApprovalPhase.CO_PENDING;
            } else if (inspection.category == InspectionCategory.FINAL_BUILDING) {
                permit.phase = ApprovalPhase.FINAL_INSPECTION;
            } else {
                permit.phase = ApprovalPhase.INSPECTION_PASSED;
            }

            emit InspectionCompleted(inspection.inspectionId, true, _resultCode);
        } else {
            permit.phase = ApprovalPhase.INSPECTION_FAILED;
            inspection.reinspectionDeadline = block.timestamp + 30 days;

            for (uint i = 0; i < _corrections.length; i++) {
                inspection.corrections.push(_corrections[i]);
            }

            emit InspectionFailed(inspection.inspectionId, _corrections);
        }

        emit PermitPhaseChanged(_permitId, ApprovalPhase.INSPECTION_REQUIRED, permit.phase, msg.sender);
    }

    // ============ Certificate of Occupancy ============

    /**
     * @notice Issue Certificate of Occupancy
     */
    function issueCertificateOfOccupancy(
        uint256 _permitId,
        string calldata _coNumber,
        uint256 _maxOccupancy,
        bool _isTemporary,
        uint256 _temporaryExpiresAt,
        string calldata _coCID
    ) external permitExists(_permitId) onlyJurisdiction(permits[_permitId].municipalityId, BUILDING_OFFICIAL) {
        PrimaryPermit storage permit = permits[_permitId];
        require(
            permit.phase == ApprovalPhase.CO_PENDING ||
            permit.phase == ApprovalPhase.FINAL_INSPECTION,
            "Not ready for C/O"
        );

        // Verify all required trade permits are complete
        if (permit.requiresTradePermits) {
            for (uint i = 0; i < permit.tradePermitIds.length; i++) {
                TradePermit storage trade = tradePermits[permit.tradePermitIds[i]];
                require(
                    trade.phase == ApprovalPhase.COMPLETED,
                    "Trade permit not complete"
                );
            }
        }

        uint256 coId = _coIdCounter++;

        certificatesOfOccupancy[_permitId] = CertificateOfOccupancy({
            coId: coId,
            permitId: _permitId,
            municipalityId: permit.municipalityId,
            coNumber: _coNumber,
            occupancyType: permit.useGroup,
            maxOccupancy: _maxOccupancy,
            isTemporary: _isTemporary,
            temporaryExpiresAt: _temporaryExpiresAt,
            issuedBy: msg.sender,
            issuedAt: block.timestamp,
            coCID: _coCID
        });

        permit.phase = ApprovalPhase.COMPLETED;
        permit.completedAt = block.timestamp;

        emit CertificateOfOccupancyIssued(coId, _permitId, _coNumber);
        emit PermitPhaseChanged(_permitId, ApprovalPhase.CO_PENDING, ApprovalPhase.COMPLETED, msg.sender);
    }

    // ============ Permit Management ============

    /**
     * @notice Extend permit validity
     */
    function extendPermit(uint256 _permitId, uint256 _extensionDays)
        external
        permitExists(_permitId)
        onlyJurisdiction(permits[_permitId].municipalityId, BUILDING_OFFICIAL)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(
            permit.phase == ApprovalPhase.PERMIT_ISSUED ||
            permit.phase == ApprovalPhase.CONSTRUCTION_ACTIVE ||
            permit.phase == ApprovalPhase.INSPECTION_REQUIRED ||
            permit.phase == ApprovalPhase.INSPECTION_PASSED,
            "Cannot extend in current phase"
        );
        require(_extensionDays * 1 days <= MAX_EXTENSION_PERIOD, "Exceeds max extension");

        permit.expiresAt += _extensionDays * 1 days;

        emit PermitExtended(_permitId, permit.expiresAt);
    }

    /**
     * @notice Suspend permit (stop work order)
     */
    function suspendPermit(uint256 _permitId, string calldata _reason)
        external
        permitExists(_permitId)
        onlyJurisdiction(permits[_permitId].municipalityId, BUILDING_OFFICIAL)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(permit.phase != ApprovalPhase.COMPLETED, "Cannot suspend completed");

        ApprovalPhase previousPhase = permit.phase;
        permit.phase = ApprovalPhase.SUSPENDED;

        emit PermitSuspended(_permitId, _reason);
        emit PermitPhaseChanged(_permitId, previousPhase, permit.phase, msg.sender);
    }

    /**
     * @notice Revoke permit
     */
    function revokePermit(uint256 _permitId, string calldata _reason)
        external
        permitExists(_permitId)
        onlyJurisdiction(permits[_permitId].municipalityId, BUILDING_OFFICIAL)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(permit.phase != ApprovalPhase.COMPLETED, "Cannot revoke completed");

        ApprovalPhase previousPhase = permit.phase;
        permit.phase = ApprovalPhase.REVOKED;

        emit PermitRevoked(_permitId, _reason);
        emit PermitPhaseChanged(_permitId, previousPhase, permit.phase, msg.sender);
    }

    /**
     * @notice Void permit and issue refund
     */
    function voidPermitWithRefund(uint256 _permitId, string calldata _reason)
        external
        permitExists(_permitId)
        onlyJurisdiction(permits[_permitId].municipalityId, MUNICIPAL_CLERK)
    {
        PrimaryPermit storage permit = permits[_permitId];
        require(
            permit.phase == ApprovalPhase.ZONING_REVIEW ||
            permit.phase == ApprovalPhase.PLAN_REVIEW ||
            permit.phase == ApprovalPhase.FEES_PENDING,
            "Cannot void in current phase"
        );

        // Calculate refund (application fee minus processing fee)
        uint256 processingFee = permit.applicationFee / 10; // Keep 10%
        uint256 refundAmount = permit.totalPaid - processingFee;

        if (refundAmount > 0) {
            usdc.safeTransfer(permit.applicant, refundAmount);

            // Record refund
            PaymentRecord[] storage payments = permitPayments[_permitId];
            for (uint i = 0; i < payments.length; i++) {
                if (!payments[i].isRefunded) {
                    payments[i].isRefunded = true;
                    payments[i].refundedAt = block.timestamp;
                    payments[i].refundReason = _reason;
                    emit RefundIssued(payments[i].paymentId, payments[i].amount, _reason);
                }
            }
        }

        permit.phase = ApprovalPhase.VOIDED;

        emit PermitVoided(_permitId, refundAmount);
    }

    /**
     * @notice State approval for large projects
     */
    function grantStateApproval(uint256 _permitId)
        external
        permitExists(_permitId)
        onlyStateOfficial
    {
        permits[_permitId].stateApproved = true;
    }

    // ============ Internal Functions ============

    function _calculateApplicationFee(
        bytes32 _municipalityId,
        PrimaryPermitType _permitType
    ) internal view returns (uint256) {
        FeeScheduleEntry storage entry = feeSchedules[_municipalityId][_permitType];

        // If no fee schedule set, use defaults
        if (entry.baseFee == 0) {
            // Default application fees (in USDC with 6 decimals)
            if (_permitType == PrimaryPermitType.RESIDENTIAL_NEW_CONSTRUCTION ||
                _permitType == PrimaryPermitType.COMMERCIAL_NEW_CONSTRUCTION) {
                return 250 * 10**6; // $250
            } else if (_permitType == PrimaryPermitType.DEMOLITION_FULL) {
                return 150 * 10**6; // $150
            }
            return 100 * 10**6; // $100 default
        }

        return entry.baseFee;
    }

    function _calculatePermitFee(
        bytes32 _municipalityId,
        PrimaryPermitType _permitType,
        uint256 _squareFootage,
        uint256 _estimatedCost
    ) internal view returns (uint256) {
        FeeScheduleEntry storage entry = feeSchedules[_municipalityId][_permitType];

        uint256 sqftFee = _squareFootage * entry.perSqFtFee;
        uint256 costFee = (_estimatedCost * 50) / 10000; // 0.5% of cost

        uint256 fee = sqftFee > costFee ? sqftFee : costFee;

        if (fee < entry.minimumFee) fee = entry.minimumFee;
        if (entry.maximumFee > 0 && fee > entry.maximumFee) fee = entry.maximumFee;

        // Add plan review fee
        fee += (fee * entry.planReviewPercent) / 10000;

        return fee;
    }

    function _collectPayment(
        address _from,
        bytes32 _municipalityId,
        uint256 _amount
    ) internal {
        // Transfer from payer to contract
        usdc.safeTransferFrom(_from, address(this), _amount);

        // Calculate state share
        uint256 stateShare = (_amount * stateFeePercent) / 10000;
        uint256 muniShare = _amount - stateShare;

        // Distribute
        usdc.safeTransfer(stateTreasury, stateShare);
        usdc.safeTransfer(municipalities[_municipalityId].treasury, muniShare);

        // Update stats
        municipalities[_municipalityId].totalRevenue += _amount;
    }

    function _recordPayment(
        uint256 _permitId,
        uint256 _amount,
        string memory _paymentType
    ) internal {
        uint256 paymentId = _paymentIdCounter++;

        permitPayments[_permitId].push(PaymentRecord({
            paymentId: paymentId,
            permitId: _permitId,
            amount: _amount,
            paymentType: _paymentType,
            receiptHash: keccak256(abi.encodePacked(_permitId, _amount, block.timestamp, msg.sender)),
            paidBy: msg.sender,
            paidAt: block.timestamp,
            isRefunded: false,
            refundedAt: 0,
            refundReason: ""
        }));

        emit PaymentReceived(paymentId, _permitId, _amount, _paymentType);
    }

    function _requiresTradePermits(PrimaryPermitType _type) internal pure returns (bool) {
        return _type == PrimaryPermitType.RESIDENTIAL_NEW_CONSTRUCTION ||
               _type == PrimaryPermitType.RESIDENTIAL_ADDITION ||
               _type == PrimaryPermitType.MULTIFAMILY_NEW_CONSTRUCTION ||
               _type == PrimaryPermitType.COMMERCIAL_NEW_CONSTRUCTION ||
               _type == PrimaryPermitType.COMMERCIAL_TENANT_FITOUT ||
               _type == PrimaryPermitType.INDUSTRIAL_NEW_CONSTRUCTION ||
               _type == PrimaryPermitType.MIXED_USE;
    }

    function _getRequiredTradeRole(TradePermitType _type) internal pure returns (bytes32) {
        if (_type == TradePermitType.ELECTRICAL || _type == TradePermitType.LOW_VOLTAGE) {
            return LICENSED_ELECTRICIAN;
        } else if (_type == TradePermitType.PLUMBING) {
            return LICENSED_PLUMBER;
        } else if (_type == TradePermitType.GAS) {
            return LICENSED_GAS_FITTER;
        }
        return LICENSED_CONTRACTOR;
    }

    function _getRequiredInspectorRole(TradePermitType _type) internal pure returns (bytes32) {
        if (_type == TradePermitType.ELECTRICAL || _type == TradePermitType.LOW_VOLTAGE) {
            return ELECTRICAL_INSPECTOR;
        } else if (_type == TradePermitType.PLUMBING) {
            return PLUMBING_INSPECTOR;
        } else if (_type == TradePermitType.GAS) {
            return GAS_INSPECTOR;
        } else if (_type == TradePermitType.MECHANICAL_HVAC) {
            return MECHANICAL_INSPECTOR;
        } else if (_type == TradePermitType.FIRE_SUPPRESSION || _type == TradePermitType.FIRE_ALARM) {
            return FIRE_INSPECTOR;
        }
        return BUILDING_OFFICIAL;
    }

    function _getRequiredInspectorRoleForCategory(InspectionCategory _category) internal pure returns (bytes32) {
        if (_category == InspectionCategory.ELECTRICAL_ROUGH ||
            _category == InspectionCategory.ELECTRICAL_FINAL) {
            return ELECTRICAL_INSPECTOR;
        } else if (_category == InspectionCategory.PLUMBING_ROUGH ||
                   _category == InspectionCategory.PLUMBING_FINAL ||
                   _category == InspectionCategory.PLUMBING_WATER_TEST) {
            return PLUMBING_INSPECTOR;
        } else if (_category == InspectionCategory.GAS_ROUGH ||
                   _category == InspectionCategory.GAS_FINAL ||
                   _category == InspectionCategory.GAS_PRESSURE_TEST) {
            return GAS_INSPECTOR;
        } else if (_category == InspectionCategory.MECHANICAL_ROUGH ||
                   _category == InspectionCategory.MECHANICAL_FINAL) {
            return MECHANICAL_INSPECTOR;
        } else if (_category == InspectionCategory.FIRE_SUPPRESSION_ROUGH ||
                   _category == InspectionCategory.FIRE_SUPPRESSION_FINAL ||
                   _category == InspectionCategory.FIRE_ALARM) {
            return FIRE_INSPECTOR;
        }
        return BUILDING_OFFICIAL;
    }

    // ============ View Functions ============

    function getPermit(uint256 _permitId) external view returns (
        uint256 permitId,
        bytes32 municipalityId,
        PrimaryPermitType permitType,
        ApprovalPhase phase,
        address applicant,
        uint256 estimatedCost,
        uint256 grossSquareFootage,
        uint256 totalPaid,
        uint256 submittedAt,
        uint256 expiresAt,
        bool plansLocked,
        string memory plansCID
    ) {
        PrimaryPermit storage p = permits[_permitId];
        return (
            p.permitId,
            p.municipalityId,
            p.permitType,
            p.phase,
            p.applicant,
            p.estimatedCost,
            p.grossSquareFootage,
            p.totalPaid,
            p.submittedAt,
            p.expiresAt,
            p.plans.isLocked,
            p.plans.plansCID
        );
    }

    function getPermitProperty(uint256 _permitId) external view returns (PropertyRecord memory) {
        return permits[_permitId].property;
    }

    function getPermitPlans(uint256 _permitId) external view returns (StampedPlanSet memory) {
        return permits[_permitId].plans;
    }

    function getPermitAmendments(uint256 _permitId) external view returns (PlanAmendment[] memory) {
        return permits[_permitId].amendments;
    }

    function getTradePermit(uint256 _tradePermitId) external view returns (TradePermit memory) {
        return tradePermits[_tradePermitId];
    }

    function getPermitInspections(uint256 _permitId) external view returns (Inspection[] memory) {
        return permitInspections[_permitId];
    }

    function getPermitPayments(uint256 _permitId) external view returns (PaymentRecord[] memory) {
        return permitPayments[_permitId];
    }

    function getCertificateOfOccupancy(uint256 _permitId) external view returns (CertificateOfOccupancy memory) {
        return certificatesOfOccupancy[_permitId];
    }

    function getApplicantPermits(address _applicant) external view returns (uint256[] memory) {
        return applicantPermits[_applicant];
    }

    function getMunicipalityPermits(bytes32 _municipalityId) external view returns (uint256[] memory) {
        return municipalityPermits[_municipalityId];
    }

    function getParcelHistory(string calldata _parcelId) external view returns (uint256[] memory) {
        return parcelPermitHistory[_parcelId];
    }

    function getMunicipality(bytes32 _id) external view returns (Municipality memory) {
        return municipalities[_id];
    }

    function getLicense(address _holder) external view returns (License memory) {
        return licenses[_holder];
    }

    function hasJurisdiction(
        address _official,
        bytes32 _municipalityId,
        bytes32 _role
    ) external view returns (bool) {
        return _hasJurisdiction(_official, _municipalityId, _role);
    }

    function isPermitValid(uint256 _permitId) external view returns (bool) {
        PrimaryPermit storage p = permits[_permitId];
        if (p.permitId == 0) return false;
        if (p.phase == ApprovalPhase.COMPLETED) return true;
        if (p.phase == ApprovalPhase.EXPIRED ||
            p.phase == ApprovalPhase.REVOKED ||
            p.phase == ApprovalPhase.VOIDED ||
            p.phase == ApprovalPhase.SUSPENDED) return false;
        if (p.expiresAt != 0 && block.timestamp > p.expiresAt) return false;
        return p.phase == ApprovalPhase.PERMIT_ISSUED ||
               p.phase == ApprovalPhase.CONSTRUCTION_ACTIVE ||
               p.phase == ApprovalPhase.INSPECTION_REQUIRED ||
               p.phase == ApprovalPhase.INSPECTION_PASSED ||
               p.phase == ApprovalPhase.TRADES_PENDING ||
               p.phase == ApprovalPhase.FINAL_INSPECTION;
    }

    function getAllMunicipalities() external view returns (bytes32[] memory) {
        return municipalityList;
    }

    // ============ Admin Functions ============

    function updateStateTreasury(address _newTreasury) external onlyStateOfficial {
        require(_newTreasury != address(0), "Invalid address");
        stateTreasury = _newTreasury;
    }

    function updateStateFeePercent(uint256 _newPercent) external onlyStateOfficial {
        require(_newPercent <= 1000, "Max 10%");
        stateFeePercent = _newPercent;
    }

    function updateStateReviewThreshold(uint256 _newThreshold) external onlyStateOfficial {
        stateReviewThreshold = _newThreshold;
    }

    function pause() external onlyStateOfficial {
        _pause();
    }

    function unpause() external onlyStateOfficial {
        _unpause();
    }

    /**
     * @notice Emergency withdrawal of stuck tokens
     */
    function emergencyWithdraw(address _token, address _to, uint256 _amount)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        require(_to != address(0), "Invalid recipient");
        IERC20(_token).safeTransfer(_to, _amount);
    }
}
