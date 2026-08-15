# Video pipeline playbook

Use this playbook for automated video or YouTube production pipelines.

The planner should split the work into small sequential stages such as input inspection, asset preparation, rendering, metadata generation, and final artifact checks. It must state expected disk usage, timeout risk, and the output path. Heavy tools should run on Ubuntu, not on the Redmi 10a. Any upload, credential use, or external publication must be a separate review-sensitive step and must not happen from an unapproved direct command.

The verifier should confirm that the expected artifact exists, has a non-zero size, and can be inspected with a read-only command. The final report must include the artifact path, test or inspection evidence, and any unfinished publication step.
