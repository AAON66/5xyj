"""Initial schema for social security aggregation tool."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260320_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


batch_status = sa.Enum(
    "uploaded",
    "parsing",
    "normalized",
    "validated",
    "matched",
    "export_ready",
    "exported",
    "failed",
    "blocked",
    name="batchstatus",
    native_enum=False,
)
mapping_source = sa.Enum("rule", "llm", "manual", name="mappingsource", native_enum=False)
match_status = sa.Enum(
    "matched",
    "unmatched",
    "duplicate",
    "low_confidence",
    "manual",
    name="matchstatus",
    native_enum=False,
)
template_type = sa.Enum("salary", "final_tool", name="templatetype", native_enum=False)


UUID_TYPE = sa.Uuid(as_uuid=False)
AMOUNT_TYPE = sa.Numeric(12, 2)


def upgrade() -> None:
    op.create_table(
        "import_batches",
        sa.Column("batch_name", sa.String(length=255), nullable=False),
        sa.Column("status", batch_status, nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_import_batches")),
    )
    op.create_index(op.f("ix_import_batches_batch_name"), "import_batches", ["batch_name"], unique=False)
    op.create_index(op.f("ix_import_batches_status"), "import_batches", ["status"], unique=False)

    op.create_table(
        "employee_master",
        sa.Column("employee_id", sa.String(length=100), nullable=False),
        sa.Column("person_name", sa.String(length=255), nullable=False),
        sa.Column("id_number", sa.String(length=100), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("department", sa.String(length=255), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_employee_master")),
        sa.UniqueConstraint("employee_id", name=op.f("uq_employee_master_employee_id")),
    )
    op.create_index(op.f("ix_employee_master_active"), "employee_master", ["active"], unique=False)
    op.create_index(op.f("ix_employee_master_company_name"), "employee_master", ["company_name"], unique=False)
    op.create_index(op.f("ix_employee_master_employee_id"), "employee_master", ["employee_id"], unique=True)
    op.create_index(op.f("ix_employee_master_id_number"), "employee_master", ["id_number"], unique=False)
    op.create_index(op.f("ix_employee_master_person_name"), "employee_master", ["person_name"], unique=False)

    op.create_table(
        "source_files",
        sa.Column("batch_id", UUID_TYPE, nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("raw_sheet_name", sa.String(length=255), nullable=True),
        sa.Column("file_hash", sa.String(length=128), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"], name=op.f("fk_source_files_batch_id_import_batches"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_source_files")),
    )
    op.create_index(op.f("ix_source_files_batch_id"), "source_files", ["batch_id"], unique=False)
    op.create_index(op.f("ix_source_files_company_name"), "source_files", ["company_name"], unique=False)
    op.create_index(op.f("ix_source_files_file_hash"), "source_files", ["file_hash"], unique=False)
    op.create_index(op.f("ix_source_files_file_name"), "source_files", ["file_name"], unique=False)

    op.create_table(
        "export_jobs",
        sa.Column("batch_id", UUID_TYPE, nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"], name=op.f("fk_export_jobs_batch_id_import_batches"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_export_jobs")),
    )
    op.create_index(op.f("ix_export_jobs_batch_id"), "export_jobs", ["batch_id"], unique=False)
    op.create_index(op.f("ix_export_jobs_status"), "export_jobs", ["status"], unique=False)

    op.create_table(
        "header_mappings",
        sa.Column("source_file_id", UUID_TYPE, nullable=False),
        sa.Column("raw_header", sa.String(length=500), nullable=False),
        sa.Column("raw_header_signature", sa.String(length=500), nullable=False),
        sa.Column("canonical_field", sa.String(length=100), nullable=True),
        sa.Column("mapping_source", mapping_source, nullable=False),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("manually_overridden", sa.Boolean(), nullable=False),
        sa.Column("candidate_fields", sa.JSON(), nullable=True),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["source_file_id"], ["source_files.id"], name=op.f("fk_header_mappings_source_file_id_source_files"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_header_mappings")),
    )
    op.create_index(op.f("ix_header_mappings_canonical_field"), "header_mappings", ["canonical_field"], unique=False)
    op.create_index(op.f("ix_header_mappings_mapping_source"), "header_mappings", ["mapping_source"], unique=False)
    op.create_index(op.f("ix_header_mappings_raw_header_signature"), "header_mappings", ["raw_header_signature"], unique=False)
    op.create_index(op.f("ix_header_mappings_source_file_id"), "header_mappings", ["source_file_id"], unique=False)

    op.create_table(
        "normalized_records",
        sa.Column("batch_id", UUID_TYPE, nullable=False),
        sa.Column("source_file_id", UUID_TYPE, nullable=False),
        sa.Column("source_row_number", sa.Integer(), nullable=False),
        sa.Column("person_name", sa.String(length=255), nullable=True),
        sa.Column("id_type", sa.String(length=100), nullable=True),
        sa.Column("id_number", sa.String(length=100), nullable=True),
        sa.Column("employee_id", sa.String(length=100), nullable=True),
        sa.Column("social_security_number", sa.String(length=100), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("billing_period", sa.String(length=100), nullable=True),
        sa.Column("period_start", sa.String(length=100), nullable=True),
        sa.Column("period_end", sa.String(length=100), nullable=True),
        sa.Column("payment_base", AMOUNT_TYPE, nullable=True),
        sa.Column("payment_salary", AMOUNT_TYPE, nullable=True),
        sa.Column("total_amount", AMOUNT_TYPE, nullable=True),
        sa.Column("company_total_amount", AMOUNT_TYPE, nullable=True),
        sa.Column("personal_total_amount", AMOUNT_TYPE, nullable=True),
        sa.Column("pension_company", AMOUNT_TYPE, nullable=True),
        sa.Column("pension_personal", AMOUNT_TYPE, nullable=True),
        sa.Column("medical_company", AMOUNT_TYPE, nullable=True),
        sa.Column("medical_personal", AMOUNT_TYPE, nullable=True),
        sa.Column("medical_maternity_company", AMOUNT_TYPE, nullable=True),
        sa.Column("maternity_amount", AMOUNT_TYPE, nullable=True),
        sa.Column("unemployment_company", AMOUNT_TYPE, nullable=True),
        sa.Column("unemployment_personal", AMOUNT_TYPE, nullable=True),
        sa.Column("injury_company", AMOUNT_TYPE, nullable=True),
        sa.Column("supplementary_medical_company", AMOUNT_TYPE, nullable=True),
        sa.Column("supplementary_pension_company", AMOUNT_TYPE, nullable=True),
        sa.Column("large_medical_personal", AMOUNT_TYPE, nullable=True),
        sa.Column("late_fee", AMOUNT_TYPE, nullable=True),
        sa.Column("interest", AMOUNT_TYPE, nullable=True),
        sa.Column("raw_sheet_name", sa.String(length=255), nullable=True),
        sa.Column("raw_header_signature", sa.String(length=500), nullable=True),
        sa.Column("source_file_name", sa.String(length=255), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"], name=op.f("fk_normalized_records_batch_id_import_batches"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_file_id"], ["source_files.id"], name=op.f("fk_normalized_records_source_file_id_source_files"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_normalized_records")),
    )
    op.create_index(op.f("ix_normalized_records_batch_id"), "normalized_records", ["batch_id"], unique=False)
    op.create_index(op.f("ix_normalized_records_billing_period"), "normalized_records", ["billing_period"], unique=False)
    op.create_index(op.f("ix_normalized_records_company_name"), "normalized_records", ["company_name"], unique=False)
    op.create_index(op.f("ix_normalized_records_employee_id"), "normalized_records", ["employee_id"], unique=False)
    op.create_index(op.f("ix_normalized_records_id_number"), "normalized_records", ["id_number"], unique=False)
    op.create_index(op.f("ix_normalized_records_person_name"), "normalized_records", ["person_name"], unique=False)
    op.create_index(op.f("ix_normalized_records_region"), "normalized_records", ["region"], unique=False)
    op.create_index(op.f("ix_normalized_records_social_security_number"), "normalized_records", ["social_security_number"], unique=False)
    op.create_index(op.f("ix_normalized_records_source_file_id"), "normalized_records", ["source_file_id"], unique=False)

    op.create_table(
        "validation_issues",
        sa.Column("batch_id", UUID_TYPE, nullable=False),
        sa.Column("normalized_record_id", UUID_TYPE, nullable=True),
        sa.Column("issue_type", sa.String(length=100), nullable=False),
        sa.Column("severity", sa.String(length=50), nullable=False),
        sa.Column("field_name", sa.String(length=100), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("resolved", sa.Boolean(), nullable=False),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"], name=op.f("fk_validation_issues_batch_id_import_batches"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["normalized_record_id"], ["normalized_records.id"], name=op.f("fk_validation_issues_normalized_record_id_normalized_records"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_validation_issues")),
    )
    op.create_index(op.f("ix_validation_issues_batch_id"), "validation_issues", ["batch_id"], unique=False)
    op.create_index(op.f("ix_validation_issues_field_name"), "validation_issues", ["field_name"], unique=False)
    op.create_index(op.f("ix_validation_issues_issue_type"), "validation_issues", ["issue_type"], unique=False)
    op.create_index(op.f("ix_validation_issues_normalized_record_id"), "validation_issues", ["normalized_record_id"], unique=False)
    op.create_index(op.f("ix_validation_issues_resolved"), "validation_issues", ["resolved"], unique=False)
    op.create_index(op.f("ix_validation_issues_severity"), "validation_issues", ["severity"], unique=False)

    op.create_table(
        "match_results",
        sa.Column("batch_id", UUID_TYPE, nullable=False),
        sa.Column("normalized_record_id", UUID_TYPE, nullable=False),
        sa.Column("employee_master_id", UUID_TYPE, nullable=True),
        sa.Column("match_status", match_status, nullable=False),
        sa.Column("match_basis", sa.String(length=255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["import_batches.id"], name=op.f("fk_match_results_batch_id_import_batches"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["employee_master_id"], ["employee_master.id"], name=op.f("fk_match_results_employee_master_id_employee_master"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["normalized_record_id"], ["normalized_records.id"], name=op.f("fk_match_results_normalized_record_id_normalized_records"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_match_results")),
        sa.UniqueConstraint("normalized_record_id", name="uq_match_results_normalized_record_id"),
    )
    op.create_index(op.f("ix_match_results_batch_id"), "match_results", ["batch_id"], unique=False)
    op.create_index(op.f("ix_match_results_employee_master_id"), "match_results", ["employee_master_id"], unique=False)
    op.create_index(op.f("ix_match_results_match_status"), "match_results", ["match_status"], unique=False)
    op.create_index(op.f("ix_match_results_normalized_record_id"), "match_results", ["normalized_record_id"], unique=False)

    op.create_table(
        "export_artifacts",
        sa.Column("export_job_id", UUID_TYPE, nullable=False),
        sa.Column("template_type", template_type, nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", UUID_TYPE, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["export_job_id"], ["export_jobs.id"], name=op.f("fk_export_artifacts_export_job_id_export_jobs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_export_artifacts")),
        sa.UniqueConstraint("export_job_id", "template_type", name="uq_export_artifacts_job_template"),
    )
    op.create_index(op.f("ix_export_artifacts_export_job_id"), "export_artifacts", ["export_job_id"], unique=False)
    op.create_index(op.f("ix_export_artifacts_status"), "export_artifacts", ["status"], unique=False)
    op.create_index(op.f("ix_export_artifacts_template_type"), "export_artifacts", ["template_type"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_export_artifacts_template_type"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_status"), table_name="export_artifacts")
    op.drop_index(op.f("ix_export_artifacts_export_job_id"), table_name="export_artifacts")
    op.drop_table("export_artifacts")

    op.drop_index(op.f("ix_match_results_normalized_record_id"), table_name="match_results")
    op.drop_index(op.f("ix_match_results_match_status"), table_name="match_results")
    op.drop_index(op.f("ix_match_results_employee_master_id"), table_name="match_results")
    op.drop_index(op.f("ix_match_results_batch_id"), table_name="match_results")
    op.drop_table("match_results")

    op.drop_index(op.f("ix_validation_issues_severity"), table_name="validation_issues")
    op.drop_index(op.f("ix_validation_issues_resolved"), table_name="validation_issues")
    op.drop_index(op.f("ix_validation_issues_normalized_record_id"), table_name="validation_issues")
    op.drop_index(op.f("ix_validation_issues_issue_type"), table_name="validation_issues")
    op.drop_index(op.f("ix_validation_issues_field_name"), table_name="validation_issues")
    op.drop_index(op.f("ix_validation_issues_batch_id"), table_name="validation_issues")
    op.drop_table("validation_issues")

    op.drop_index(op.f("ix_normalized_records_source_file_id"), table_name="normalized_records")
    op.drop_index(op.f("ix_normalized_records_social_security_number"), table_name="normalized_records")
    op.drop_index(op.f("ix_normalized_records_region"), table_name="normalized_records")
    op.drop_index(op.f("ix_normalized_records_person_name"), table_name="normalized_records")
    op.drop_index(op.f("ix_normalized_records_id_number"), table_name="normalized_records")
    op.drop_index(op.f("ix_normalized_records_employee_id"), table_name="normalized_records")
    op.drop_index(op.f("ix_normalized_records_company_name"), table_name="normalized_records")
    op.drop_index(op.f("ix_normalized_records_billing_period"), table_name="normalized_records")
    op.drop_index(op.f("ix_normalized_records_batch_id"), table_name="normalized_records")
    op.drop_table("normalized_records")

    op.drop_index(op.f("ix_header_mappings_source_file_id"), table_name="header_mappings")
    op.drop_index(op.f("ix_header_mappings_raw_header_signature"), table_name="header_mappings")
    op.drop_index(op.f("ix_header_mappings_mapping_source"), table_name="header_mappings")
    op.drop_index(op.f("ix_header_mappings_canonical_field"), table_name="header_mappings")
    op.drop_table("header_mappings")

    op.drop_index(op.f("ix_export_jobs_status"), table_name="export_jobs")
    op.drop_index(op.f("ix_export_jobs_batch_id"), table_name="export_jobs")
    op.drop_table("export_jobs")

    op.drop_index(op.f("ix_source_files_file_name"), table_name="source_files")
    op.drop_index(op.f("ix_source_files_file_hash"), table_name="source_files")
    op.drop_index(op.f("ix_source_files_company_name"), table_name="source_files")
    op.drop_index(op.f("ix_source_files_batch_id"), table_name="source_files")
    op.drop_table("source_files")

    op.drop_index(op.f("ix_employee_master_person_name"), table_name="employee_master")
    op.drop_index(op.f("ix_employee_master_id_number"), table_name="employee_master")
    op.drop_index(op.f("ix_employee_master_employee_id"), table_name="employee_master")
    op.drop_index(op.f("ix_employee_master_company_name"), table_name="employee_master")
    op.drop_index(op.f("ix_employee_master_active"), table_name="employee_master")
    op.drop_table("employee_master")

    op.drop_index(op.f("ix_import_batches_status"), table_name="import_batches")
    op.drop_index(op.f("ix_import_batches_batch_name"), table_name="import_batches")
    op.drop_table("import_batches")