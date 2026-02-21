// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title HumanApprovalGateway
 * @author NoblePort ETF - Human-in-the-Loop Governance Module
 * @notice Enforces mandatory human approval for all legal, medical, and financial decisions
 * @dev No decision in these domains can be executed without explicit sign-off from
 *      qualified human approvers. AI systems, automated processes, and smart contract
 *      logic MUST route through this gateway before any binding action is taken.
 *
 * Core Invariant: Every legal, medical, and financial decision MUST receive the
 * required number of human approvals before execution. There is no bypass mechanism.
 *
 * Integrates with NoblePort's ENS-based DID system for approver identity verification.
 */

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

contract HumanApprovalGateway is AccessControl, ReentrancyGuard, Pausable {
    using Counters for Counters.Counter;

    // ============ Constants ============

    bytes32 public constant GOVERNANCE_ADMIN_ROLE = keccak256("GOVERNANCE_ADMIN_ROLE");
    bytes32 public constant LEGAL_APPROVER_ROLE = keccak256("LEGAL_APPROVER_ROLE");
    bytes32 public constant MEDICAL_APPROVER_ROLE = keccak256("MEDICAL_APPROVER_ROLE");
    bytes32 public constant FINANCIAL_APPROVER_ROLE = keccak256("FINANCIAL_APPROVER_ROLE");
    bytes32 public constant PROPOSER_ROLE = keccak256("PROPOSER_ROLE");

    // Minimum review period before a decision can be executed (even after quorum)
    uint256 public constant MIN_REVIEW_PERIOD = 1 hours;

    // Maximum time a decision can remain open before it expires
    uint256 public constant MAX_DECISION_LIFETIME = 30 days;

    // ============ Enums ============

    enum DecisionDomain {
        LEGAL,                       // Contracts, compliance, regulatory filings, litigation
        MEDICAL,                     // Patient care, treatment plans, drug administration, diagnoses
        FINANCIAL                    // Fund transfers, investment allocations, tax filings, audits
    }

    enum DecisionStatus {
        PROPOSED,                    // Decision submitted, awaiting human review
        UNDER_REVIEW,                // At least one approver has begun review
        APPROVED,                    // Required quorum reached, in mandatory cool-down
        REJECTED,                    // Decision rejected by an approver
        EXECUTED,                    // Decision approved and executed
        EXPIRED,                     // Decision expired without sufficient approvals
        ESCALATED,                   // Escalated for additional review
        CANCELLED                    // Cancelled by the proposer
    }

    enum Urgency {
        STANDARD,                    // Normal review timeline
        ELEVATED,                    // Faster review, same quorum requirements
        CRITICAL                     // Expedited review, same quorum requirements (no quorum reduction)
    }

    // ============ Structs ============

    struct HumanApprover {
        address wallet;
        string ensName;              // ENS DID (e.g., counsel.nobleport.eth)
        string fullName;
        string credential;          // Bar number, medical license, CPA number, etc.
        string jurisdiction;         // Jurisdiction or specialty
        DecisionDomain domain;
        bool isActive;
        uint256 registeredAt;
        uint256 totalDecisionsReviewed;
    }

    struct Decision {
        uint256 decisionId;
        DecisionDomain domain;
        DecisionStatus status;
        Urgency urgency;

        // Proposal details
        address proposer;
        string title;
        string description;
        string rationale;
        string[] documentHashes;     // IPFS hashes of supporting documents
        bytes actionPayload;         // Encoded action to execute upon approval
        address targetContract;      // Contract to call upon execution (address(0) if off-chain)

        // Approval tracking
        uint256 approvalsReceived;
        uint256 rejectionsReceived;
        uint256 quorumRequired;

        // Timestamps
        uint256 proposedAt;
        uint256 reviewStartedAt;
        uint256 approvedAt;
        uint256 executedAt;
        uint256 expiresAt;
    }

    struct ApprovalRecord {
        uint256 decisionId;
        address approver;
        string ensName;
        bool approved;               // true = approved, false = rejected
        string justification;        // Required written justification
        string[] reviewDocHashes;    // IPFS hashes of review notes
        uint256 timestamp;
    }

    struct EscalationRecord {
        uint256 decisionId;
        address escalatedBy;
        string reason;
        DecisionDomain escalatedToDomain;
        uint256 timestamp;
    }

    // ============ State Variables ============

    Counters.Counter private _decisionIdCounter;
    Counters.Counter private _approverIdCounter;

    // Domain-specific quorum requirements (minimum human approvals needed)
    mapping(DecisionDomain => uint256) public domainQuorum;

    // Domain-specific approver counts
    mapping(DecisionDomain => uint256) public domainApproverCount;

    // Core storage
    mapping(uint256 => Decision) public decisions;
    mapping(address => HumanApprover) public approvers;
    mapping(uint256 => ApprovalRecord[]) public decisionApprovals;
    mapping(uint256 => EscalationRecord[]) public decisionEscalations;

    // Lookup mappings
    mapping(address => uint256[]) public proposerDecisions;
    mapping(address => uint256[]) public approverDecisionHistory;
    mapping(DecisionDomain => uint256[]) public domainDecisions;

    // Prevents double-approval
    mapping(uint256 => mapping(address => bool)) public hasVoted;

    // Track all decision IDs
    uint256[] public allDecisionIds;

    // ============ Events ============

    event DecisionProposed(
        uint256 indexed decisionId,
        DecisionDomain indexed domain,
        address indexed proposer,
        string title,
        Urgency urgency,
        uint256 quorumRequired
    );

    event HumanApprovalSubmitted(
        uint256 indexed decisionId,
        address indexed approver,
        bool approved,
        string justification
    );

    event DecisionApproved(
        uint256 indexed decisionId,
        DecisionDomain indexed domain,
        uint256 approvalsReceived,
        uint256 timestamp
    );

    event DecisionRejected(
        uint256 indexed decisionId,
        DecisionDomain indexed domain,
        address indexed rejectedBy,
        string justification
    );

    event DecisionExecuted(
        uint256 indexed decisionId,
        DecisionDomain indexed domain,
        address indexed executor,
        uint256 timestamp
    );

    event DecisionEscalated(
        uint256 indexed decisionId,
        address indexed escalatedBy,
        string reason
    );

    event DecisionCancelled(
        uint256 indexed decisionId,
        address indexed cancelledBy
    );

    event DecisionExpired(
        uint256 indexed decisionId
    );

    event ApproverRegistered(
        address indexed approver,
        DecisionDomain indexed domain,
        string ensName,
        string credential
    );

    event ApproverDeactivated(
        address indexed approver,
        DecisionDomain indexed domain
    );

    event ApproverReactivated(
        address indexed approver,
        DecisionDomain indexed domain
    );

    event QuorumUpdated(
        DecisionDomain indexed domain,
        uint256 oldQuorum,
        uint256 newQuorum
    );

    event AutomatedActionBlocked(
        address indexed caller,
        DecisionDomain indexed domain,
        string reason
    );

    // ============ Modifiers ============

    modifier decisionExists(uint256 _decisionId) {
        require(decisions[_decisionId].proposedAt != 0, "Decision does not exist");
        _;
    }

    modifier onlyActiveApprover(DecisionDomain _domain) {
        require(approvers[msg.sender].isActive, "Not an active approver");
        require(approvers[msg.sender].domain == _domain, "Not authorized for this domain");
        _;
    }

    modifier notExpired(uint256 _decisionId) {
        require(block.timestamp <= decisions[_decisionId].expiresAt, "Decision has expired");
        _;
    }

    modifier inStatus(uint256 _decisionId, DecisionStatus _status) {
        require(
            decisions[_decisionId].status == _status,
            "Decision is not in the required status"
        );
        _;
    }

    modifier requiresHumanApproval(uint256 _decisionId) {
        Decision storage d = decisions[_decisionId];
        require(
            d.status == DecisionStatus.APPROVED,
            "Human approval quorum not yet reached"
        );
        require(
            d.approvedAt + MIN_REVIEW_PERIOD <= block.timestamp,
            "Mandatory review cool-down period has not elapsed"
        );
        _;
    }

    // ============ Constructor ============

    /**
     * @notice Initializes the gateway with default quorum requirements
     * @param _governanceAdmin Address of the initial governance administrator
     */
    constructor(address _governanceAdmin) {
        require(_governanceAdmin != address(0), "Invalid admin address");

        _grantRole(DEFAULT_ADMIN_ROLE, _governanceAdmin);
        _grantRole(GOVERNANCE_ADMIN_ROLE, _governanceAdmin);

        // Default quorum: at least 2 qualified humans must approve each domain
        domainQuorum[DecisionDomain.LEGAL] = 2;
        domainQuorum[DecisionDomain.MEDICAL] = 2;
        domainQuorum[DecisionDomain.FINANCIAL] = 2;
    }

    // ============ Approver Management ============

    /**
     * @notice Registers a qualified human approver for a specific decision domain
     * @dev Only governance admins can register approvers. Each approver must hold
     *      valid professional credentials (bar number, medical license, CPA, etc.)
     * @param _wallet Approver's Ethereum address
     * @param _ensName Approver's ENS name (e.g., counsel.nobleport.eth)
     * @param _fullName Approver's legal full name
     * @param _credential Professional credential identifier
     * @param _jurisdiction Jurisdiction or area of specialty
     * @param _domain Decision domain this approver is qualified for
     */
    function registerApprover(
        address _wallet,
        string calldata _ensName,
        string calldata _fullName,
        string calldata _credential,
        string calldata _jurisdiction,
        DecisionDomain _domain
    ) external onlyRole(GOVERNANCE_ADMIN_ROLE) {
        require(_wallet != address(0), "Invalid approver address");
        require(bytes(_fullName).length > 0, "Full name required");
        require(bytes(_credential).length > 0, "Professional credential required");
        require(!approvers[_wallet].isActive, "Approver already active");

        approvers[_wallet] = HumanApprover({
            wallet: _wallet,
            ensName: _ensName,
            fullName: _fullName,
            credential: _credential,
            jurisdiction: _jurisdiction,
            domain: _domain,
            isActive: true,
            registeredAt: block.timestamp,
            totalDecisionsReviewed: 0
        });

        // Grant the corresponding role
        if (_domain == DecisionDomain.LEGAL) {
            _grantRole(LEGAL_APPROVER_ROLE, _wallet);
        } else if (_domain == DecisionDomain.MEDICAL) {
            _grantRole(MEDICAL_APPROVER_ROLE, _wallet);
        } else if (_domain == DecisionDomain.FINANCIAL) {
            _grantRole(FINANCIAL_APPROVER_ROLE, _wallet);
        }

        domainApproverCount[_domain]++;

        emit ApproverRegistered(_wallet, _domain, _ensName, _credential);
    }

    /**
     * @notice Deactivates an approver, preventing them from voting on new decisions
     * @param _wallet Address of the approver to deactivate
     */
    function deactivateApprover(address _wallet) external onlyRole(GOVERNANCE_ADMIN_ROLE) {
        require(approvers[_wallet].isActive, "Approver not active");

        DecisionDomain domain = approvers[_wallet].domain;
        approvers[_wallet].isActive = false;
        domainApproverCount[domain]--;

        // Ensure deactivation doesn't make quorum impossible
        require(
            domainApproverCount[domain] >= domainQuorum[domain],
            "Cannot deactivate: would make quorum impossible"
        );

        emit ApproverDeactivated(_wallet, domain);
    }

    /**
     * @notice Reactivates a previously deactivated approver
     * @param _wallet Address of the approver to reactivate
     */
    function reactivateApprover(address _wallet) external onlyRole(GOVERNANCE_ADMIN_ROLE) {
        require(approvers[_wallet].wallet != address(0), "Approver not registered");
        require(!approvers[_wallet].isActive, "Approver already active");

        approvers[_wallet].isActive = true;
        domainApproverCount[approvers[_wallet].domain]++;

        emit ApproverReactivated(_wallet, approvers[_wallet].domain);
    }

    // ============ Quorum Management ============

    /**
     * @notice Updates the quorum requirement for a decision domain
     * @dev Quorum must be at least 1 and cannot exceed the current number of active approvers
     * @param _domain The decision domain to update
     * @param _newQuorum The new minimum number of human approvals required
     */
    function updateQuorum(
        DecisionDomain _domain,
        uint256 _newQuorum
    ) external onlyRole(GOVERNANCE_ADMIN_ROLE) {
        require(_newQuorum >= 1, "Quorum must be at least 1 human approver");
        require(
            _newQuorum <= domainApproverCount[_domain],
            "Quorum cannot exceed number of active approvers"
        );

        uint256 oldQuorum = domainQuorum[_domain];
        domainQuorum[_domain] = _newQuorum;

        emit QuorumUpdated(_domain, oldQuorum, _newQuorum);
    }

    // ============ Decision Lifecycle ============

    /**
     * @notice Proposes a new decision that requires mandatory human approval
     * @dev This is the entry point for ALL legal, medical, and financial decisions.
     *      Both human users and AI/automated systems MUST use this function.
     * @param _domain The decision domain (LEGAL, MEDICAL, or FINANCIAL)
     * @param _title Short title describing the decision
     * @param _description Full description of the proposed action
     * @param _rationale Reasoning behind the proposed decision
     * @param _documentHashes IPFS hashes of supporting documents
     * @param _actionPayload Encoded calldata to execute on approval (empty for off-chain actions)
     * @param _targetContract Contract to call on execution (address(0) for off-chain actions)
     * @param _urgency Urgency level of the decision
     * @return decisionId The unique identifier for this decision
     */
    function proposeDecision(
        DecisionDomain _domain,
        string calldata _title,
        string calldata _description,
        string calldata _rationale,
        string[] calldata _documentHashes,
        bytes calldata _actionPayload,
        address _targetContract,
        Urgency _urgency
    ) external whenNotPaused onlyRole(PROPOSER_ROLE) returns (uint256 decisionId) {
        require(bytes(_title).length > 0, "Title is required");
        require(bytes(_description).length > 0, "Description is required");
        require(bytes(_rationale).length > 0, "Rationale is required");
        require(
            domainApproverCount[_domain] >= domainQuorum[_domain],
            "Insufficient approvers registered for this domain"
        );

        _decisionIdCounter.increment();
        decisionId = _decisionIdCounter.current();

        uint256 quorum = domainQuorum[_domain];

        Decision storage d = decisions[decisionId];
        d.decisionId = decisionId;
        d.domain = _domain;
        d.status = DecisionStatus.PROPOSED;
        d.urgency = _urgency;
        d.proposer = msg.sender;
        d.title = _title;
        d.description = _description;
        d.rationale = _rationale;
        d.documentHashes = _documentHashes;
        d.actionPayload = _actionPayload;
        d.targetContract = _targetContract;
        d.approvalsReceived = 0;
        d.rejectionsReceived = 0;
        d.quorumRequired = quorum;
        d.proposedAt = block.timestamp;
        d.expiresAt = block.timestamp + MAX_DECISION_LIFETIME;

        proposerDecisions[msg.sender].push(decisionId);
        domainDecisions[_domain].push(decisionId);
        allDecisionIds.push(decisionId);

        emit DecisionProposed(decisionId, _domain, msg.sender, _title, _urgency, quorum);

        return decisionId;
    }

    /**
     * @notice Submit a human approval or rejection for a pending decision
     * @dev THIS IS THE CRITICAL HUMAN-IN-THE-LOOP FUNCTION. Only qualified,
     *      credentialed human approvers in the correct domain can call this.
     *      A written justification is mandatory for both approvals and rejections.
     * @param _decisionId The decision to vote on
     * @param _approved True to approve, false to reject
     * @param _justification Written reasoning for the approval/rejection (mandatory)
     * @param _reviewDocHashes IPFS hashes of any review documents or notes
     */
    function submitHumanApproval(
        uint256 _decisionId,
        bool _approved,
        string calldata _justification,
        string[] calldata _reviewDocHashes
    )
        external
        whenNotPaused
        nonReentrant
        decisionExists(_decisionId)
        notExpired(_decisionId)
        onlyActiveApprover(decisions[_decisionId].domain)
    {
        Decision storage d = decisions[_decisionId];

        require(
            d.status == DecisionStatus.PROPOSED ||
            d.status == DecisionStatus.UNDER_REVIEW ||
            d.status == DecisionStatus.ESCALATED,
            "Decision is not open for review"
        );
        require(!hasVoted[_decisionId][msg.sender], "Approver has already voted");
        require(bytes(_justification).length > 0, "Written justification is mandatory");

        // Record the vote
        hasVoted[_decisionId][msg.sender] = true;

        ApprovalRecord memory record = ApprovalRecord({
            decisionId: _decisionId,
            approver: msg.sender,
            ensName: approvers[msg.sender].ensName,
            approved: _approved,
            justification: _justification,
            reviewDocHashes: _reviewDocHashes,
            timestamp: block.timestamp
        });
        decisionApprovals[_decisionId].push(record);

        // Update approver stats
        approvers[msg.sender].totalDecisionsReviewed++;
        approverDecisionHistory[msg.sender].push(_decisionId);

        // Transition to UNDER_REVIEW on first vote
        if (d.status == DecisionStatus.PROPOSED) {
            d.status = DecisionStatus.UNDER_REVIEW;
            d.reviewStartedAt = block.timestamp;
        }

        if (_approved) {
            d.approvalsReceived++;

            emit HumanApprovalSubmitted(_decisionId, msg.sender, true, _justification);

            // Check if quorum has been reached
            if (d.approvalsReceived >= d.quorumRequired) {
                d.status = DecisionStatus.APPROVED;
                d.approvedAt = block.timestamp;

                emit DecisionApproved(
                    _decisionId,
                    d.domain,
                    d.approvalsReceived,
                    block.timestamp
                );
            }
        } else {
            d.rejectionsReceived++;
            d.status = DecisionStatus.REJECTED;

            emit DecisionRejected(_decisionId, d.domain, msg.sender, _justification);
            emit HumanApprovalSubmitted(_decisionId, msg.sender, false, _justification);
        }
    }

    /**
     * @notice Executes a decision that has received full human approval and passed the cool-down
     * @dev Can only be called after quorum is met AND the mandatory review period has elapsed.
     *      For on-chain actions, the encoded payload is forwarded to the target contract.
     *      For off-chain actions (targetContract == address(0)), this marks the decision
     *      as authorized for off-chain execution.
     * @param _decisionId The decision to execute
     */
    function executeDecision(uint256 _decisionId)
        external
        whenNotPaused
        nonReentrant
        decisionExists(_decisionId)
        notExpired(_decisionId)
        requiresHumanApproval(_decisionId)
    {
        Decision storage d = decisions[_decisionId];
        require(d.status == DecisionStatus.APPROVED, "Decision is not approved");

        d.status = DecisionStatus.EXECUTED;
        d.executedAt = block.timestamp;

        // Execute on-chain action if target contract is specified
        if (d.targetContract != address(0) && d.actionPayload.length > 0) {
            (bool success, ) = d.targetContract.call(d.actionPayload);
            require(success, "On-chain action execution failed");
        }

        emit DecisionExecuted(_decisionId, d.domain, msg.sender, block.timestamp);
    }

    /**
     * @notice Escalates a decision for additional review, resetting it for broader input
     * @dev Any active approver in the domain can escalate. Escalation does NOT reset
     *      existing votes but opens the decision for additional scrutiny.
     * @param _decisionId The decision to escalate
     * @param _reason Reason for escalation
     */
    function escalateDecision(
        uint256 _decisionId,
        string calldata _reason
    )
        external
        whenNotPaused
        decisionExists(_decisionId)
        notExpired(_decisionId)
        onlyActiveApprover(decisions[_decisionId].domain)
    {
        Decision storage d = decisions[_decisionId];
        require(
            d.status == DecisionStatus.PROPOSED ||
            d.status == DecisionStatus.UNDER_REVIEW,
            "Cannot escalate in current status"
        );
        require(bytes(_reason).length > 0, "Escalation reason is required");

        d.status = DecisionStatus.ESCALATED;

        // Increase quorum by 1 on escalation to require broader consensus
        d.quorumRequired++;

        EscalationRecord memory esc = EscalationRecord({
            decisionId: _decisionId,
            escalatedBy: msg.sender,
            reason: _reason,
            escalatedToDomain: d.domain,
            timestamp: block.timestamp
        });
        decisionEscalations[_decisionId].push(esc);

        emit DecisionEscalated(_decisionId, msg.sender, _reason);
    }

    /**
     * @notice Allows the original proposer to cancel their own pending decision
     * @param _decisionId The decision to cancel
     */
    function cancelDecision(uint256 _decisionId)
        external
        whenNotPaused
        decisionExists(_decisionId)
    {
        Decision storage d = decisions[_decisionId];
        require(msg.sender == d.proposer, "Only the proposer can cancel");
        require(
            d.status == DecisionStatus.PROPOSED ||
            d.status == DecisionStatus.UNDER_REVIEW ||
            d.status == DecisionStatus.ESCALATED,
            "Cannot cancel in current status"
        );

        d.status = DecisionStatus.CANCELLED;

        emit DecisionCancelled(_decisionId, msg.sender);
    }

    /**
     * @notice Marks an expired decision as expired
     * @dev Anyone can call this to garbage-collect expired decisions
     * @param _decisionId The decision to expire
     */
    function markExpired(uint256 _decisionId)
        external
        decisionExists(_decisionId)
    {
        Decision storage d = decisions[_decisionId];
        require(block.timestamp > d.expiresAt, "Decision has not expired yet");
        require(
            d.status != DecisionStatus.EXECUTED &&
            d.status != DecisionStatus.CANCELLED &&
            d.status != DecisionStatus.EXPIRED,
            "Decision is already in a terminal state"
        );

        d.status = DecisionStatus.EXPIRED;

        emit DecisionExpired(_decisionId);
    }

    // ============ Automated Action Blocking ============

    /**
     * @notice Blocks any automated or AI-initiated action in protected domains
     * @dev External contracts and AI agents MUST call this before taking action.
     *      This function ALWAYS reverts. It exists as a safety guard: any system
     *      that attempts to execute a legal, medical, or financial action directly
     *      (without routing through proposeDecision → submitHumanApproval → executeDecision)
     *      will be stopped and logged.
     * @param _domain The domain of the attempted action
     * @param _actionDescription Description of the blocked action
     */
    function blockAutomatedAction(
        DecisionDomain _domain,
        string calldata _actionDescription
    ) external {
        emit AutomatedActionBlocked(msg.sender, _domain, _actionDescription);

        revert(
            string(
                abi.encodePacked(
                    "HUMAN APPROVAL REQUIRED: All ",
                    _domainName(_domain),
                    " decisions must go through the Human Approval Gateway. "
                    "Use proposeDecision() to submit for human review."
                )
            )
        );
    }

    // ============ View Functions ============

    /**
     * @notice Returns the full details of a decision
     * @param _decisionId The decision to query
     * @return The Decision struct
     */
    function getDecision(uint256 _decisionId)
        external
        view
        decisionExists(_decisionId)
        returns (Decision memory)
    {
        return decisions[_decisionId];
    }

    /**
     * @notice Returns all approval records for a decision
     * @param _decisionId The decision to query
     * @return Array of ApprovalRecord structs
     */
    function getApprovalRecords(uint256 _decisionId)
        external
        view
        returns (ApprovalRecord[] memory)
    {
        return decisionApprovals[_decisionId];
    }

    /**
     * @notice Returns all escalation records for a decision
     * @param _decisionId The decision to query
     * @return Array of EscalationRecord structs
     */
    function getEscalationRecords(uint256 _decisionId)
        external
        view
        returns (EscalationRecord[] memory)
    {
        return decisionEscalations[_decisionId];
    }

    /**
     * @notice Returns all decision IDs for a given domain
     * @param _domain The decision domain
     * @return Array of decision IDs
     */
    function getDecisionsByDomain(DecisionDomain _domain)
        external
        view
        returns (uint256[] memory)
    {
        return domainDecisions[_domain];
    }

    /**
     * @notice Returns all decision IDs proposed by a specific address
     * @param _proposer The proposer's address
     * @return Array of decision IDs
     */
    function getDecisionsByProposer(address _proposer)
        external
        view
        returns (uint256[] memory)
    {
        return proposerDecisions[_proposer];
    }

    /**
     * @notice Returns all decision IDs an approver has reviewed
     * @param _approver The approver's address
     * @return Array of decision IDs
     */
    function getApproverHistory(address _approver)
        external
        view
        returns (uint256[] memory)
    {
        return approverDecisionHistory[_approver];
    }

    /**
     * @notice Returns the total number of decisions ever proposed
     * @return count Total decision count
     */
    function getTotalDecisions() external view returns (uint256 count) {
        return _decisionIdCounter.current();
    }

    /**
     * @notice Checks whether a decision is ready to execute
     * @param _decisionId The decision to check
     * @return ready True if quorum is met and cool-down has elapsed
     * @return reason Human-readable status explanation
     */
    function isReadyToExecute(uint256 _decisionId)
        external
        view
        decisionExists(_decisionId)
        returns (bool ready, string memory reason)
    {
        Decision storage d = decisions[_decisionId];

        if (d.status == DecisionStatus.EXECUTED) {
            return (false, "Decision has already been executed");
        }
        if (d.status == DecisionStatus.REJECTED) {
            return (false, "Decision was rejected by a human approver");
        }
        if (d.status == DecisionStatus.CANCELLED) {
            return (false, "Decision was cancelled");
        }
        if (d.status == DecisionStatus.EXPIRED || block.timestamp > d.expiresAt) {
            return (false, "Decision has expired");
        }
        if (d.approvalsReceived < d.quorumRequired) {
            return (
                false,
                string(
                    abi.encodePacked(
                        "Awaiting human approval: ",
                        _uint2str(d.approvalsReceived),
                        " of ",
                        _uint2str(d.quorumRequired),
                        " required approvals received"
                    )
                )
            );
        }
        if (d.status == DecisionStatus.APPROVED && d.approvedAt + MIN_REVIEW_PERIOD > block.timestamp) {
            return (false, "Mandatory review cool-down period has not elapsed");
        }
        if (d.status == DecisionStatus.APPROVED) {
            return (true, "Decision is approved and ready for execution");
        }

        return (false, "Decision is not in an executable state");
    }

    /**
     * @notice Returns details about a registered approver
     * @param _wallet The approver's address
     * @return The HumanApprover struct
     */
    function getApprover(address _wallet) external view returns (HumanApprover memory) {
        return approvers[_wallet];
    }

    // ============ Emergency Controls ============

    /**
     * @notice Pauses all gateway operations in case of emergency
     * @dev Only governance admin. When paused, no new decisions can be proposed,
     *      no approvals can be submitted, and no decisions can be executed.
     *      This is a safety measure — it does NOT allow bypassing human approval.
     */
    function pause() external onlyRole(GOVERNANCE_ADMIN_ROLE) {
        _pause();
    }

    /**
     * @notice Resumes gateway operations after emergency
     */
    function unpause() external onlyRole(GOVERNANCE_ADMIN_ROLE) {
        _unpause();
    }

    // ============ Internal Helpers ============

    /**
     * @dev Returns the human-readable name for a decision domain
     */
    function _domainName(DecisionDomain _domain) internal pure returns (string memory) {
        if (_domain == DecisionDomain.LEGAL) return "legal";
        if (_domain == DecisionDomain.MEDICAL) return "medical";
        if (_domain == DecisionDomain.FINANCIAL) return "financial";
        return "unknown";
    }

    /**
     * @dev Converts a uint256 to its string representation
     */
    function _uint2str(uint256 _value) internal pure returns (string memory) {
        if (_value == 0) return "0";
        uint256 temp = _value;
        uint256 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (_value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint256(_value % 10)));
            _value /= 10;
        }
        return string(buffer);
    }
}
