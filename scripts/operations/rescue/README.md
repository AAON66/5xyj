# Rescue Surface

Everything in this directory is rescue, legacy, or server-specific tooling. It is kept for investigation and emergency recovery only.

Do not treat this directory as the normal way to run or deploy the project.

## Start Here Instead

- `OPERATIONS.md` for the supported local workflow
- `DEPLOYMENT.md` for the supported Linux deployment workflow
- `OPERATIONS_RESCUE.md` for the inventory and classification of the files in this directory

## Usage Notes

- Many scripts here assume the current working directory is the repo root.
- Several scripts embed old host-specific assumptions and should be reviewed before any use.
- If a future agent is unsure whether a step is supported, follow the discuss -> plan -> execute -> verify loop from `.planning/README.md` before touching rescue tooling.
