"""Names of workflow input files and export stages."""

FILES = {'school':'saved_admission_school', 'dump':'saved_admission_dump', 'email_dump':'saved_email_dump'}


STAGES = {'admission':'admission_exports', 'email':'email_exports', 'full_name_class':'full_name_class_exports'}


# Purpose: Defines the canonical state keys for workflow input files and result stages.
# FILES maps public file kinds to their corresponding saved-state fields.
# STAGES maps public mapping-stage names to their stored export dictionaries.
# Central definitions prevent routes and response builders from repeating key strings.
# These mappings also constrain which file kinds and stages APIs may resolve.
# Used by: snapshot helpers validate inputs and response summaries enumerate files/exports.
# File input, preview, result-preview, and download routes resolve requested resources.
# Session storage uses matching key collections when persisting binary snapshots.
