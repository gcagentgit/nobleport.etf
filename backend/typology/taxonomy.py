"""
Taxonomy Engine — Hierarchical Classification Structures

Maintains the canonical project and permit taxonomies used for:
- PermitStream routing
- AWO classification
- Labor forecasting
- Insurance logic
- Inspection sequencing
- Dashboard analytics
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TaxonomyNode:
    id: str
    label: str
    children: tuple[TaxonomyNode, ...] = ()


PROJECT_TAXONOMY = TaxonomyNode(
    id="project",
    label="Project",
    children=(
        TaxonomyNode(
            id="residential",
            label="Residential",
            children=(
                TaxonomyNode(id="reno", label="Renovation"),
                TaxonomyNode(id="addition", label="Addition"),
                TaxonomyNode(id="new_build", label="New Construction"),
                TaxonomyNode(id="historic_reno", label="Historic Renovation"),
                TaxonomyNode(id="coastal_build", label="Coastal Build"),
            ),
        ),
        TaxonomyNode(
            id="commercial",
            label="Commercial",
            children=(
                TaxonomyNode(id="tenant_fit", label="Tenant Fit-Out"),
                TaxonomyNode(id="ground_up", label="Ground-Up"),
                TaxonomyNode(id="adaptive_reuse", label="Adaptive Reuse"),
            ),
        ),
        TaxonomyNode(
            id="municipal",
            label="Municipal",
            children=(
                TaxonomyNode(id="civic", label="Civic Buildings"),
                TaxonomyNode(id="infrastructure", label="Infrastructure"),
            ),
        ),
        TaxonomyNode(
            id="maintenance",
            label="Maintenance",
            children=(
                TaxonomyNode(id="scheduled", label="Scheduled"),
                TaxonomyNode(id="emergency", label="Emergency"),
                TaxonomyNode(id="warranty", label="Warranty"),
            ),
        ),
    ),
)

PERMIT_TAXONOMY = TaxonomyNode(
    id="permit",
    label="Permit",
    children=(
        TaxonomyNode(
            id="building",
            label="Building",
            children=(
                TaxonomyNode(id="bldg_res", label="Residential"),
                TaxonomyNode(id="bldg_com", label="Commercial"),
                TaxonomyNode(id="bldg_mixed", label="Mixed Use"),
            ),
        ),
        TaxonomyNode(
            id="trade",
            label="Trade",
            children=(
                TaxonomyNode(id="electrical", label="Electrical"),
                TaxonomyNode(id="plumbing", label="Plumbing"),
                TaxonomyNode(id="mechanical", label="Mechanical/HVAC"),
                TaxonomyNode(id="fire", label="Fire Protection"),
            ),
        ),
        TaxonomyNode(
            id="special",
            label="Special",
            children=(
                TaxonomyNode(id="demolition", label="Demolition"),
                TaxonomyNode(id="sign", label="Sign"),
                TaxonomyNode(id="occupancy", label="Certificate of Occupancy"),
                TaxonomyNode(id="wetlands", label="Wetlands/Conservation"),
                TaxonomyNode(id="historic", label="Historic Commission"),
            ),
        ),
    ),
)

CONTRACTOR_TAXONOMY = TaxonomyNode(
    id="contractor",
    label="Contractor",
    children=(
        TaxonomyNode(
            id="general",
            label="General Contractor",
            children=(
                TaxonomyNode(id="gc_res", label="Residential GC"),
                TaxonomyNode(id="gc_com", label="Commercial GC"),
            ),
        ),
        TaxonomyNode(
            id="specialty",
            label="Specialty Trade",
            children=(
                TaxonomyNode(id="elec_sub", label="Electrical"),
                TaxonomyNode(id="plumb_sub", label="Plumbing"),
                TaxonomyNode(id="hvac_sub", label="HVAC"),
                TaxonomyNode(id="frame_sub", label="Framing"),
                TaxonomyNode(id="roof_sub", label="Roofing"),
                TaxonomyNode(id="concrete_sub", label="Concrete/Foundation"),
                TaxonomyNode(id="finish_sub", label="Finish Carpentry"),
            ),
        ),
        TaxonomyNode(
            id="professional",
            label="Professional Services",
            children=(
                TaxonomyNode(id="architect", label="Architect"),
                TaxonomyNode(id="engineer", label="Engineer"),
                TaxonomyNode(id="surveyor", label="Surveyor"),
            ),
        ),
    ),
)


def flatten_taxonomy(node: TaxonomyNode, prefix: str = "") -> list[str]:
    """Flatten a taxonomy tree into a list of dot-notation paths."""
    path = f"{prefix}.{node.id}" if prefix else node.id
    paths = [path]
    for child in node.children:
        paths.extend(flatten_taxonomy(child, path))
    return paths


def get_taxonomy_depth(node: TaxonomyNode) -> int:
    if not node.children:
        return 0
    return 1 + max(get_taxonomy_depth(c) for c in node.children)


def find_node(root: TaxonomyNode, node_id: str) -> TaxonomyNode | None:
    if root.id == node_id:
        return root
    for child in root.children:
        found = find_node(child, node_id)
        if found:
            return found
    return None
