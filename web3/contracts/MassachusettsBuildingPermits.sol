// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MassachusettsBuildingPermits
 * @author NoblePort ETF - Building Permits Module
 * @notice Smart contract for managing building permits in Massachusetts
 * @dev Integrates with ENS-based DID system for identity verification
 *
 * This contract implements the Massachusetts State Building Code (780 CMR)
 * permit process on-chain, providing transparency, immutability, and
 * efficient processing for construction permits across the Commonwealth.
 */

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract MassachusettsBuildingPermits is AccessControl, ReentrancyGuard, Pausable {
    using Counters for Counters.Counter;

    // ============ Constants ============

    bytes32 public constant STATE_ADMIN_ROLE = keccak256("STATE_ADMIN_ROLE");
    bytes32 public constant MUNICIPALITY_ROLE = keccak256("MUNICIPALITY_ROLE");
    bytes32 public constant INSPECTOR_ROLE = keccak256("INSPECTOR_ROLE");
    bytes32 public constant CONTRACTOR_ROLE = keccak256("CONTRACTOR_ROLE");

    // Massachusetts Building Code Reference
    string public constant MA_BUILDING_CODE = "780 CMR - 9th Edition";

    // ============ Enums ============

    enum PermitType {
        RESIDENTIAL_NEW_CONSTRUCTION,   // New single/multi-family homes
        RESIDENTIAL_RENOVATION,          // Alterations to existing residential
        RESIDENTIAL_ADDITION,            // Additions to existing residential
        COMMERCIAL_NEW_CONSTRUCTION,     // New commercial buildings
        COMMERCIAL_RENOVATION,           // Alterations to existing commercial
        COMMERCIAL_TENANT_FITOUT,        // Interior commercial buildout
        INDUSTRIAL_NEW_CONSTRUCTION,     // New industrial facilities
        INDUSTRIAL_RENOVATION,           // Alterations to existing industrial
        DEMOLITION,                      // Full or partial demolition
        MECHANICAL,                      // HVAC systems
        ELECTRICAL,                      // Electrical work
        PLUMBING,                        // Plumbing systems
        FIRE_PROTECTION,                 // Sprinklers, fire alarms
        SIGN,                            // Signage installation
        FENCE,                           // Fence/wall construction
        ROOFING,                         // Roof replacement/repair
        SIDING,                          // Exterior siding
        DECK_PORCH,                      // Deck or porch construction
        SWIMMING_POOL,                   // Pool installation
        SOLAR_PANELS,                    // Solar/PV installation
        ACCESSORY_DWELLING_UNIT,         // ADU per MA Housing Choice Act
        FOUNDATION_ONLY,                 // Foundation work
        TEMPORARY_STRUCTURE              // Temporary buildings/tents
    }

    enum PermitStatus {
        DRAFT,                 // Initial application created
        SUBMITTED,             // Submitted for review
        UNDER_REVIEW,          // Being reviewed by municipality
        ADDITIONAL_INFO_REQUIRED, // More information needed
        APPROVED,              // Permit approved, fees pending
        FEES_PAID,             // Fees paid, permit active
        ACTIVE,                // Construction in progress
        INSPECTION_SCHEDULED,  // Inspection scheduled
        INSPECTION_FAILED,     // Failed inspection
        INSPECTION_PASSED,     // Passed inspection
        FINAL_INSPECTION,      // Final inspection phase
        COMPLETED,             // Construction complete, CO issued
        EXPIRED,               // Permit expired
        REVOKED,               // Permit revoked
        CANCELLED              // Cancelled by applicant
    }

    enum InspectionType {
        FOUNDATION,            // Foundation inspection
        ROUGH_FRAMING,         // Framing before drywall
        ROUGH_ELECTRICAL,      // Electrical before drywall
        ROUGH_PLUMBING,        // Plumbing before drywall
        ROUGH_MECHANICAL,      // HVAC before drywall
        INSULATION,            // Insulation inspection
        FIRE_STOPPING,         // Fire stopping inspection
        FINAL_ELECTRICAL,      // Final electrical
        FINAL_PLUMBING,        // Final plumbing
        FINAL_MECHANICAL,      // Final HVAC
        FINAL_BUILDING,        // Final building inspection
        CERTIFICATE_OF_OCCUPANCY // CO inspection
    }

    // ============ Structs ============

    struct Municipality {
        bytes32 municipalityId;
        string name;
        string county;
        address treasury;
        bool isActive;
        uint256 baseFeeMultiplier; // Basis points (100 = 1x)
        uint256 totalPermitsIssued;
        uint256 createdAt;
    }

    struct PropertyAddress {
        string streetNumber;
        string streetName;
        string unit;
        string city;
        string zipCode;
        bytes32 municipalityId;
        string parcelId;           // Assessor's parcel number
        string zoningDistrict;     // Zoning classification
    }

    struct Applicant {
        address wallet;
        string ensName;            // ENS DID (e.g., contractor.nobleport.eth)
        string companyName;
        string licenseNumber;      // MA contractor license
        string phoneNumber;
        string email;
        bool isVerified;
    }

    struct PermitApplication {
        uint256 permitId;
        bytes32 municipalityId;
        PermitType permitType;
        PermitStatus status;
        PropertyAddress propertyAddress;
        Applicant applicant;
        address propertyOwner;
        string projectDescription;
        uint256 estimatedCost;     // In wei (can represent USD cents)
        uint256 squareFootage;
        uint256 applicationFee;
        uint256 permitFee;
        uint256 totalFeesPaid;
        uint256 submittedAt;
        uint256 approvedAt;
        uint256 expiresAt;
        uint256 completedAt;
        string[] documentHashes;   // IPFS hashes of submitted documents
        bool requiresStateReview;  // For projects over threshold
    }

    struct Inspection {
        uint256 inspectionId;
        uint256 permitId;
        InspectionType inspectionType;
        address inspector;
        uint256 scheduledDate;
        uint256 completedDate;
        bool passed;
        string notes;
        string[] photoHashes;      // IPFS hashes of inspection photos
    }

    struct ReviewComment {
        uint256 commentId;
        uint256 permitId;
        address reviewer;
        string comment;
        uint256 timestamp;
        bool requiresResponse;
    }

    // ============ State Variables ============

    Counters.Counter private _permitIdCounter;
    Counters.Counter private _inspectionIdCounter;
    Counters.Counter private _commentIdCounter;

    // Massachusetts state-level settings
    uint256 public stateReviewThreshold = 1_000_000 * 10**18; // $1M projects require state review
    uint256 public permitValidityPeriod = 365 days;           // Standard permit validity
    uint256 public maxExtensionPeriod = 180 days;             // Maximum extension allowed
    address public stateTreasury;

    // Fee structure (in basis points, 10000 = 100%)
    uint256 public baseFeePerSquareFoot = 0.50 * 10**18;     // $0.50 per sq ft
    uint256 public minimumPermitFee = 50 * 10**18;           // $50 minimum
    uint256 public planReviewFeePercent = 6500;              // 65% of permit fee
    uint256 public stateFeePercent = 500;                    // 5% goes to state

    // Mappings
    mapping(bytes32 => Municipality) public municipalities;
    mapping(uint256 => PermitApplication) public permits;
    mapping(uint256 => Inspection[]) public permitInspections;
    mapping(uint256 => ReviewComment[]) public permitComments;
    mapping(address => uint256[]) public applicantPermits;
    mapping(bytes32 => uint256[]) public municipalityPermits;
    mapping(address => bool) public verifiedContractors;
    mapping(string => bool) public registeredLicenses;

    // Arrays for enumeration
    bytes32[] public municipalityList;

    // ============ Events ============

    event MunicipalityRegistered(
        bytes32 indexed municipalityId,
        string name,
        string county,
        address treasury
    );

    event MunicipalityUpdated(
        bytes32 indexed municipalityId,
        address newTreasury,
        uint256 newFeeMultiplier
    );

    event PermitApplicationCreated(
        uint256 indexed permitId,
        bytes32 indexed municipalityId,
        PermitType permitType,
        address indexed applicant,
        string propertyAddress
    );

    event PermitStatusChanged(
        uint256 indexed permitId,
        PermitStatus previousStatus,
        PermitStatus newStatus,
        address changedBy
    );

    event PermitApproved(
        uint256 indexed permitId,
        address approvedBy,
        uint256 permitFee,
        uint256 expiresAt
    );

    event PermitFeePaid(
        uint256 indexed permitId,
        uint256 amount,
        address paidBy
    );

    event InspectionScheduled(
        uint256 indexed inspectionId,
        uint256 indexed permitId,
        InspectionType inspectionType,
        uint256 scheduledDate
    );

    event InspectionCompleted(
        uint256 indexed inspectionId,
        uint256 indexed permitId,
        bool passed,
        address inspector
    );

    event CertificateOfOccupancyIssued(
        uint256 indexed permitId,
        bytes32 indexed municipalityId,
        uint256 issuedAt
    );

    event ReviewCommentAdded(
        uint256 indexed permitId,
        uint256 commentId,
        address reviewer
    );

    event ContractorVerified(
        address indexed contractor,
        string licenseNumber,
        string ensName
    );

    event DocumentAdded(
        uint256 indexed permitId,
        string documentHash,
        address addedBy
    );

    event PermitExtended(
        uint256 indexed permitId,
        uint256 previousExpiry,
        uint256 newExpiry
    );

    // ============ Modifiers ============

    modifier onlyMunicipality(bytes32 _municipalityId) {
        require(
            hasRole(MUNICIPALITY_ROLE, msg.sender) || hasRole(STATE_ADMIN_ROLE, msg.sender),
            "Not authorized for this municipality"
        );
        _;
    }

    modifier onlyInspector() {
        require(
            hasRole(INSPECTOR_ROLE, msg.sender) || hasRole(STATE_ADMIN_ROLE, msg.sender),
            "Not an authorized inspector"
        );
        _;
    }

    modifier permitExists(uint256 _permitId) {
        require(permits[_permitId].permitId != 0, "Permit does not exist");
        _;
    }

    modifier onlyPermitApplicant(uint256 _permitId) {
        require(
            permits[_permitId].applicant.wallet == msg.sender ||
            permits[_permitId].propertyOwner == msg.sender,
            "Not permit applicant or property owner"
        );
        _;
    }

    // ============ Constructor ============

    constructor(address _stateTreasury) {
        require(_stateTreasury != address(0), "Invalid state treasury");

        stateTreasury = _stateTreasury;

        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(STATE_ADMIN_ROLE, msg.sender);

        // Initialize permit counter starting at 1
        _permitIdCounter.increment();
        _inspectionIdCounter.increment();
        _commentIdCounter.increment();
    }

    // ============ Municipality Management ============

    /**
     * @notice Register a new Massachusetts municipality
     * @param _name Municipality name (e.g., "Boston", "Cambridge")
     * @param _county County name (e.g., "Suffolk", "Middlesex")
     * @param _treasury Treasury address for fee collection
     * @param _feeMultiplier Fee multiplier in basis points (10000 = 1x)
     */
    function registerMunicipality(
        string calldata _name,
        string calldata _county,
        address _treasury,
        uint256 _feeMultiplier
    ) external onlyRole(STATE_ADMIN_ROLE) {
        require(_treasury != address(0), "Invalid treasury address");
        require(_feeMultiplier >= 5000 && _feeMultiplier <= 20000, "Fee multiplier out of range");

        bytes32 municipalityId = keccak256(abi.encodePacked(_name, _county));
        require(municipalities[municipalityId].createdAt == 0, "Municipality already registered");

        municipalities[municipalityId] = Municipality({
            municipalityId: municipalityId,
            name: _name,
            county: _county,
            treasury: _treasury,
            isActive: true,
            baseFeeMultiplier: _feeMultiplier,
            totalPermitsIssued: 0,
            createdAt: block.timestamp
        });

        municipalityList.push(municipalityId);

        emit MunicipalityRegistered(municipalityId, _name, _county, _treasury);
    }

    /**
     * @notice Update municipality settings
     * @param _municipalityId Municipality identifier
     * @param _treasury New treasury address
     * @param _feeMultiplier New fee multiplier
     * @param _isActive Active status
     */
    function updateMunicipality(
        bytes32 _municipalityId,
        address _treasury,
        uint256 _feeMultiplier,
        bool _isActive
    ) external onlyRole(STATE_ADMIN_ROLE) {
        require(municipalities[_municipalityId].createdAt != 0, "Municipality not found");
        require(_treasury != address(0), "Invalid treasury address");

        Municipality storage muni = municipalities[_municipalityId];
        muni.treasury = _treasury;
        muni.baseFeeMultiplier = _feeMultiplier;
        muni.isActive = _isActive;

        emit MunicipalityUpdated(_municipalityId, _treasury, _feeMultiplier);
    }

    // ============ Contractor Management ============

    /**
     * @notice Verify a contractor's license
     * @param _contractor Contractor wallet address
     * @param _licenseNumber MA contractor license number
     * @param _ensName ENS name for DID verification
     */
    function verifyContractor(
        address _contractor,
        string calldata _licenseNumber,
        string calldata _ensName
    ) external onlyRole(STATE_ADMIN_ROLE) {
        require(_contractor != address(0), "Invalid contractor address");
        require(!registeredLicenses[_licenseNumber], "License already registered");

        verifiedContractors[_contractor] = true;
        registeredLicenses[_licenseNumber] = true;
        _grantRole(CONTRACTOR_ROLE, _contractor);

        emit ContractorVerified(_contractor, _licenseNumber, _ensName);
    }

    /**
     * @notice Revoke contractor verification
     * @param _contractor Contractor wallet address
     */
    function revokeContractorVerification(address _contractor)
        external
        onlyRole(STATE_ADMIN_ROLE)
    {
        verifiedContractors[_contractor] = false;
        _revokeRole(CONTRACTOR_ROLE, _contractor);
    }

    // ============ Permit Application ============

    /**
     * @notice Submit a new permit application
     * @param _municipalityId Target municipality
     * @param _permitType Type of permit
     * @param _propertyAddress Property address details
     * @param _applicant Applicant information
     * @param _propertyOwner Property owner address
     * @param _projectDescription Description of the project
     * @param _estimatedCost Estimated project cost
     * @param _squareFootage Project square footage
     * @param _documentHashes IPFS hashes of supporting documents
     */
    function submitPermitApplication(
        bytes32 _municipalityId,
        PermitType _permitType,
        PropertyAddress calldata _propertyAddress,
        Applicant calldata _applicant,
        address _propertyOwner,
        string calldata _projectDescription,
        uint256 _estimatedCost,
        uint256 _squareFootage,
        string[] calldata _documentHashes
    ) external payable nonReentrant whenNotPaused returns (uint256) {
        require(municipalities[_municipalityId].isActive, "Municipality not active");
        require(_propertyOwner != address(0), "Invalid property owner");
        require(bytes(_projectDescription).length > 0, "Description required");

        uint256 applicationFee = calculateApplicationFee(_permitType, _municipalityId);
        require(msg.value >= applicationFee, "Insufficient application fee");

        uint256 permitId = _permitIdCounter.current();
        _permitIdCounter.increment();

        bool requiresStateReview = _estimatedCost >= stateReviewThreshold;

        permits[permitId] = PermitApplication({
            permitId: permitId,
            municipalityId: _municipalityId,
            permitType: _permitType,
            status: PermitStatus.SUBMITTED,
            propertyAddress: _propertyAddress,
            applicant: _applicant,
            propertyOwner: _propertyOwner,
            projectDescription: _projectDescription,
            estimatedCost: _estimatedCost,
            squareFootage: _squareFootage,
            applicationFee: applicationFee,
            permitFee: 0,
            totalFeesPaid: msg.value,
            submittedAt: block.timestamp,
            approvedAt: 0,
            expiresAt: 0,
            completedAt: 0,
            documentHashes: _documentHashes,
            requiresStateReview: requiresStateReview
        });

        applicantPermits[msg.sender].push(permitId);
        municipalityPermits[_municipalityId].push(permitId);

        // Distribute application fee
        _distributeApplicationFee(_municipalityId, applicationFee);

        // Refund excess payment
        if (msg.value > applicationFee) {
            payable(msg.sender).transfer(msg.value - applicationFee);
        }

        string memory fullAddress = string(abi.encodePacked(
            _propertyAddress.streetNumber, " ",
            _propertyAddress.streetName, ", ",
            _propertyAddress.city, " MA ",
            _propertyAddress.zipCode
        ));

        emit PermitApplicationCreated(
            permitId,
            _municipalityId,
            _permitType,
            msg.sender,
            fullAddress
        );

        return permitId;
    }

    /**
     * @notice Add documents to an existing permit application
     * @param _permitId Permit identifier
     * @param _documentHashes IPFS hashes of new documents
     */
    function addDocuments(
        uint256 _permitId,
        string[] calldata _documentHashes
    ) external permitExists(_permitId) onlyPermitApplicant(_permitId) {
        PermitApplication storage permit = permits[_permitId];
        require(
            permit.status == PermitStatus.SUBMITTED ||
            permit.status == PermitStatus.UNDER_REVIEW ||
            permit.status == PermitStatus.ADDITIONAL_INFO_REQUIRED,
            "Cannot add documents in current status"
        );

        for (uint256 i = 0; i < _documentHashes.length; i++) {
            permit.documentHashes.push(_documentHashes[i]);
            emit DocumentAdded(_permitId, _documentHashes[i], msg.sender);
        }
    }

    // ============ Permit Review ============

    /**
     * @notice Begin review of a permit application
     * @param _permitId Permit identifier
     */
    function beginReview(uint256 _permitId)
        external
        permitExists(_permitId)
        onlyMunicipality(permits[_permitId].municipalityId)
    {
        PermitApplication storage permit = permits[_permitId];
        require(permit.status == PermitStatus.SUBMITTED, "Not in submitted status");

        PermitStatus previousStatus = permit.status;
        permit.status = PermitStatus.UNDER_REVIEW;

        emit PermitStatusChanged(_permitId, previousStatus, permit.status, msg.sender);
    }

    /**
     * @notice Request additional information from applicant
     * @param _permitId Permit identifier
     * @param _comment Comment explaining what is needed
     */
    function requestAdditionalInfo(
        uint256 _permitId,
        string calldata _comment
    ) external permitExists(_permitId) onlyMunicipality(permits[_permitId].municipalityId) {
        PermitApplication storage permit = permits[_permitId];
        require(
            permit.status == PermitStatus.UNDER_REVIEW,
            "Not under review"
        );

        PermitStatus previousStatus = permit.status;
        permit.status = PermitStatus.ADDITIONAL_INFO_REQUIRED;

        uint256 commentId = _commentIdCounter.current();
        _commentIdCounter.increment();

        permitComments[_permitId].push(ReviewComment({
            commentId: commentId,
            permitId: _permitId,
            reviewer: msg.sender,
            comment: _comment,
            timestamp: block.timestamp,
            requiresResponse: true
        }));

        emit PermitStatusChanged(_permitId, previousStatus, permit.status, msg.sender);
        emit ReviewCommentAdded(_permitId, commentId, msg.sender);
    }

    /**
     * @notice Approve a permit application
     * @param _permitId Permit identifier
     * @param _conditions Any conditions for approval
     */
    function approvePermit(
        uint256 _permitId,
        string calldata _conditions
    ) external permitExists(_permitId) onlyMunicipality(permits[_permitId].municipalityId) {
        PermitApplication storage permit = permits[_permitId];
        require(
            permit.status == PermitStatus.UNDER_REVIEW ||
            permit.status == PermitStatus.ADDITIONAL_INFO_REQUIRED,
            "Cannot approve in current status"
        );

        // If state review required, ensure state admin approves
        if (permit.requiresStateReview) {
            require(hasRole(STATE_ADMIN_ROLE, msg.sender), "State review required");
        }

        PermitStatus previousStatus = permit.status;
        permit.status = PermitStatus.APPROVED;
        permit.approvedAt = block.timestamp;
        permit.permitFee = calculatePermitFee(
            permit.permitType,
            permit.municipalityId,
            permit.squareFootage,
            permit.estimatedCost
        );

        if (bytes(_conditions).length > 0) {
            uint256 commentId = _commentIdCounter.current();
            _commentIdCounter.increment();

            permitComments[_permitId].push(ReviewComment({
                commentId: commentId,
                permitId: _permitId,
                reviewer: msg.sender,
                comment: string(abi.encodePacked("APPROVAL CONDITIONS: ", _conditions)),
                timestamp: block.timestamp,
                requiresResponse: false
            }));
        }

        emit PermitStatusChanged(_permitId, previousStatus, permit.status, msg.sender);
        emit PermitApproved(_permitId, msg.sender, permit.permitFee, 0);
    }

    /**
     * @notice Reject a permit application
     * @param _permitId Permit identifier
     * @param _reason Reason for rejection
     */
    function rejectPermit(
        uint256 _permitId,
        string calldata _reason
    ) external permitExists(_permitId) onlyMunicipality(permits[_permitId].municipalityId) {
        PermitApplication storage permit = permits[_permitId];
        require(
            permit.status == PermitStatus.UNDER_REVIEW ||
            permit.status == PermitStatus.ADDITIONAL_INFO_REQUIRED,
            "Cannot reject in current status"
        );

        PermitStatus previousStatus = permit.status;
        permit.status = PermitStatus.CANCELLED;

        uint256 commentId = _commentIdCounter.current();
        _commentIdCounter.increment();

        permitComments[_permitId].push(ReviewComment({
            commentId: commentId,
            permitId: _permitId,
            reviewer: msg.sender,
            comment: string(abi.encodePacked("REJECTION: ", _reason)),
            timestamp: block.timestamp,
            requiresResponse: false
        }));

        emit PermitStatusChanged(_permitId, previousStatus, permit.status, msg.sender);
    }

    // ============ Fee Payment ============

    /**
     * @notice Pay permit fees after approval
     * @param _permitId Permit identifier
     */
    function payPermitFee(uint256 _permitId)
        external
        payable
        nonReentrant
        permitExists(_permitId)
    {
        PermitApplication storage permit = permits[_permitId];
        require(permit.status == PermitStatus.APPROVED, "Permit not approved");
        require(msg.value >= permit.permitFee, "Insufficient fee payment");

        permit.totalFeesPaid += msg.value;
        permit.status = PermitStatus.FEES_PAID;
        permit.expiresAt = block.timestamp + permitValidityPeriod;

        // Distribute permit fee
        _distributePermitFee(permit.municipalityId, permit.permitFee);

        // Update municipality stats
        municipalities[permit.municipalityId].totalPermitsIssued++;

        // Refund excess
        if (msg.value > permit.permitFee) {
            payable(msg.sender).transfer(msg.value - permit.permitFee);
        }

        emit PermitFeePaid(_permitId, permit.permitFee, msg.sender);
        emit PermitStatusChanged(
            _permitId,
            PermitStatus.APPROVED,
            PermitStatus.FEES_PAID,
            msg.sender
        );
    }

    // ============ Inspection Management ============

    /**
     * @notice Schedule an inspection
     * @param _permitId Permit identifier
     * @param _inspectionType Type of inspection
     * @param _scheduledDate Scheduled date timestamp
     * @param _inspector Assigned inspector address
     */
    function scheduleInspection(
        uint256 _permitId,
        InspectionType _inspectionType,
        uint256 _scheduledDate,
        address _inspector
    ) external permitExists(_permitId) onlyMunicipality(permits[_permitId].municipalityId) {
        require(hasRole(INSPECTOR_ROLE, _inspector), "Invalid inspector");
        require(_scheduledDate > block.timestamp, "Must be future date");

        PermitApplication storage permit = permits[_permitId];
        require(
            permit.status == PermitStatus.FEES_PAID ||
            permit.status == PermitStatus.ACTIVE ||
            permit.status == PermitStatus.INSPECTION_PASSED ||
            permit.status == PermitStatus.INSPECTION_FAILED,
            "Cannot schedule inspection in current status"
        );

        uint256 inspectionId = _inspectionIdCounter.current();
        _inspectionIdCounter.increment();

        permitInspections[_permitId].push(Inspection({
            inspectionId: inspectionId,
            permitId: _permitId,
            inspectionType: _inspectionType,
            inspector: _inspector,
            scheduledDate: _scheduledDate,
            completedDate: 0,
            passed: false,
            notes: "",
            photoHashes: new string[](0)
        }));

        if (permit.status == PermitStatus.FEES_PAID) {
            permit.status = PermitStatus.ACTIVE;
        }
        permit.status = PermitStatus.INSPECTION_SCHEDULED;

        emit InspectionScheduled(inspectionId, _permitId, _inspectionType, _scheduledDate);
    }

    /**
     * @notice Complete an inspection
     * @param _permitId Permit identifier
     * @param _inspectionIndex Index of inspection in array
     * @param _passed Whether inspection passed
     * @param _notes Inspector notes
     * @param _photoHashes IPFS hashes of inspection photos
     */
    function completeInspection(
        uint256 _permitId,
        uint256 _inspectionIndex,
        bool _passed,
        string calldata _notes,
        string[] calldata _photoHashes
    ) external permitExists(_permitId) onlyInspector {
        require(_inspectionIndex < permitInspections[_permitId].length, "Invalid inspection index");

        Inspection storage inspection = permitInspections[_permitId][_inspectionIndex];
        require(inspection.inspector == msg.sender, "Not assigned inspector");
        require(inspection.completedDate == 0, "Inspection already completed");

        inspection.completedDate = block.timestamp;
        inspection.passed = _passed;
        inspection.notes = _notes;

        for (uint256 i = 0; i < _photoHashes.length; i++) {
            inspection.photoHashes.push(_photoHashes[i]);
        }

        PermitApplication storage permit = permits[_permitId];
        PermitStatus previousStatus = permit.status;

        if (_passed) {
            // Check if this is the final inspection
            if (inspection.inspectionType == InspectionType.CERTIFICATE_OF_OCCUPANCY) {
                permit.status = PermitStatus.COMPLETED;
                permit.completedAt = block.timestamp;
                emit CertificateOfOccupancyIssued(_permitId, permit.municipalityId, block.timestamp);
            } else if (inspection.inspectionType == InspectionType.FINAL_BUILDING) {
                permit.status = PermitStatus.FINAL_INSPECTION;
            } else {
                permit.status = PermitStatus.INSPECTION_PASSED;
            }
        } else {
            permit.status = PermitStatus.INSPECTION_FAILED;
        }

        emit InspectionCompleted(inspection.inspectionId, _permitId, _passed, msg.sender);
        emit PermitStatusChanged(_permitId, previousStatus, permit.status, msg.sender);
    }

    // ============ Permit Management ============

    /**
     * @notice Extend permit validity
     * @param _permitId Permit identifier
     * @param _extensionDays Number of days to extend
     */
    function extendPermit(
        uint256 _permitId,
        uint256 _extensionDays
    ) external payable permitExists(_permitId) onlyMunicipality(permits[_permitId].municipalityId) {
        PermitApplication storage permit = permits[_permitId];
        require(
            permit.status == PermitStatus.ACTIVE ||
            permit.status == PermitStatus.INSPECTION_SCHEDULED ||
            permit.status == PermitStatus.INSPECTION_PASSED ||
            permit.status == PermitStatus.INSPECTION_FAILED,
            "Cannot extend in current status"
        );
        require(_extensionDays * 1 days <= maxExtensionPeriod, "Extension exceeds maximum");

        uint256 previousExpiry = permit.expiresAt;
        permit.expiresAt += _extensionDays * 1 days;

        emit PermitExtended(_permitId, previousExpiry, permit.expiresAt);
    }

    /**
     * @notice Mark a permit as expired
     * @param _permitId Permit identifier
     */
    function expirePermit(uint256 _permitId)
        external
        permitExists(_permitId)
        onlyMunicipality(permits[_permitId].municipalityId)
    {
        PermitApplication storage permit = permits[_permitId];
        require(block.timestamp > permit.expiresAt, "Permit not yet expired");
        require(permit.status != PermitStatus.COMPLETED, "Cannot expire completed permit");

        PermitStatus previousStatus = permit.status;
        permit.status = PermitStatus.EXPIRED;

        emit PermitStatusChanged(_permitId, previousStatus, permit.status, msg.sender);
    }

    /**
     * @notice Revoke a permit
     * @param _permitId Permit identifier
     * @param _reason Reason for revocation
     */
    function revokePermit(
        uint256 _permitId,
        string calldata _reason
    ) external permitExists(_permitId) onlyRole(STATE_ADMIN_ROLE) {
        PermitApplication storage permit = permits[_permitId];
        require(permit.status != PermitStatus.COMPLETED, "Cannot revoke completed permit");

        PermitStatus previousStatus = permit.status;
        permit.status = PermitStatus.REVOKED;

        uint256 commentId = _commentIdCounter.current();
        _commentIdCounter.increment();

        permitComments[_permitId].push(ReviewComment({
            commentId: commentId,
            permitId: _permitId,
            reviewer: msg.sender,
            comment: string(abi.encodePacked("REVOCATION: ", _reason)),
            timestamp: block.timestamp,
            requiresResponse: false
        }));

        emit PermitStatusChanged(_permitId, previousStatus, permit.status, msg.sender);
    }

    // ============ Fee Calculations ============

    /**
     * @notice Calculate application fee
     * @param _permitType Type of permit
     * @param _municipalityId Municipality identifier
     * @return Application fee amount
     */
    function calculateApplicationFee(
        PermitType _permitType,
        bytes32 _municipalityId
    ) public view returns (uint256) {
        uint256 baseFee;

        // Base fees by permit type (in wei, representing cents)
        if (_permitType == PermitType.RESIDENTIAL_NEW_CONSTRUCTION ||
            _permitType == PermitType.COMMERCIAL_NEW_CONSTRUCTION ||
            _permitType == PermitType.INDUSTRIAL_NEW_CONSTRUCTION) {
            baseFee = 200 * 10**18; // $200
        } else if (_permitType == PermitType.DEMOLITION) {
            baseFee = 150 * 10**18; // $150
        } else if (_permitType == PermitType.ELECTRICAL ||
                   _permitType == PermitType.PLUMBING ||
                   _permitType == PermitType.MECHANICAL) {
            baseFee = 75 * 10**18; // $75
        } else {
            baseFee = 100 * 10**18; // $100 default
        }

        // Apply municipality multiplier
        uint256 multiplier = municipalities[_municipalityId].baseFeeMultiplier;
        if (multiplier == 0) multiplier = 10000; // Default 1x

        return (baseFee * multiplier) / 10000;
    }

    /**
     * @notice Calculate total permit fee
     * @param _permitType Type of permit
     * @param _municipalityId Municipality identifier
     * @param _squareFootage Project square footage
     * @param _estimatedCost Estimated project cost
     * @return Total permit fee
     */
    function calculatePermitFee(
        PermitType _permitType,
        bytes32 _municipalityId,
        uint256 _squareFootage,
        uint256 _estimatedCost
    ) public view returns (uint256) {
        uint256 fee;

        // Calculate based on square footage
        uint256 sqftFee = (_squareFootage * baseFeePerSquareFoot) / 10**18;

        // Calculate based on estimated cost (0.5% of project cost)
        uint256 costFee = (_estimatedCost * 50) / 10000;

        // Use the higher of the two
        fee = sqftFee > costFee ? sqftFee : costFee;

        // Ensure minimum fee
        if (fee < minimumPermitFee) {
            fee = minimumPermitFee;
        }

        // Apply permit type multiplier
        uint256 typeMultiplier = _getPermitTypeMultiplier(_permitType);
        fee = (fee * typeMultiplier) / 10000;

        // Apply municipality multiplier
        uint256 muniMultiplier = municipalities[_municipalityId].baseFeeMultiplier;
        if (muniMultiplier == 0) muniMultiplier = 10000;
        fee = (fee * muniMultiplier) / 10000;

        // Add plan review fee
        fee += (fee * planReviewFeePercent) / 10000;

        return fee;
    }

    /**
     * @notice Get permit type fee multiplier
     * @param _permitType Type of permit
     * @return Multiplier in basis points
     */
    function _getPermitTypeMultiplier(PermitType _permitType) internal pure returns (uint256) {
        if (_permitType == PermitType.COMMERCIAL_NEW_CONSTRUCTION ||
            _permitType == PermitType.INDUSTRIAL_NEW_CONSTRUCTION) {
            return 15000; // 1.5x
        } else if (_permitType == PermitType.RESIDENTIAL_NEW_CONSTRUCTION) {
            return 12000; // 1.2x
        } else if (_permitType == PermitType.DEMOLITION) {
            return 8000; // 0.8x
        } else if (_permitType == PermitType.SOLAR_PANELS ||
                   _permitType == PermitType.ACCESSORY_DWELLING_UNIT) {
            return 7500; // 0.75x (incentivize green/housing)
        }
        return 10000; // 1x default
    }

    // ============ Fee Distribution ============

    /**
     * @notice Distribute application fee between municipality and state
     */
    function _distributeApplicationFee(bytes32 _municipalityId, uint256 _amount) internal {
        uint256 stateShare = (_amount * stateFeePercent) / 10000;
        uint256 muniShare = _amount - stateShare;

        payable(stateTreasury).transfer(stateShare);
        payable(municipalities[_municipalityId].treasury).transfer(muniShare);
    }

    /**
     * @notice Distribute permit fee between municipality and state
     */
    function _distributePermitFee(bytes32 _municipalityId, uint256 _amount) internal {
        uint256 stateShare = (_amount * stateFeePercent) / 10000;
        uint256 muniShare = _amount - stateShare;

        payable(stateTreasury).transfer(stateShare);
        payable(municipalities[_municipalityId].treasury).transfer(muniShare);
    }

    // ============ View Functions ============

    /**
     * @notice Get permit details
     * @param _permitId Permit identifier
     * @return Permit application struct
     */
    function getPermit(uint256 _permitId)
        external
        view
        permitExists(_permitId)
        returns (PermitApplication memory)
    {
        return permits[_permitId];
    }

    /**
     * @notice Get all inspections for a permit
     * @param _permitId Permit identifier
     * @return Array of inspections
     */
    function getPermitInspections(uint256 _permitId)
        external
        view
        returns (Inspection[] memory)
    {
        return permitInspections[_permitId];
    }

    /**
     * @notice Get all comments for a permit
     * @param _permitId Permit identifier
     * @return Array of review comments
     */
    function getPermitComments(uint256 _permitId)
        external
        view
        returns (ReviewComment[] memory)
    {
        return permitComments[_permitId];
    }

    /**
     * @notice Get all permits for an applicant
     * @param _applicant Applicant address
     * @return Array of permit IDs
     */
    function getApplicantPermits(address _applicant)
        external
        view
        returns (uint256[] memory)
    {
        return applicantPermits[_applicant];
    }

    /**
     * @notice Get all permits for a municipality
     * @param _municipalityId Municipality identifier
     * @return Array of permit IDs
     */
    function getMunicipalityPermits(bytes32 _municipalityId)
        external
        view
        returns (uint256[] memory)
    {
        return municipalityPermits[_municipalityId];
    }

    /**
     * @notice Get municipality details
     * @param _municipalityId Municipality identifier
     * @return Municipality struct
     */
    function getMunicipality(bytes32 _municipalityId)
        external
        view
        returns (Municipality memory)
    {
        return municipalities[_municipalityId];
    }

    /**
     * @notice Get all registered municipalities
     * @return Array of municipality IDs
     */
    function getAllMunicipalities() external view returns (bytes32[] memory) {
        return municipalityList;
    }

    /**
     * @notice Get total number of permits issued
     * @return Total permit count
     */
    function getTotalPermits() external view returns (uint256) {
        return _permitIdCounter.current() - 1;
    }

    /**
     * @notice Check if a permit is valid and active
     * @param _permitId Permit identifier
     * @return Whether permit is valid
     */
    function isPermitValid(uint256 _permitId) external view returns (bool) {
        if (permits[_permitId].permitId == 0) return false;

        PermitApplication storage permit = permits[_permitId];

        if (permit.status == PermitStatus.COMPLETED) return true;
        if (permit.status == PermitStatus.EXPIRED ||
            permit.status == PermitStatus.REVOKED ||
            permit.status == PermitStatus.CANCELLED) return false;

        if (permit.expiresAt != 0 && block.timestamp > permit.expiresAt) return false;

        return permit.status == PermitStatus.FEES_PAID ||
               permit.status == PermitStatus.ACTIVE ||
               permit.status == PermitStatus.INSPECTION_SCHEDULED ||
               permit.status == PermitStatus.INSPECTION_PASSED ||
               permit.status == PermitStatus.FINAL_INSPECTION;
    }

    // ============ Admin Functions ============

    /**
     * @notice Update state treasury address
     * @param _newTreasury New treasury address
     */
    function updateStateTreasury(address _newTreasury)
        external
        onlyRole(STATE_ADMIN_ROLE)
    {
        require(_newTreasury != address(0), "Invalid treasury address");
        stateTreasury = _newTreasury;
    }

    /**
     * @notice Update fee parameters
     * @param _baseFeePerSquareFoot New base fee per square foot
     * @param _minimumPermitFee New minimum permit fee
     * @param _planReviewFeePercent New plan review fee percentage
     * @param _stateFeePercent New state fee percentage
     */
    function updateFeeParameters(
        uint256 _baseFeePerSquareFoot,
        uint256 _minimumPermitFee,
        uint256 _planReviewFeePercent,
        uint256 _stateFeePercent
    ) external onlyRole(STATE_ADMIN_ROLE) {
        require(_stateFeePercent <= 1000, "State fee too high"); // Max 10%
        require(_planReviewFeePercent <= 10000, "Plan review fee too high"); // Max 100%

        baseFeePerSquareFoot = _baseFeePerSquareFoot;
        minimumPermitFee = _minimumPermitFee;
        planReviewFeePercent = _planReviewFeePercent;
        stateFeePercent = _stateFeePercent;
    }

    /**
     * @notice Update state review threshold
     * @param _newThreshold New threshold amount
     */
    function updateStateReviewThreshold(uint256 _newThreshold)
        external
        onlyRole(STATE_ADMIN_ROLE)
    {
        stateReviewThreshold = _newThreshold;
    }

    /**
     * @notice Grant inspector role
     * @param _inspector Inspector address
     */
    function addInspector(address _inspector) external onlyRole(STATE_ADMIN_ROLE) {
        _grantRole(INSPECTOR_ROLE, _inspector);
    }

    /**
     * @notice Revoke inspector role
     * @param _inspector Inspector address
     */
    function removeInspector(address _inspector) external onlyRole(STATE_ADMIN_ROLE) {
        _revokeRole(INSPECTOR_ROLE, _inspector);
    }

    /**
     * @notice Grant municipality role
     * @param _official Municipality official address
     */
    function addMunicipalityOfficial(address _official) external onlyRole(STATE_ADMIN_ROLE) {
        _grantRole(MUNICIPALITY_ROLE, _official);
    }

    /**
     * @notice Revoke municipality role
     * @param _official Municipality official address
     */
    function removeMunicipalityOfficial(address _official) external onlyRole(STATE_ADMIN_ROLE) {
        _revokeRole(MUNICIPALITY_ROLE, _official);
    }

    /**
     * @notice Pause contract operations
     */
    function pause() external onlyRole(STATE_ADMIN_ROLE) {
        _pause();
    }

    /**
     * @notice Unpause contract operations
     */
    function unpause() external onlyRole(STATE_ADMIN_ROLE) {
        _unpause();
    }

    /**
     * @notice Emergency withdrawal (only for stuck funds)
     * @param _to Recipient address
     * @param _amount Amount to withdraw
     */
    function emergencyWithdraw(address _to, uint256 _amount)
        external
        onlyRole(DEFAULT_ADMIN_ROLE)
    {
        require(_to != address(0), "Invalid recipient");
        require(address(this).balance >= _amount, "Insufficient balance");
        payable(_to).transfer(_amount);
    }

    // ============ Receive Function ============

    receive() external payable {}
}
