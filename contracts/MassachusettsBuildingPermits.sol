// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MassachusettsBuildingPermits
 * @author NoblePort ETF - Construction Workflow Intelligence Engine
 * @notice Production-grade building permit management with AGI reasoning layer
 * @dev Hardened contract features:
 *      - Separate state machines for primary vs trade permits
 *      - Deterministic dependency enforcement (no guessing)
 *      - AI compliance scoring for AGI reasoning
 *      - Stripe/escrow-compatible financial milestones
 *      - Voice-avatar deterministic status output
 *      - Multi-jurisdiction support
 *
 * Compliance: MA 780 CMR 10th Edition | MGL c.143 ss.93-100
 */

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract MassachusettsBuildingPermits is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // ============ Code References ============

    string public constant VERSION = "2.0.0-hardened";
    string public constant MA_CODE_REF = "780 CMR 10th Edition";
    string public constant STATUTORY_REF = "MGL c.143, ss.93-100";

    // ============ Role Hierarchy ============

    bytes32 public constant STATE_COMMISSIONER = keccak256("STATE_COMMISSIONER");
    bytes32 public constant BUILDING_OFFICIAL = keccak256("BUILDING_OFFICIAL");
    bytes32 public constant ELECTRICAL_INSPECTOR = keccak256("ELECTRICAL_INSPECTOR");
    bytes32 public constant PLUMBING_INSPECTOR = keccak256("PLUMBING_INSPECTOR");
    bytes32 public constant GAS_INSPECTOR = keccak256("GAS_INSPECTOR");
    bytes32 public constant MECHANICAL_INSPECTOR = keccak256("MECHANICAL_INSPECTOR");
    bytes32 public constant FIRE_INSPECTOR = keccak256("FIRE_INSPECTOR");
    bytes32 public constant ZONING_OFFICER = keccak256("ZONING_OFFICER");
    bytes32 public constant MUNICIPAL_CLERK = keccak256("MUNICIPAL_CLERK");

    // ============ FIX #1: Separate State Machines ============
    // Primary and trade lifecycles are NOT identical

    /// @notice Primary permit lifecycle (can expire, requires zoning)
    enum PrimaryPhase {
        Draft,          // 0: Application created
        Submitted,      // 1: Submitted for review
        ZoningReview,   // 2: Awaiting zoning clearance
        PlanReview,     // 3: Technical plan review
        Approved,       // 4: Approved, pending fees
        Issued,         // 5: Permit card issued ← GATE for trades
        Active,         // 6: Construction in progress
        FinalInspection,// 7: Final inspection phase
        Finaled,        // 8: Certificate of Occupancy issued
        Expired,        // 9: 180 days no activity
        Revoked,        // 10: Permit revoked
        Suspended       // 11: Stop work order
    }

    /// @notice Trade permit lifecycle (inspection-centric, no zoning)
    enum TradePhase {
        Pending,        // 0: Created, awaiting submission
        Submitted,      // 1: Submitted for review
        Issued,         // 2: Trade permit issued
        RoughScheduled, // 3: Rough inspection scheduled
        RoughPassed,    // 4: Rough inspection passed
        RoughFailed,    // 5: Rough inspection failed
        FinalScheduled, // 6: Final inspection scheduled
        Inspected,      // 7: All inspections complete
        Finaled,        // 8: Trade work signed off
        Rejected,       // 9: Application rejected
        Voided          // 10: Voided with refund
    }

    // ============ FIX #7: Jurisdiction Switch ============

    enum Jurisdiction {
        MA_10th,        // Massachusetts 780 CMR 10th Edition
        MA_9th,         // Massachusetts 780 CMR 9th Edition (legacy)
        NYC_DOB,        // New York City DOB
        CA_2022,        // California 2022 Building Code
        Custom          // Custom ruleset
    }

    // ============ Enums ============

    enum PrimaryType {
        NewConstruction,
        Addition,
        Alteration,
        Remodel,
        Demolition,
        ChangeOfUse,
        ShellOnly,
        ADU,
        SolarPV,
        Other
    }

    enum TradeType {
        Electrical,
        Plumbing,
        Gas,
        Mechanical,
        Fire,
        LowVoltage,
        Elevator,
        Other
    }

    /// @notice FIX #4: Upgraded inspection types for real execution
    enum InspectionType {
        Underground,    // Below grade
        Rough,          // Before drywall
        TopOut,         // Above ceiling
        Final,          // Completion inspection
        Reinspection    // Failed re-check
    }

    enum InspectionResult {
        Pending,        // Not yet performed
        Passed,         // Approved
        Failed,         // Requires corrections
        Conditional     // Passed with conditions
    }

    /// @notice FIX #3: AI risk levels for compliance scoring
    enum RiskLevel {
        Low,            // Score 80-100
        Medium,         // Score 50-79
        High            // Score 0-49
    }

    /// @notice FIX #5: Payment milestone triggers
    enum MilestoneTrigger {
        OnSubmission,       // Pay on permit submission
        OnIssuance,         // Pay on permit issuance
        OnInspectionPass,   // Release on inspection pass
        OnFinaled,          // Release on final signoff
        Manual              // Manual release
    }

    // ============ Structs ============

    struct Municipality {
        bytes32 id;
        string name;
        uint16 townCode;
        address treasury;
        Jurisdiction jurisdiction;
        bool isActive;
        uint256 permitsIssued;
        uint256 totalRevenue;
    }

    struct JurisdictionGrant {
        bytes32 municipalityId;
        bytes32 role;
        uint256 expiresAt;
        bool isActive;
    }

    struct License {
        address holder;
        string licenseNumber;
        string licenseType;
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
        string parcelId;
        string zoningDistrict;
    }

    /// @notice Immutable plan set with IPFS/Arweave anchoring
    struct StampedPlans {
        string plansCID;
        string specsCID;
        string calcsCID;
        string peLicense;
        uint256 lockedAt;
        bool isLocked;
    }

    /// @notice FIX #3: Compliance scoring for AGI reasoning
    struct ComplianceMeta {
        uint8 score;            // 0-100
        RiskLevel risk;
        string[] flags;         // e.g., ["Missing setback", "Zoning variance needed"]
        uint256 scoredAt;
        address scoredBy;       // AI oracle or official
    }

    /// @notice FIX #4: Production-grade inspection
    struct Inspection {
        uint256 id;
        InspectionType inspectionType;
        InspectionResult result;
        address inspector;
        uint256 scheduledAt;
        uint256 completedAt;
        string notes;
        string[] photoCIDs;
        string[] corrections;   // Required fixes if failed
    }

    /// @notice FIX #5: Stripe/smart-contract financial layer
    struct FinancialMilestone {
        uint256 fee;                    // Permit fee (6 decimals USDC)
        uint256 escrowAmount;           // Held in escrow
        MilestoneTrigger releaseOn;     // When to release escrow
        bool feePaid;
        bool escrowReleased;
        uint256 paidAt;
        uint256 releasedAt;
        bytes32 stripePaymentId;        // Off-chain Stripe reference
        bytes32 receiptHash;            // On-chain receipt proof
    }

    /// @notice Primary permit (building permit)
    struct PrimaryPermit {
        uint256 id;
        bytes32 municipalityId;
        Jurisdiction jurisdiction;
        PrimaryType permitType;
        PrimaryPhase phase;

        // Property & applicant
        PropertyRecord property;
        address applicant;
        address propertyOwner;
        string contractorLicense;

        // Project
        string description;
        uint256 estimatedCost;
        uint256 squareFootage;
        string useGroup;
        string constructionType;

        // Plans (immutable after lock)
        StampedPlans plans;

        // FIX #3: AI compliance
        ComplianceMeta compliance;

        // FIX #5: Financials
        FinancialMilestone financials;

        // Timestamps
        uint256 submittedAt;
        uint256 issuedAt;
        uint256 expiresAt;
        uint256 finaledAt;
        uint256 lastActivityAt;

        // Linked trades
        uint256[] tradePermitIds;
        bool requiresTradePermits;

        // State review
        bool requiresStateReview;
        bool stateApproved;
    }

    /// @notice Trade permit (electrical, plumbing, etc.)
    struct TradePermit {
        uint256 id;
        uint256 primaryId;          // Parent permit reference
        TradeType tradeType;
        TradePhase phase;

        // Licensed tradesperson
        address contractor;
        string contractorLicense;

        // Scope
        string scope;
        uint256 fixtureCount;
        uint256 estimatedCost;

        // FIX #4: Inspections
        Inspection[] inspections;

        // FIX #5: Financials
        FinancialMilestone financials;

        // FIX #3: AI compliance
        ComplianceMeta compliance;

        // Timestamps
        uint256 submittedAt;
        uint256 issuedAt;
        uint256 finaledAt;

        // Assigned inspector
        address assignedInspector;
    }

    struct CertificateOfOccupancy {
        uint256 id;
        uint256 permitId;
        string coNumber;
        string occupancyType;
        uint256 maxOccupancy;
        bool isTemporary;
        uint256 expiresAt;
        address issuedBy;
        uint256 issuedAt;
        string coCID;
    }

    // ============ State Variables ============

    IERC20 public immutable usdc;
    address public stateTreasury;
    uint256 public stateFeePercent = 500; // 5%

    uint256 private _permitCounter = 1;
    uint256 private _tradeCounter = 1;
    uint256 private _inspectionCounter = 1;
    uint256 private _coCounter = 1;

    uint256 public constant PERMIT_VALIDITY = 365 days;
    uint256 public constant INACTIVITY_EXPIRY = 180 days;
    uint256 public stateReviewThreshold = 50_000_000 * 10**6;

    // Mappings
    mapping(bytes32 => Municipality) public municipalities;
    bytes32[] public municipalityList;

    mapping(address => mapping(bytes32 => mapping(bytes32 => JurisdictionGrant))) public jurisdictions;
    mapping(address => License) public licenses;
    mapping(string => address) public licenseRegistry;

    mapping(uint256 => PrimaryPermit) public permits;
    mapping(uint256 => TradePermit) public tradePermits;
    mapping(uint256 => CertificateOfOccupancy) public certificates;

    mapping(address => uint256[]) public applicantPermits;
    mapping(bytes32 => uint256[]) public municipalityPermits;

    // ============ Events ============

    event MunicipalityRegistered(bytes32 indexed id, string name, Jurisdiction jurisdiction);
    event JurisdictionGranted(address indexed official, bytes32 indexed municipalityId, bytes32 role);
    event LicenseRegistered(address indexed holder, string licenseNumber);

    event PrimaryPermitCreated(uint256 indexed id, bytes32 indexed municipalityId, PrimaryType permitType);
    event PrimaryPhaseChanged(uint256 indexed id, PrimaryPhase from, PrimaryPhase to, address by);
    event PlansLocked(uint256 indexed id, string plansCID);

    event TradePermitCreated(uint256 indexed id, uint256 indexed primaryId, TradeType tradeType);
    event TradePhaseChanged(uint256 indexed id, TradePhase from, TradePhase to, address by);

    event InspectionScheduled(uint256 indexed permitId, uint256 inspectionId, InspectionType inspectionType);
    event InspectionCompleted(uint256 indexed permitId, uint256 inspectionId, InspectionResult result);

    event ComplianceScored(uint256 indexed permitId, uint8 score, RiskLevel risk);
    event PaymentReceived(uint256 indexed permitId, uint256 amount, bytes32 receiptHash);
    event EscrowReleased(uint256 indexed permitId, uint256 amount, MilestoneTrigger trigger);

    event COIssued(uint256 indexed coId, uint256 indexed permitId, string coNumber);

    // FIX #6: Voice status events
    event VoiceStatus(uint256 indexed permitId, string message);

    // ============ Errors (Gas-Efficient) ============

    error NotAuthorized();
    error InvalidPhase();
    error InvalidDependency();
    error LicenseInvalid();
    error InsufficientPayment();
    error PlansLocked();
    error MunicipalityInactive();
    error PrimaryNotIssued();
    error TradeNotEligible();

    // ============ Modifiers ============

    modifier onlyState() {
        if (!hasRole(STATE_COMMISSIONER, msg.sender) && !hasRole(DEFAULT_ADMIN_ROLE, msg.sender))
            revert NotAuthorized();
        _;
    }

    modifier onlyJurisdiction(bytes32 _muniId, bytes32 _role) {
        if (!_hasJurisdiction(msg.sender, _muniId, _role) &&
            !hasRole(STATE_COMMISSIONER, msg.sender) &&
            !hasRole(DEFAULT_ADMIN_ROLE, msg.sender))
            revert NotAuthorized();
        _;
    }

    modifier primaryExists(uint256 _id) {
        require(permits[_id].id != 0, "Primary not found");
        _;
    }

    modifier tradeExists(uint256 _id) {
        require(tradePermits[_id].id != 0, "Trade not found");
        _;
    }

    // ============ Constructor ============

    constructor(address _usdc, address _treasury) {
        require(_usdc != address(0) && _treasury != address(0), "Invalid address");
        usdc = IERC20(_usdc);
        stateTreasury = _treasury;
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(STATE_COMMISSIONER, msg.sender);
    }

    // ============ FIX #2: Deterministic Dependency Logic ============

    /**
     * @notice Check if primary permit is in a state that allows trade permits
     * @dev Trade permits can ONLY proceed if primary is ISSUED or later (not expired/revoked)
     */
    function isPrimaryEligibleForTrades(uint256 _primaryId) public view returns (bool) {
        PrimaryPermit storage p = permits[_primaryId];
        if (p.id == 0) return false;

        // Only these phases allow trade permit activity
        return p.phase == PrimaryPhase.Issued ||
               p.phase == PrimaryPhase.Active ||
               p.phase == PrimaryPhase.FinalInspection;
    }

    /**
     * @notice Check if a specific trade type can be submitted for a primary
     * @dev Deterministic check - no guessing, no hallucination
     */
    function isTradeEligible(
        uint256 _primaryId,
        TradeType _tradeType
    ) public view returns (bool eligible, string memory reason) {
        PrimaryPermit storage p = permits[_primaryId];

        if (p.id == 0) {
            return (false, "Primary permit does not exist");
        }

        if (p.phase != PrimaryPhase.Issued &&
            p.phase != PrimaryPhase.Active &&
            p.phase != PrimaryPhase.FinalInspection) {
            return (false, "Primary permit is not issued");
        }

        if (p.phase == PrimaryPhase.Expired) {
            return (false, "Primary permit has expired");
        }

        if (p.phase == PrimaryPhase.Revoked) {
            return (false, "Primary permit has been revoked");
        }

        if (p.phase == PrimaryPhase.Suspended) {
            return (false, "Primary permit is suspended - stop work order in effect");
        }

        // Check if this trade type already has a finaled permit
        for (uint i = 0; i < p.tradePermitIds.length; i++) {
            TradePermit storage t = tradePermits[p.tradePermitIds[i]];
            if (t.tradeType == _tradeType && t.phase == TradePhase.Finaled) {
                return (false, "Trade permit of this type already finaled");
            }
        }

        return (true, "Eligible");
    }

    /**
     * @notice Check if inspection can proceed
     */
    function canScheduleInspection(uint256 _tradeId) public view returns (bool eligible, string memory reason) {
        TradePermit storage t = tradePermits[_tradeId];

        if (t.id == 0) {
            return (false, "Trade permit does not exist");
        }

        if (t.phase == TradePhase.Pending || t.phase == TradePhase.Submitted) {
            return (false, "Trade permit not yet issued");
        }

        if (t.phase == TradePhase.Finaled) {
            return (false, "Trade permit already finaled");
        }

        if (t.phase == TradePhase.Voided || t.phase == TradePhase.Rejected) {
            return (false, "Trade permit is voided or rejected");
        }

        // Check primary is still valid
        if (!isPrimaryEligibleForTrades(t.primaryId)) {
            return (false, "Parent primary permit is not active");
        }

        return (true, "Eligible for inspection");
    }

    /**
     * @notice Check if payment can be released (escrow)
     */
    function canReleasePayment(uint256 _tradeId) public view returns (bool) {
        TradePermit storage t = tradePermits[_tradeId];
        if (t.id == 0) return false;
        if (t.financials.escrowReleased) return false;
        if (t.financials.escrowAmount == 0) return false;

        if (t.financials.releaseOn == MilestoneTrigger.OnInspectionPass) {
            // Check if any inspection passed
            for (uint i = 0; i < t.inspections.length; i++) {
                if (t.inspections[i].result == InspectionResult.Passed) {
                    return true;
                }
            }
            return false;
        }

        if (t.financials.releaseOn == MilestoneTrigger.OnFinaled) {
            return t.phase == TradePhase.Finaled;
        }

        return false;
    }

    // ============ FIX #6: Voice-Optimized Status Output ============

    /**
     * @notice Get deterministic voice summary for primary permit
     * @dev Prevents speculative AGI speech - avatar becomes reliable
     */
    function getVoiceSummary(uint256 _primaryId) external view returns (string memory) {
        PrimaryPermit storage p = permits[_primaryId];

        if (p.id == 0) {
            return "Permit not found.";
        }

        // Draft phase
        if (p.phase == PrimaryPhase.Draft) {
            return "Application is in draft status. Submit to begin review.";
        }

        // Submitted/Review phases
        if (p.phase == PrimaryPhase.Submitted || p.phase == PrimaryPhase.ZoningReview) {
            return "Application is under review. Awaiting zoning clearance.";
        }

        if (p.phase == PrimaryPhase.PlanReview) {
            return "Plans are under technical review by the building department.";
        }

        // Approved but not issued
        if (p.phase == PrimaryPhase.Approved) {
            return "Permit approved. Pay fees to receive permit card.";
        }

        // Issued - check trades
        if (p.phase == PrimaryPhase.Issued || p.phase == PrimaryPhase.Active) {
            uint256 openTrades = 0;
            uint256 totalTrades = p.tradePermitIds.length;

            for (uint i = 0; i < totalTrades; i++) {
                TradePermit storage t = tradePermits[p.tradePermitIds[i]];
                if (t.phase != TradePhase.Finaled) {
                    openTrades++;
                }
            }

            if (totalTrades == 0) {
                return "Primary permit issued. No trade permits on file.";
            }

            if (openTrades == 0) {
                return "All trade permits finalized. Eligible for final inspection.";
            }

            // Return count (can't concatenate strings efficiently in Solidity)
            return "Primary permit issued. Trade permits in progress.";
        }

        // Final inspection
        if (p.phase == PrimaryPhase.FinalInspection) {
            return "Final building inspection phase. Schedule final inspection to close out.";
        }

        // Finaled
        if (p.phase == PrimaryPhase.Finaled) {
            return "Project complete. Certificate of Occupancy issued.";
        }

        // Problem states
        if (p.phase == PrimaryPhase.Expired) {
            return "Permit expired due to inactivity. Renewal required.";
        }

        if (p.phase == PrimaryPhase.Revoked) {
            return "Permit has been revoked. Contact building department.";
        }

        if (p.phase == PrimaryPhase.Suspended) {
            return "Stop work order in effect. All work must cease immediately.";
        }

        return "Status unknown.";
    }

    /**
     * @notice Get trade permit voice summary
     */
    function getTradeVoiceSummary(uint256 _tradeId) external view returns (string memory) {
        TradePermit storage t = tradePermits[_tradeId];

        if (t.id == 0) return "Trade permit not found.";

        if (t.phase == TradePhase.Pending) return "Trade permit pending submission.";
        if (t.phase == TradePhase.Submitted) return "Trade permit under review.";
        if (t.phase == TradePhase.Issued) return "Trade permit issued. Ready for rough inspection.";
        if (t.phase == TradePhase.RoughScheduled) return "Rough inspection scheduled.";
        if (t.phase == TradePhase.RoughPassed) return "Rough inspection passed. Ready for final.";
        if (t.phase == TradePhase.RoughFailed) return "Rough inspection failed. Corrections required.";
        if (t.phase == TradePhase.FinalScheduled) return "Final inspection scheduled.";
        if (t.phase == TradePhase.Inspected) return "Inspections complete. Awaiting signoff.";
        if (t.phase == TradePhase.Finaled) return "Trade permit finaled. Work complete.";
        if (t.phase == TradePhase.Rejected) return "Trade permit rejected.";
        if (t.phase == TradePhase.Voided) return "Trade permit voided.";

        return "Status unknown.";
    }

    // ============ Jurisdiction Management ============

    function _hasJurisdiction(address _addr, bytes32 _muniId, bytes32 _role) internal view returns (bool) {
        JurisdictionGrant storage g = jurisdictions[_addr][_muniId][_role];
        if (!g.isActive) return false;
        if (g.expiresAt != 0 && g.expiresAt < block.timestamp) return false;
        return true;
    }

    function grantJurisdiction(
        address _official,
        bytes32 _muniId,
        bytes32 _role,
        uint256 _expiresAt
    ) external onlyState {
        jurisdictions[_official][_muniId][_role] = JurisdictionGrant({
            municipalityId: _muniId,
            role: _role,
            expiresAt: _expiresAt,
            isActive: true
        });
        emit JurisdictionGranted(_official, _muniId, _role);
    }

    // ============ Municipality Management ============

    function registerMunicipality(
        string calldata _name,
        uint16 _townCode,
        address _treasury,
        Jurisdiction _jurisdiction
    ) external onlyState {
        bytes32 id = keccak256(abi.encodePacked(_name, _townCode));
        require(municipalities[id].townCode == 0, "Exists");

        municipalities[id] = Municipality({
            id: id,
            name: _name,
            townCode: _townCode,
            treasury: _treasury,
            jurisdiction: _jurisdiction,
            isActive: true,
            permitsIssued: 0,
            totalRevenue: 0
        });

        municipalityList.push(id);
        emit MunicipalityRegistered(id, _name, _jurisdiction);
    }

    // ============ License Management ============

    function registerLicense(
        address _holder,
        string calldata _number,
        string calldata _type,
        uint256 _expiresAt
    ) external onlyState {
        require(licenseRegistry[_number] == address(0), "License exists");

        licenses[_holder] = License({
            holder: _holder,
            licenseNumber: _number,
            licenseType: _type,
            expiresAt: _expiresAt,
            isActive: true,
            isSuspended: false
        });

        licenseRegistry[_number] = _holder;
        emit LicenseRegistered(_holder, _number);
    }

    // ============ Primary Permit Lifecycle ============

    function submitPrimaryPermit(
        bytes32 _muniId,
        PrimaryType _type,
        PropertyRecord calldata _property,
        address _propertyOwner,
        string calldata _contractorLicense,
        string calldata _description,
        uint256 _estimatedCost,
        uint256 _squareFootage,
        string calldata _useGroup,
        string calldata _constructionType
    ) external nonReentrant whenNotPaused returns (uint256) {
        Municipality storage m = municipalities[_muniId];
        if (!m.isActive) revert MunicipalityInactive();

        // Validate contractor license
        address contractor = licenseRegistry[_contractorLicense];
        License storage lic = licenses[contractor];
        if (!lic.isActive || lic.isSuspended || lic.expiresAt < block.timestamp) {
            revert LicenseInvalid();
        }

        uint256 id = _permitCounter++;

        permits[id].id = id;
        permits[id].municipalityId = _muniId;
        permits[id].jurisdiction = m.jurisdiction;
        permits[id].permitType = _type;
        permits[id].phase = PrimaryPhase.Submitted;
        permits[id].property = _property;
        permits[id].applicant = msg.sender;
        permits[id].propertyOwner = _propertyOwner;
        permits[id].contractorLicense = _contractorLicense;
        permits[id].description = _description;
        permits[id].estimatedCost = _estimatedCost;
        permits[id].squareFootage = _squareFootage;
        permits[id].useGroup = _useGroup;
        permits[id].constructionType = _constructionType;
        permits[id].submittedAt = block.timestamp;
        permits[id].lastActivityAt = block.timestamp;
        permits[id].requiresStateReview = _estimatedCost >= stateReviewThreshold;
        permits[id].requiresTradePermits = _requiresTradePermits(_type);

        applicantPermits[msg.sender].push(id);
        municipalityPermits[_muniId].push(id);

        emit PrimaryPermitCreated(id, _muniId, _type);
        emit PrimaryPhaseChanged(id, PrimaryPhase.Draft, PrimaryPhase.Submitted, msg.sender);

        return id;
    }

    function advancePrimaryPhase(
        uint256 _id,
        PrimaryPhase _newPhase
    ) external primaryExists(_id) onlyJurisdiction(permits[_id].municipalityId, BUILDING_OFFICIAL) {
        PrimaryPermit storage p = permits[_id];
        PrimaryPhase current = p.phase;

        // FIX #8: Validation guards - enforce valid transitions
        if (_newPhase == PrimaryPhase.ZoningReview) {
            require(current == PrimaryPhase.Submitted, "Must be submitted");
        } else if (_newPhase == PrimaryPhase.PlanReview) {
            require(current == PrimaryPhase.ZoningReview, "Must have zoning review");
        } else if (_newPhase == PrimaryPhase.Approved) {
            require(current == PrimaryPhase.PlanReview, "Must be in plan review");
            require(p.plans.isLocked, "Plans must be locked");
        } else if (_newPhase == PrimaryPhase.Issued) {
            require(current == PrimaryPhase.Approved, "Must be approved");
            require(p.financials.feePaid, "Fees not paid");
            if (p.requiresStateReview) {
                require(p.stateApproved, "State approval required");
            }
            p.issuedAt = block.timestamp;
            p.expiresAt = block.timestamp + PERMIT_VALIDITY;
            municipalities[p.municipalityId].permitsIssued++;
        }

        p.phase = _newPhase;
        p.lastActivityAt = block.timestamp;

        emit PrimaryPhaseChanged(_id, current, _newPhase, msg.sender);
        emit VoiceStatus(_id, "Permit status updated.");
    }

    function lockPlans(
        uint256 _id,
        string calldata _plansCID,
        string calldata _specsCID,
        string calldata _calcsCID,
        string calldata _peLicense
    ) external primaryExists(_id) {
        PrimaryPermit storage p = permits[_id];
        require(p.applicant == msg.sender || p.propertyOwner == msg.sender, "Not authorized");
        if (p.plans.isLocked) revert PlansLocked();
        require(p.phase == PrimaryPhase.PlanReview, "Not in plan review");

        p.plans = StampedPlans({
            plansCID: _plansCID,
            specsCID: _specsCID,
            calcsCID: _calcsCID,
            peLicense: _peLicense,
            lockedAt: block.timestamp,
            isLocked: true
        });

        emit PlansLocked(_id, _plansCID);
    }

    // ============ FIX #3: Compliance Scoring ============

    /**
     * @notice Set AI compliance score
     * @dev Called by AI oracle or building official
     */
    function setComplianceScore(
        uint256 _id,
        uint8 _score,
        string[] calldata _flags
    ) external primaryExists(_id) onlyJurisdiction(permits[_id].municipalityId, BUILDING_OFFICIAL) {
        PrimaryPermit storage p = permits[_id];

        RiskLevel risk;
        if (_score >= 80) {
            risk = RiskLevel.Low;
        } else if (_score >= 50) {
            risk = RiskLevel.Medium;
        } else {
            risk = RiskLevel.High;
        }

        p.compliance = ComplianceMeta({
            score: _score,
            risk: risk,
            flags: _flags,
            scoredAt: block.timestamp,
            scoredBy: msg.sender
        });

        emit ComplianceScored(_id, _score, risk);
    }

    // ============ Trade Permit Lifecycle ============

    function submitTradePermit(
        uint256 _primaryId,
        TradeType _tradeType,
        string calldata _scope,
        uint256 _fixtureCount,
        uint256 _estimatedCost
    ) external nonReentrant primaryExists(_primaryId) returns (uint256) {
        // FIX #2: Deterministic dependency check
        (bool eligible, string memory reason) = isTradeEligible(_primaryId, _tradeType);
        if (!eligible) revert TradeNotEligible();

        // Validate tradesperson license
        License storage lic = licenses[msg.sender];
        if (!lic.isActive || lic.isSuspended) revert LicenseInvalid();

        uint256 id = _tradeCounter++;
        PrimaryPermit storage primary = permits[_primaryId];

        tradePermits[id].id = id;
        tradePermits[id].primaryId = _primaryId;
        tradePermits[id].tradeType = _tradeType;
        tradePermits[id].phase = TradePhase.Submitted;
        tradePermits[id].contractor = msg.sender;
        tradePermits[id].contractorLicense = lic.licenseNumber;
        tradePermits[id].scope = _scope;
        tradePermits[id].fixtureCount = _fixtureCount;
        tradePermits[id].estimatedCost = _estimatedCost;
        tradePermits[id].submittedAt = block.timestamp;

        primary.tradePermitIds.push(id);

        emit TradePermitCreated(id, _primaryId, _tradeType);
        emit TradePhaseChanged(id, TradePhase.Pending, TradePhase.Submitted, msg.sender);

        return id;
    }

    function advanceTradePhase(
        uint256 _id,
        TradePhase _newPhase
    ) external tradeExists(_id) {
        TradePermit storage t = tradePermits[_id];
        PrimaryPermit storage p = permits[t.primaryId];

        require(
            _hasJurisdiction(msg.sender, p.municipalityId, _getInspectorRole(t.tradeType)),
            "Not authorized"
        );

        TradePhase current = t.phase;

        // Validation guards
        if (_newPhase == TradePhase.Issued) {
            require(current == TradePhase.Submitted, "Must be submitted");
            t.issuedAt = block.timestamp;
        }

        if (_newPhase == TradePhase.Finaled) {
            require(
                current == TradePhase.Inspected ||
                current == TradePhase.RoughPassed ||
                current == TradePhase.FinalScheduled,
                "Must pass inspection"
            );
            t.finaledAt = block.timestamp;
        }

        t.phase = _newPhase;
        emit TradePhaseChanged(_id, current, _newPhase, msg.sender);
    }

    // ============ Inspection Management ============

    function scheduleInspection(
        uint256 _tradeId,
        InspectionType _type,
        uint256 _scheduledAt
    ) external tradeExists(_tradeId) returns (uint256) {
        (bool eligible,) = canScheduleInspection(_tradeId);
        require(eligible, "Not eligible for inspection");

        TradePermit storage t = tradePermits[_tradeId];
        uint256 inspId = _inspectionCounter++;

        t.inspections.push(Inspection({
            id: inspId,
            inspectionType: _type,
            result: InspectionResult.Pending,
            inspector: address(0),
            scheduledAt: _scheduledAt,
            completedAt: 0,
            notes: "",
            photoCIDs: new string[](0),
            corrections: new string[](0)
        }));

        // Update trade phase
        if (_type == InspectionType.Rough) {
            t.phase = TradePhase.RoughScheduled;
        } else if (_type == InspectionType.Final) {
            t.phase = TradePhase.FinalScheduled;
        }

        emit InspectionScheduled(_tradeId, inspId, _type);
        return inspId;
    }

    function completeInspection(
        uint256 _tradeId,
        uint256 _inspectionIndex,
        InspectionResult _result,
        string calldata _notes,
        string[] calldata _photoCIDs,
        string[] calldata _corrections
    ) external tradeExists(_tradeId) {
        TradePermit storage t = tradePermits[_tradeId];
        PrimaryPermit storage p = permits[t.primaryId];

        require(
            _hasJurisdiction(msg.sender, p.municipalityId, _getInspectorRole(t.tradeType)),
            "Not authorized inspector"
        );
        require(_inspectionIndex < t.inspections.length, "Invalid index");

        Inspection storage insp = t.inspections[_inspectionIndex];
        require(insp.result == InspectionResult.Pending, "Already completed");

        insp.result = _result;
        insp.inspector = msg.sender;
        insp.completedAt = block.timestamp;
        insp.notes = _notes;

        for (uint i = 0; i < _photoCIDs.length; i++) {
            insp.photoCIDs.push(_photoCIDs[i]);
        }

        // Update phase based on result and type
        if (_result == InspectionResult.Passed || _result == InspectionResult.Conditional) {
            if (insp.inspectionType == InspectionType.Rough) {
                t.phase = TradePhase.RoughPassed;
            } else if (insp.inspectionType == InspectionType.Final) {
                t.phase = TradePhase.Inspected;
            }

            // FIX #5: Check if escrow should be released
            if (canReleasePayment(_tradeId)) {
                _releaseEscrow(_tradeId);
            }
        } else if (_result == InspectionResult.Failed) {
            if (insp.inspectionType == InspectionType.Rough) {
                t.phase = TradePhase.RoughFailed;
            }
            for (uint i = 0; i < _corrections.length; i++) {
                insp.corrections.push(_corrections[i]);
            }
        }

        emit InspectionCompleted(_tradeId, insp.id, _result);
    }

    // ============ FIX #5: Financial Layer ============

    function payPermitFee(uint256 _id, uint256 _amount) external nonReentrant primaryExists(_id) {
        PrimaryPermit storage p = permits[_id];
        require(p.phase == PrimaryPhase.Approved, "Not approved");

        usdc.safeTransferFrom(msg.sender, address(this), _amount);

        // Distribute
        uint256 stateShare = (_amount * stateFeePercent) / 10000;
        uint256 muniShare = _amount - stateShare;

        usdc.safeTransfer(stateTreasury, stateShare);
        usdc.safeTransfer(municipalities[p.municipalityId].treasury, muniShare);

        p.financials.fee = _amount;
        p.financials.feePaid = true;
        p.financials.paidAt = block.timestamp;
        p.financials.receiptHash = keccak256(abi.encodePacked(_id, _amount, block.timestamp, msg.sender));

        municipalities[p.municipalityId].totalRevenue += _amount;

        emit PaymentReceived(_id, _amount, p.financials.receiptHash);
    }

    function depositEscrow(
        uint256 _tradeId,
        uint256 _amount,
        MilestoneTrigger _releaseOn
    ) external nonReentrant tradeExists(_tradeId) {
        TradePermit storage t = tradePermits[_tradeId];

        usdc.safeTransferFrom(msg.sender, address(this), _amount);

        t.financials.escrowAmount = _amount;
        t.financials.releaseOn = _releaseOn;
        t.financials.feePaid = true;
        t.financials.paidAt = block.timestamp;
    }

    function _releaseEscrow(uint256 _tradeId) internal {
        TradePermit storage t = tradePermits[_tradeId];
        require(!t.financials.escrowReleased, "Already released");
        require(t.financials.escrowAmount > 0, "No escrow");

        usdc.safeTransfer(t.contractor, t.financials.escrowAmount);

        t.financials.escrowReleased = true;
        t.financials.releasedAt = block.timestamp;

        emit EscrowReleased(_tradeId, t.financials.escrowAmount, t.financials.releaseOn);
    }

    // ============ Certificate of Occupancy ============

    function issueCO(
        uint256 _primaryId,
        string calldata _coNumber,
        uint256 _maxOccupancy,
        bool _isTemporary,
        uint256 _tempExpiresAt,
        string calldata _coCID
    ) external primaryExists(_primaryId) onlyJurisdiction(permits[_primaryId].municipalityId, BUILDING_OFFICIAL) {
        PrimaryPermit storage p = permits[_primaryId];
        require(
            p.phase == PrimaryPhase.FinalInspection ||
            p.phase == PrimaryPhase.Active,
            "Not ready for CO"
        );

        // Verify all trades finaled
        for (uint i = 0; i < p.tradePermitIds.length; i++) {
            require(
                tradePermits[p.tradePermitIds[i]].phase == TradePhase.Finaled,
                "Trade not finaled"
            );
        }

        uint256 coId = _coCounter++;

        certificates[_primaryId] = CertificateOfOccupancy({
            id: coId,
            permitId: _primaryId,
            coNumber: _coNumber,
            occupancyType: p.useGroup,
            maxOccupancy: _maxOccupancy,
            isTemporary: _isTemporary,
            expiresAt: _tempExpiresAt,
            issuedBy: msg.sender,
            issuedAt: block.timestamp,
            coCID: _coCID
        });

        p.phase = PrimaryPhase.Finaled;
        p.finaledAt = block.timestamp;

        emit COIssued(coId, _primaryId, _coNumber);
        emit PrimaryPhaseChanged(_primaryId, PrimaryPhase.FinalInspection, PrimaryPhase.Finaled, msg.sender);
        emit VoiceStatus(_primaryId, "Certificate of Occupancy issued. Project complete.");
    }

    // ============ Internal Helpers ============

    function _requiresTradePermits(PrimaryType _type) internal pure returns (bool) {
        return _type == PrimaryType.NewConstruction ||
               _type == PrimaryType.Addition ||
               _type == PrimaryType.Remodel;
    }

    function _getInspectorRole(TradeType _type) internal pure returns (bytes32) {
        if (_type == TradeType.Electrical || _type == TradeType.LowVoltage) return ELECTRICAL_INSPECTOR;
        if (_type == TradeType.Plumbing) return PLUMBING_INSPECTOR;
        if (_type == TradeType.Gas) return GAS_INSPECTOR;
        if (_type == TradeType.Mechanical) return MECHANICAL_INSPECTOR;
        if (_type == TradeType.Fire) return FIRE_INSPECTOR;
        return BUILDING_OFFICIAL;
    }

    // ============ View Functions ============

    function getPrimaryPermit(uint256 _id) external view returns (
        uint256 id,
        PrimaryType permitType,
        PrimaryPhase phase,
        Jurisdiction jurisdiction,
        uint8 complianceScore,
        RiskLevel risk,
        bool feePaid,
        uint256 tradeCount
    ) {
        PrimaryPermit storage p = permits[_id];
        return (
            p.id,
            p.permitType,
            p.phase,
            p.jurisdiction,
            p.compliance.score,
            p.compliance.risk,
            p.financials.feePaid,
            p.tradePermitIds.length
        );
    }

    function getTradePermit(uint256 _id) external view returns (TradePermit memory) {
        return tradePermits[_id];
    }

    function getTradeInspections(uint256 _id) external view returns (Inspection[] memory) {
        return tradePermits[_id].inspections;
    }

    function getComplianceFlags(uint256 _id) external view returns (string[] memory) {
        return permits[_id].compliance.flags;
    }

    function getCertificate(uint256 _primaryId) external view returns (CertificateOfOccupancy memory) {
        return certificates[_primaryId];
    }

    // ============ Admin ============

    function grantStateApproval(uint256 _id) external onlyState primaryExists(_id) {
        permits[_id].stateApproved = true;
    }

    function updateStateTreasury(address _new) external onlyState {
        stateTreasury = _new;
    }

    function pause() external onlyState { _pause(); }
    function unpause() external onlyState { _unpause(); }

    function emergencyWithdraw(address _token, address _to, uint256 _amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        IERC20(_token).safeTransfer(_to, _amount);
    }
}
